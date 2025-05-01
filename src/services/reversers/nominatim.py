from src.models import Result, Success, Failure, Address, Coordinates
from src.services.abstract import ReverseGeocoderBase


class NominatimReverseGeocoder(ReverseGeocoderBase):
    """Implementation of ReverseGeocoderBase using Nominatim API."""

    name: str = "NominatimReverseGeocoder"

    def __init__(
        self,
        url: str = "https://nominatim.openstreetmap.org/reverse",
        /,
        user_agent: str = "MyGeocoderApp/1.0 (email@example.com)",
    ):
        """Initializes the Nominatim Reverse Geocoder with User Agent header"""
        self.url = url
        self.user_agent = user_agent

    def execute(self):
        """Placeholder for the execution method."""

    async def get_addresses(
        self, coordinates: Coordinates
    ) -> Result[list[Address], str]:
        """Gets addresses for given geographic coordinates using Nominatim API.

        Args:
            coordinates (Coordinates): The geographic coordinates.

        Returns:
            result (Result[list[Address], str]):
                A Result containing a list of addresses (on success)
                or an error message (on failure).
        """
        params = {
            "format": "json",
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "accept-language": "en",
            "addressdetails": 1,
        }

        result = self._make_request(self.url, params, user_agent=self.user_agent)
        if result.is_failure():
            return result

        try:
            data = result.unwrap()
            items = data.get("address", None)
            if not items:
                return Failure("No address found for the given coordinates.")

            address_data: dict = data["address"]

            # Construye la lista de objetos Address
            addresses = [
                Address(
                    formatted_address=data.get("display_name", ""),
                    postcode=address_data.get("postcode"),
                    country=address_data.get("country"),
                    state=address_data.get("state") or address_data.get("plot"),
                    district=address_data.get("state_district"),
                    settlement=address_data.get("city") or address_data.get("village"),
                    suburb=address_data.get("suburb")
                    or address_data.get("city_district"),
                    street=address_data.get("road"),
                    house=address_data.get("house_number"),
                )
            ]
            return Success(addresses)
        except (KeyError, TypeError, IndexError) as e:
            return Failure(f"Invalid response format: {e}")
