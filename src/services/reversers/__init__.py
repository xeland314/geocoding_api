import hashlib
from typing import Optional
from src.models import Coordinates
from src.responses import ReverseGeocodeResponse
from src.services.abstract import ReverseGeocoderBase
from src.services.cache import CacheManager
from src.services.config import config
from src.services.reversers.geoapify import GeoapifyReverseGeocoder
from src.services.reversers.here import HereReverseGeocoder
from src.services.reversers.nominatim import NominatimReverseGeocoder


class GeocoderReverser:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self, cache: CacheManager):
        """Initializes a dictionary of geocoders based on config.json."""
        self.cache = cache
        self.geocoders: dict[str, ReverseGeocoderBase] = {}
        
        reversers_config = config.get("reversers", {})
        
        # Mapping of config keys to Reverser classes
        class_map = {
            "GEOAPIFY": GeoapifyReverseGeocoder,
            "HERE": HereReverseGeocoder,
            "NOMINATIM": NominatimReverseGeocoder,
            "NOMINATIM_REPLICA_1": NominatimReverseGeocoder,
        }

        for name, settings in reversers_config.items():
            if not settings.get("enabled", False):
                continue
            
            reverser_class = class_map.get(name)
            if not reverser_class:
                print(f"[GeocoderReverser] Unknown reverser type: {name}")
                continue
                
            # Initialize with settings from config
            init_params = {
                "cache": self.cache,
            }
            
            # Add optional parameters based on class requirements
            if "api_key" in settings and settings["api_key"]:
                init_params["api_key"] = settings["api_key"]
            if "url" in settings and settings["url"]:
                init_params["url"] = settings["url"]
            if "user_agent" in settings and settings["user_agent"]:
                init_params["user_agent"] = settings["user_agent"]
                
            try:
                self.geocoders[name] = reverser_class(**init_params)
            except TypeError as e:
                print(f"[GeocoderReverser] Error initializing {name}: {e}")

        print(f"[GeocoderReverser] Active reversers: {list(self.geocoders.keys())}")

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
                    success=False, error="Invalid platform specified or platform disabled."
                )

            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                response = ReverseGeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data or [])
                return response
            return ReverseGeocodeResponse(success=False, error=result.unwrap_err())

        # Failover logic
        if not self.geocoders:
            return ReverseGeocodeResponse(
                success=False, error="No reversers are configured or enabled."
            )

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                response = ReverseGeocodeResponse(success=True, data=result.unwrap())
                await self.cache.set_final(cache_key, response.data or [])
                return response

        return ReverseGeocodeResponse(
            success=False, error="All geocoding services failed."
        )
