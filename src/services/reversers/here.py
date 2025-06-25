from src.models import Result, Success, Failure, Address, Coordinates
from src.services.abstract import ReverseGeocoderBase
from src.services.cache import CacheManager


class HereReverseGeocoder(ReverseGeocoderBase):
    """Implementation of ReverseGeocoderBase using HERE.com API."""

    name: str = "HereReverseGeocoder"
    url: str = "https://revgeocode.search.hereapi.com/v1/revgeocode"
    api_key: str

    def __init__(self, cache: CacheManager, api_key: str):
        """Initializes the HERE Reverse Geocoder with the API key.

        Args:
            cache (CacheManager): The cache manager instance.
            api_key (str): HERE.com API key.
        """
        self.cache = cache
        self.api_key = api_key

    def execute(self):
        pass

    async def get_addresses(
        self, coordinates: Coordinates
    ) -> Result[list[Address], str]:
        """Performs reverse geocoding to obtain addresses from coordinates.

        Args:
            coordinates (Coordinates): The latitude and longitude to reverse geocode.

        Returns:
            result (Result[list[Address], str]):
                A Result containing a list of addresses (Success)
                or an error message (Failure).
        """
        params = {
            "at": f"{coordinates.latitude},{coordinates.longitude}",
            "apiKey": self.api_key,
            "lang": "en-US",  # Cambia según preferencias de idioma si es necesario.
        }

        # Realizar la solicitud HTTP
        result = await self._make_request(self.url, params)
        if result.is_failure():
            return result

        try:
            # Procesar los datos de la respuesta
            items = result.unwrap().get("items", [])
            if not items:
                return Failure("No address found for the given coordinates.")

            # Crear lista de direcciones
            addresses = []
            for item in items:
                address_data: dict = item.get("address", {})
                addresses.append(
                    Address(
                        formatted_address=address_data.get("label", ""),
                        postcode=address_data.get("postalCode"),
                        country=address_data.get("countryCode"),
                        state=address_data.get("state"),
                        district=address_data.get("district"),
                        settlement=address_data.get("city"),
                        suburb=address_data.get("subdistrict"),
                        street=address_data.get("street"),
                        house=address_data.get("houseNumber"),
                    )
                )
            return Success(addresses)

        except (KeyError, TypeError, IndexError) as e:
            return Failure(f"Invalid response format: {e}")
