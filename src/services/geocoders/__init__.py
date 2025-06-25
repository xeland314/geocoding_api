import os
import hashlib
from typing import Optional
from src.models import Coordinates
from src.responses import GeocodeResponse
from src.services.abstract import GeocoderBase
from src.services.cache import CacheManager
from src.services.geocoders.nominatim import NominatimGeocoder


class Geocoder:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self, cache: CacheManager):
        """Initializes a dictionary of geocoders based on environment variables."""
        self.cache = cache
        self.geocoders: dict[str, GeocoderBase] = {
            "NOMINATIM": NominatimGeocoder(
                cache=self.cache, user_agent=os.getenv("NOMINATIM_USER_AGENT")
            ),
            "NOMINATIM_REPLICA_1": NominatimGeocoder(
                cache=self.cache,
                url=os.getenv("NOMINATIM_GEOCODER_REPLICA_URL_1"),
                user_agent=os.getenv("NOMINATIM_USER_AGENT"),
            ),
        }

        # Remove entries that are not correctly configured
        self.geocoders = {
            name: geocoder
            for name, geocoder in self.geocoders.items()
            if geocoder is not None
        }

    def _generate_cache_key(self, address: str, platform: Optional[str]) -> str:
        """Generates a consistent cache key for a final response."""
        # Normalize the address and include the platform to create a unique key
        address_norm = address.lower().strip()
        platform_norm = platform.lower().strip() if platform else "any"
        hash_object = hashlib.sha256(f"{address_norm}:{platform_norm}".encode())
        return f"final:geocode:{hash_object.hexdigest()}"

    async def search(
        self, address: str, platform: Optional[str] = None
    ) -> GeocodeResponse:
        """
        Performs geocoding using a specified geocoder or tries all
        available geocoders until one succeeds, with final response caching.
        """
        cache_key = self._generate_cache_key(address, platform)

        # 1. Check final response cache
        cached_data = await self.cache.get_final(cache_key)
        if cached_data is not None:
            return GeocodeResponse(success=True, data=cached_data)

        # 2. If not cached, proceed with geocoding logic
        if platform:
            geocoder = self.geocoders.get(platform.upper())
            if not geocoder:
                return GeocodeResponse(
                    success=False, error="Invalid platform specified."
                )

            result = await geocoder.get_coordinates(address)
            if result.is_success():
                response = GeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data)
                return response
            return GeocodeResponse(success=False, error=result.unwrap_err())

        # Failover logic
        if not self.geocoders:
            return GeocodeResponse(success=False, error="No geocoders are configured.")

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_coordinates(address)
            if result.is_success():
                response = GeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data)
                return response

        return GeocodeResponse(success=False, error="All geocoding services failed.")
