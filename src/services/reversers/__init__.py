import os
import hashlib
from typing import Optional
from src.models import Coordinates
from src.responses import ReverseGeocodeResponse
from src.services.abstract import ReverseGeocoderBase
from src.services.cache import CacheManager
from src.services.reversers.geoapify import GeoapifyReverseGeocoder
from src.services.reversers.here import HereReverseGeocoder
from src.services.reversers.nominatim import NominatimReverseGeocoder


class GeocoderReverser:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self, cache: CacheManager):
        """Initializes a dictionary of geocoders based on environment variables."""
        self.cache = cache
        self.geocoders: dict[str, ReverseGeocoderBase] = {
            "GEOAPIFY": GeoapifyReverseGeocoder(
                self.cache, api_key=os.getenv("GEOAPIFY_API_KEY")
            ),
            "HERE": HereReverseGeocoder(self.cache, api_key=os.getenv("HERE_API_KEY")),
            "NOMINATIM": NominatimReverseGeocoder(
                cache=self.cache,
                user_agent=os.getenv("NOMINATIM_USER_AGENT"),
            ),
            "NOMINATIM_REPLICA_1": NominatimReverseGeocoder(
                cache=self.cache,
                url=os.getenv("NOMINATIM_REVERSER_REPLICA_URL_1"),
                user_agent=os.getenv("NOMINATIM_USER_AGENT"),
            ),
        }

        # Remove entries that are not correctly configured
        self.geocoders = {
            name: geocoder
            for name, geocoder in self.geocoders.items()
            if geocoder is not None
        }

    def _generate_cache_key(
        self, coordinates: Coordinates, platform: Optional[str]
    ) -> str:
        """Generates a consistent cache key for a final response."""
        # Use a hash of the coordinates and platform to create a unique key
        coords_str = f"{coordinates.latitude:.6f}:{coordinates.longitude:.6f}"
        platform_norm = platform.lower().strip() if platform else "any"
        hash_object = hashlib.sha256(f"{coords_str}:{platform_norm}".encode())
        return f"final:revgeo:{hash_object.hexdigest()}"

    async def search(
        self, coordinates: Coordinates, platform: Optional[str] = None
    ) -> ReverseGeocodeResponse:
        """
        Performs reverse geocoding with final response caching.
        """
        cache_key = self._generate_cache_key(coordinates, platform)

        # 1. Check final response cache
        cached_data = await self.cache.get_final(cache_key)
        if cached_data is not None:
            return ReverseGeocodeResponse(success=True, data=cached_data)

        # 2. If not cached, proceed with reverse geocoding logic
        if platform:
            geocoder = self.geocoders.get(platform.upper())
            if not geocoder:
                return ReverseGeocodeResponse(
                    success=False, error="Invalid platform specified."
                )

            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                response = ReverseGeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data)
                return response
            return ReverseGeocodeResponse(success=False, error=result.unwrap_err())

        # Failover logic
        if not self.geocoders:
            return ReverseGeocodeResponse(
                success=False, error="No geocoders are configured."
            )

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                response = ReverseGeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data)
                return response

        return ReverseGeocodeResponse(
            success=False, error="All geocoding services failed."
        )
