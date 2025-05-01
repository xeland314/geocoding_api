from pydantic import BaseModel, Field
from src.models.address import Address
from src.models.coordinates import Coordinates


class Place(BaseModel):
    """Model to represent a Place, combining Coordinates and Address.

    Attributes:
        coordinates (Coordinates): Geographic coordinates of the place.
        address (Address): Address details of the place.
    """
    coordinates: Coordinates = Field(
        ..., description="Geographic coordinates associated with the place"
    )
    address: Address = Field(
        ..., description="Address details associated with the place"
    )

    def __str__(self) -> str:
        """Returns a string representation of the Place object."""
        return f"Place(coordinates={self.coordinates}, address={self.address})"
