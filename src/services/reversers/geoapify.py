from src.models import Result, Success, Failure, Address, Coordinates
from src.services.abstract import ReverseGeocoderBase
from src.services.cache import CacheManager


class GeoapifyReverseGeocoder(ReverseGeocoderBase):
    """Implementation of ReverseGeocoderBase using Geoapify API."""

    name: str = "GeoapifyReverseGeocoder"
    url: str = "https://api.geoapify.com/v1/geocode/reverse"
    api_key: str

    def __init__(self, cache: CacheManager, api_key: str):
        """Initializes the Geoapify Reverse Geocoder with API key

        Args:
            cache (CacheManager): The cache manager instance.
            api_key (str): Geoapify API key.
        """
        self.cache = cache
        self.api_key = api_key

    def execute(self):
        pass

    async def get_addresses(
        self, coordinates: Coordinates
    ) -> Result[list[Address], str]:
        """Gets addresses for given geographic coordinates using Geoapify API.

        Args:
            coordinates (Coordinates): The geographic coordinates.

        Returns:
            result (Result[list[Address], str]):
                A Result containing either a list of addresses (on success)
                or an error message (on failure).
        """
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "apiKey": self.api_key,
            "type": "building",  # Mejorar precisión
        }
        result: Result = await self._make_request(self.url, params)
        if result.is_failure():
            return result

        try:
            features = result.unwrap().get("features", [])
            if not features:
                return Failure("No address found for coordinates")

            # Parsear resultados de la respuesta
            addresses = []
            for feature in features:
                props: dict = feature.get("properties", {})
                addresses.append(
                    Address(
                        formatted_address=props.get("formatted") or "",
                        postcode=props.get("postcode") or "",
                        country=props.get("country") or "",
                        state=props.get("state") or "",
                        district=props.get("district") or "",
                        settlement=props.get("city") or props.get("town") or "",
                        suburb=props.get("suburb") or "",
                        street=props.get("street") or "",
                        house=props.get("name") or props.get("housenumber") or "",
                    )
                )
            return Success(addresses)
        except (KeyError, TypeError) as e:
            return Failure(f"Invalid response format: {str(e)}")
