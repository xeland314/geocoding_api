import os
from typing import Optional
from src.models import Coordinates
from src.responses import ReverseGeocodeResponse
from src.services.abstract import ReverseGeocoderBase
from src.services.reversers.geoapify import GeoapifyReverseGeocoder
from src.services.reversers.here import HereReverseGeocoder
from src.services.reversers.nominatim import NominatimReverseGeocoder


class GeocoderReverser:
    """Class for managing dynamic configuration and geocoder search."""

    def __init__(self):
        """Initializes a dictionary of geocoders based on environment variables."""
        self.geocoders: dict[str, ReverseGeocoderBase] = {
            "GEOAPIFY": GeoapifyReverseGeocoder(api_key=os.getenv("GEOAPIFY_API_KEY")),
            "HERE": HereReverseGeocoder(api_key=os.getenv("HERE_API_KEY")),
            "NOMINATIM": NominatimReverseGeocoder(
                user_agent=os.getenv("NOMINATIM_USER_AGENT")
            ),
            "NOMINATIM_REPLICA_1": NominatimReverseGeocoder(
                os.getenv("NOMINATIM_REVERSER_REPLICA_URL_1"),
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
        self, coordinates: Coordinates, platform: Optional[str] = None
    ) -> ReverseGeocodeResponse:
        """
        Performs reverse geocoding using a specified geocoder or tries all
        available geocoders until one succeeds.
        """
        if platform:
            geocoder = self.geocoders.get(platform.upper())
            if not geocoder:
                return ReverseGeocodeResponse(
                    success=False, error="Invalid platform specified."
                )

            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                return ReverseGeocodeResponse(success=True, data=result.unwrap())
            return ReverseGeocodeResponse(success=False, error=result.unwrap_err())

        # If no platform is specified, try all available geocoders
        if not self.geocoders:
            return ReverseGeocodeResponse(
                success=False, error="No geocoders are configured."
            )

        for geocoder_name, geocoder in self.geocoders.items():
            result = await geocoder.get_addresses(coordinates)
            if result.is_success():
                return ReverseGeocodeResponse(success=True, data=result.unwrap())

        return ReverseGeocodeResponse(
            success=False, error="All geocoding services failed."
        )
