from src.models import Result, Success, Failure, Coordinates
from src.services.abstract import GeocoderBase
from src.services.cache import CacheManager


class NominatimGeocoder(GeocoderBase):
    """Implementation of GeocoderBase using Nominatim API."""

    name: str = "NominatimGeocoder"

    def __init__(
        self,
        *,
        cache: CacheManager,
        url: str = "https://nominatim.openstreetmap.org/search",
        user_agent: str = "MyGeocoderApp/1.0 (email@example.com)",
    ):
        """Initializes the Nominatim Geocoder with User Agent header"""
        self.cache = cache
        self.url = url
        self.user_agent = user_agent

    def execute(self):
        """Placeholder for the execution method."""

    async def get_coordinates(self, address: str) -> Result[list[Coordinates], str]:
        """Gets coordinates for a given address using Nominatim API.

        Args:
            address (str): The address to geocode.

        Returns:
            result (Result[list[Coordinates], str]):
                A Result containing a list of coordinates (on success)
                or an error message (on failure).
        """
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 5,  # Limit results to 5
        }

        result = await self._make_request(self.url, params, user_agent=self.user_agent)
        if result.is_failure():
            error_message = getattr(result, "error", None)
            if error_message is None:
                error_message = str(result)
            return Failure(error_message)

        try:
            data = result.unwrap()
            if not data:
                return Failure("No coordinates found for the given address.")

            coordinates_list = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                latitude = item.get("lat")
                longitude = item.get("lon")
                if latitude is None or longitude is None:
                    continue

                coordinates_list.append(
                    Coordinates(
                        latitude=float(latitude),
                        longitude=float(longitude),
                    )
                )

            if not coordinates_list:
                return Failure("No coordinates found for the given address.")

            return Success(coordinates_list)
        except (KeyError, TypeError, IndexError, ValueError) as e:
            return Failure(f"Invalid response format: {e}")
