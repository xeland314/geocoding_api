import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite
import redis.asyncio as redis

# Constants
REDIS_TTL_SECONDS = 3600 * 24  # 24 hours


class CacheManager:
    """Manages a two-level cache (Redis L1, SQLite L2) for API responses."""

    def __init__(self):
        """Initializes the clients for Redis and SQLite from environment variables."""
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.sqlite_path = os.getenv("SQLITE_DB_PATH", "geocoding_cache.db")
        self.redis_client: Optional[redis.Redis] = None
        self.db_conn: Optional[aiosqlite.Connection] = None

    @asynccontextmanager
    async def lifespan(self, app):
        """Manages the startup and shutdown of cache connections."""
        print("[Cache] Initializing cache connections...")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
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

    async def _get(self, key: str, table_name: str) -> Optional[str]:
        """Private helper to get a value from the cache (L1 -> L2)."""
        # L1 Cache (Redis)
        try:
            cached_value = await self.redis_client.get(key)
            if cached_value:
                return cached_value
        except Exception as e:
            print(f"[Cache] Redis GET error: {e}")

        # L2 Cache (SQLite)
        try:
            async with self.db_conn.execute(
                f"SELECT value FROM {table_name} WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    value_str = row[0]
                    # Promote from L2 to L1
                    try:
                        await self.redis_client.set(
                            key, value_str, ex=REDIS_TTL_SECONDS
                        )
                    except Exception as e:
                        print(f"[Cache] Redis SET error during L2->L1 promotion: {e}")
                    return value_str
        except Exception as e:
            print(f"[Cache] SQLite GET error: {e}")

        return None

    async def _set(self, key: str, value_str: str, table_name: str):
        """Private helper to set a value in the cache (L1 & L2)."""
        now = datetime.utcnow()
        # Set in L1 (Redis)
        try:
            await self.redis_client.set(key, value_str, ex=REDIS_TTL_SECONDS)
        except Exception as e:
            print(f"[Cache] Redis SET error: {e}")

        # Set in L2 (SQLite)
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
