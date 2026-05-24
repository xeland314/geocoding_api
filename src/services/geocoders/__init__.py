import hashlib
from typing import Optional
from src.responses import GeocodeResponse
from src.services.abstract import GeocoderBase
from src.services.cache import CacheManager
from src.services.config import config
from src.services.geocoders.nominatim import NominatimGeocoder


class Geocoder:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self, cache: CacheManager):
        """Initializes a dictionary of geocoders based on config.json."""
        self.cache = cache
        self.geocoders: dict[str, GeocoderBase] = {}
        
        geocoders_config = config.get("geocoders", {})
        
        # Mapping of config keys to Geocoder classes
        # This could be more dynamic, but for now we map them explicitly
        class_map = {
            "NOMINATIM": NominatimGeocoder,
            "NOMINATIM_REPLICA_1": NominatimGeocoder,
        }

        for name, settings in geocoders_config.items():
            if not settings.get("enabled", False):
                continue
            
            geocoder_class = class_map.get(name)
            if not geocoder_class:
                print(f"[Geocoder] Unknown geocoder type: {name}")
                continue
                
            # Initialize with settings from config
            # We pass only relevant keys to the constructor
            init_params = {
                "cache": self.cache,
            }
            if "url" in settings and settings["url"]:
                init_params["url"] = settings["url"]
            if "user_agent" in settings and settings["user_agent"]:
                init_params["user_agent"] = settings["user_agent"]
                
            self.geocoders[name] = geocoder_class(**init_params)

        print(f"[Geocoder] Active geocoders: {list(self.geocoders.keys())}")

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
                    success=False, error="Invalid platform specified or platform disabled."
                )

            result = await geocoder.get_coordinates(address)
            if result.is_success():
                data = result.unwrap()
                response = GeocodeResponse(success=True, data=data)
                await self.cache.set_final(cache_key, data)
                return response
            return GeocodeResponse(success=False, error=result.unwrap_err())

        # Failover logic
        if not self.geocoders:
            return GeocodeResponse(success=False, error="No geocoders are configured or enabled.")

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_coordinates(address)
            if result.is_success():
                data = result.unwrap()
                response = GeocodeResponse(success=True, data=data)
                await self.cache.set_final(cache_key, data)
                return response

        return GeocodeResponse(success=False, error="All geocoding services failed.")
