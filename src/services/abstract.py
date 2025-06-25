from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx
import hashlib
import json

from src.models import Result, Address, Coordinates
from src.models.failure import Failure
from src.models.success import Success
from src.services.cache import CacheManager


class ServiceCommandBase(ABC):
    """Abstract base class for service commands."""

    name: str
    url: str
    cache: CacheManager

    @abstractmethod
    def execute(self) -> None:
        """Executes the command. Must be implemented by subclasses."""

    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generates a consistent cache key for a request."""
        # Use a hash of the sorted parameters to ensure consistency
        param_string = json.dumps(params, sort_keys=True)
        hash_object = hashlib.sha256(param_string.encode())
        return f"raw:{self.name}:{hash_object.hexdigest()}"

    async def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        timeout: int = 30,
        /,
        user_agent: Optional[str] = None,
    ) -> Result[Dict[str, Any], str]:
        """Make HTTP request to an URL with error handling and caching."""
        cache_key = self._generate_cache_key(params)
        
        # 1. Check cache first
        cached_response = await self.cache.get_raw(cache_key)
        if cached_response:
            return Success(cached_response)

        # 2. If not in cache, make the actual request
        try:
            headers = None
            if user_agent:
                headers = {"User-Agent": user_agent}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, timeout=timeout, headers=headers
                )
                response.raise_for_status()
                response_data = response.json()

                # 3. Store the successful response in cache
                await self.cache.set_raw(cache_key, response_data)
                
                return Success(response_data)
        except httpx.TimeoutException:
            return Failure("Request timeout.")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return Failure("API rate limit exceeded.")
            return Failure(f"HTTP error: {e.response.text}")
        except httpx.RequestError as e:
            return Failure(f"Request failed: {e}")        
        return Failure("An unexpected error occurred while making the request.")

    def __str__(self) -> str:
        """Returns a string representation of the service command."""
        return f"ServiceCommandBase(name={self.name})"

    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"<ServiceCommandBase name='{self.name}'>"

    def __eq__(self, other) -> bool:
        """Checks equality between two ServiceCommandBase objects."""
        if not isinstance(other, ServiceCommandBase):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Generates a hash based on the service name."""
        return hash(self.name)


class GeocoderBase(ServiceCommandBase):
    """Abstract base class for geocoding commands.

    Attributes:
        name (str): Name of the service command.
    """

    def execute(self):
        pass

    @abstractmethod
    async def get_coordinates(self, address: str) -> Result[Coordinates, str]:
        """Gets geographic coordinates for a given address asynchronously.

        Args:
            address (str): The address to geocode.

        Returns:
            result (Result[Coordinates, str]):
                A `Result` containing either the coordinates
                (on success) or an error message (on failure).
        """


class ReverseGeocoderBase(ServiceCommandBase):
    """Abstract base class for reverse geocoding commands.

    Attributes:
        name (str): Name of the service command.
    """

    @abstractmethod
    async def get_addresses(
        self, coordinates: Coordinates
    ) -> Result[list[Address], str]:
        """Gets addresses for given geographic coordinates asynchronously.

        Args:
            coordinates (Coordinates): The geographic coordinates.

        Returns:
            result (Result[list[Address], str]):
                A `Result` containing either a list of addresses
                (on success) or an error message (on failure).
        """
