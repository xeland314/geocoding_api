from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx

from src.models import Result, Address, Coordinates
from src.models.failure import Failure
from src.models.success import Success


class ServiceCommandBase(ABC):
    """Abstract base class for service commands.

    Attributes:
        name (str): Name of the service command.
    """

    name: str
    url: str

    @abstractmethod
    def execute(self) -> None:
        """Executes the command. Must be implemented by subclasses."""

    def safe_execute(self) -> None:
        """Safely executes the command, handling common exceptions."""
        try:
            self.execute()
        except (RuntimeError, ValueError) as e:  # Specific exceptions can be expanded.
            print(f"Error executing {self.name}: {e}")

    async def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        timeout: int = 30,
        /,
        user_agent: Optional[str] = None,
    ) -> Result[Dict[str, Any], str]:
        """Make HTTP request to an URL with error handling."""
        try:
            headers = None
            if user_agent:
                headers = {"User-Agent": user_agent}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, timeout=timeout, headers=headers
                )
                response.raise_for_status()
                return Success(response.json())
        except httpx.TimeoutException:
            return Failure("Request timeout.")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return Failure("API rate limit exceeded.")
            return Failure(f"HTTP error: {e.response.text}")
        except httpx.RequestError as e:
            return Failure(f"Request failed: {e}")        
        return Failure("An unexpected error occurred while making the request.")

    def __str__(self) -> str:
        """Returns a string representation of the service command."""
        return f"ServiceCommandBase(name={self.name})"

    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"<ServiceCommandBase name='{self.name}'>"

    def __eq__(self, other) -> bool:
        """Checks equality between two ServiceCommandBase objects."""
        if not isinstance(other, ServiceCommandBase):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Generates a hash based on the service name."""
        return hash(self.name)


class GeocoderBase(ServiceCommandBase):
    """Abstract base class for geocoding commands.

    Attributes:
        name (str): Name of the service command.
    """

    def execute(self):
        pass

    @abstractmethod
    async def get_coordinates(self, address: str) -> Result[Coordinates, str]:
        """Gets geographic coordinates for a given address asynchronously.

        Args:
            address (str): The address to geocode.

        Returns:
            result (Result[Coordinates, str]):
                A `Result` containing either the coordinates
                (on success) or an error message (on failure).
        """


class ReverseGeocoderBase(ServiceCommandBase):
    """Abstract base class for reverse geocoding commands.

    Attributes:
        name (str): Name of the service command.
    """

    @abstractmethod
    async def get_addresses(
        self, coordinates: Coordinates
    ) -> Result[list[Address], str]:
        """Gets addresses for given geographic coordinates asynchronously.

        Args:
            coordinates (Coordinates): The geographic coordinates.

        Returns:
            result (Result[list[Address], str]):
                A `Result` containing either a list of addresses
                (on success) or an error message (on failure).
        """
