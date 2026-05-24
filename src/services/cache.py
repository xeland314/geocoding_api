import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiosqlite
import redis.asyncio as redis
from src.services.config import config

# Constants
REDIS_TTL_SECONDS = 3600 * 24  # 24 hours


class CacheManager:
    """Manages a two-level cache (Redis/Dict L1, SQLite L2) for API responses."""

    def __init__(self):
        """Initializes the cache settings from config."""
        cache_config = config.get("cache", {})
        self.use_redis = cache_config.get("use_redis", False)
        self.redis_url = cache_config.get("redis_url", "redis://localhost:6379")
        self.sqlite_path = cache_config.get("sqlite_db_path", "geocoding_cache.db")
        
        self.redis_client: Optional[redis.Redis] = None
        self.db_conn: Optional[aiosqlite.Connection] = None
        
        # In-memory L1 fallback
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    @asynccontextmanager
    async def lifespan(self, app):
        """Manages the startup and shutdown of cache connections."""
        print("[Cache] Initializing cache connections...")
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
                print("[Cache] Redis connected.")
            except Exception as e:
                print(f"[Cache] Redis connection failed, falling back to in-memory: {e}")
                self.use_redis = False
                self.redis_client = None

        await self.setup()
        yield
        print("[Cache] Closing cache connections...")
        await self.close()

    async def setup(self):
        """Establishes connections and creates database tables if they don't exist."""
        self.db_conn = await aiosqlite.connect(self.sqlite_path)
        await self.db_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_responses (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
            """
        )
        await self.db_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS final_responses (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
            """
        )
        await self.db_conn.commit()

    async def close(self):
        """Closes the database and Redis connections gracefully."""
        if self.db_conn:
            await self.db_conn.close()
        if self.redis_client:
            await self.redis_client.close()

    async def _get_l1(self, key: str) -> Optional[str]:
        """Gets a value from L1 cache (Redis or Dict)."""
        if self.use_redis and self.redis_client:
            try:
                return await self.redis_client.get(key)
            except Exception as e:
                print(f"[Cache] Redis GET error: {e}")
        
        # Fallback to memory cache
        entry = self.memory_cache.get(key)
        if entry:
            if datetime.utcnow() < entry["expires"]:
                return entry["value"]
            else:
                del self.memory_cache[key]
        return None

    async def _set_l1(self, key: str, value_str: str):
        """Sets a value in L1 cache (Redis or Dict)."""
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.set(key, value_str, ex=REDIS_TTL_SECONDS)
                return
            except Exception as e:
                print(f"[Cache] Redis SET error: {e}")

        # Fallback to memory cache
        self.memory_cache[key] = {
            "value": value_str,
            "expires": datetime.utcnow() + timedelta(seconds=REDIS_TTL_SECONDS)
        }

    async def _get(self, key: str, table_name: str) -> Optional[str]:
        """Private helper to get a value from the cache (L1 -> L2)."""
        # L1 Cache
        cached_value = await self._get_l1(key)
        if cached_value:
            return cached_value

        # L2 Cache (SQLite)
        if not self.db_conn:
            # Ensure DB connection is available (lazy initialize if not set up)
            await self.setup()
            if not self.db_conn:
                return None

        try:
            async with self.db_conn.execute(
                f"SELECT value FROM {table_name} WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    value_str = row[0]
                    # Promote from L2 to L1
                    await self._set_l1(key, value_str)
                    return value_str
        except Exception as e:
            print(f"[Cache] SQLite GET error: {e}")

        return None

    async def _set(self, key: str, value_str: str, table_name: str):
        """Private helper to set a value in the cache (L1 & L2)."""
        now = datetime.utcnow()
        # Set in L1
        await self._set_l1(key, value_str)

        # Set in L2 (SQLite)
        if not self.db_conn:
            # Ensure DB connection is available (lazy initialize if not set up)
            await self.setup()
            if not self.db_conn:
                # If still not available, skip L2 persistence
                return

        try:
            await self.db_conn.execute(
                f"INSERT OR REPLACE INTO {table_name} (key, value, timestamp) VALUES (?, ?, ?)",
                (key, value_str, now),
            )
            await self.db_conn.commit()
        except Exception as e:
            print(f"[Cache] SQLite SET error: {e}")

    async def get_raw(self, key: str) -> Optional[Dict[str, Any]]:
        """Gets a raw response from the cache."""
        value_str = await self._get(key, "raw_responses")
        return json.loads(value_str) if value_str else None

    async def set_raw(self, key: str, value: Dict[str, Any]):
        """Sets a raw response in the cache."""
        await self._set(key, json.dumps(value), "raw_responses")

    async def get_final(self, key: str) -> Optional[List[Any]]:
        """Gets a final response from the cache."""
        value_str = await self._get(key, "final_responses")
        return json.loads(value_str) if value_str else None

    async def set_final(self, key: str, value: List[Any]):
        """Sets a final response in the cache, handling Pydantic models."""
        # Convert Pydantic models to dicts for JSON serialization
        if value and hasattr(value[0], 'model_dump'):
            value_to_serialize = [item.model_dump() for item in value]
        else:
            value_to_serialize = value
        
        await self._set(key, json.dumps(value_to_serialize), "final_responses")
