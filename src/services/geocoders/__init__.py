import os
from typing import Optional
from src.models import Coordinates
from src.responses import GeocodeResponse
from src.services.abstract import GeocoderBase
from src.services.geocoders.nominatim import NominatimGeocoder


class Geocoder:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self):
        """Initializes a dictionary of geocoders based on environment variables."""
        self.geocoders: dict[str, GeocoderBase] = {
            "NOMINATIM": NominatimGeocoder(
                user_agent=os.getenv("NOMINATIM_USER_AGENT")
            ),
            "NOMINATIM_REPLICA_1": NominatimGeocoder(
                os.getenv("NOMINATIM_GEOCODER_REPLICA_URL_1"),
                user_agent=os.getenv("NOMINATIM_USER_AGENT"),
            ),
        }

        # Remove entries that are not correctly configured
        self.geocoders = {
            name: geocoder
            for name, geocoder in self.geocoders.items()
            if geocoder is not None
        }

    async def search(
        self, address: str, platform: Optional[str] = None
    ) -> GeocodeResponse:
        """
        Performs geocoding using a specified geocoder or tries all
        available geocoders until one succeeds.
        """
        if platform:
            geocoder = self.geocoders.get(platform.upper())
            if not geocoder:
                return GeocodeResponse(
                    success=False, error="Invalid platform specified."
                )
            
            result = await geocoder.get_coordinates(address)
            if result.is_success():
                return GeocodeResponse(success=True, data=result.unwrap())
            return GeocodeResponse(success=False, error=result.unwrap_err())

        # If no platform is specified, try all available geocoders
        if not self.geocoders:
            return GeocodeResponse(
                success=False, error="No geocoders are configured."
            )

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_coordinates(address)
            if result.is_success():
                return GeocodeResponse(success=True, data=result.unwrap())
        
        return GeocodeResponse(
            success=False, error="All geocoding services failed."
        )