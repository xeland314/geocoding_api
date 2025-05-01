from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    """Model to represent geographic coordinates with validation.

    Attributes:
        latitude (float): Latitude in the range of -90 to 90.
        longitude (float): Longitude in the range of -180 to 180.
    """
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in the range of -90 to 90"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in the range of -180 to 180"
    )

    def __str__(self) -> str:
        """Returns a string representation of the Coordinates object."""
        return f"Coordinates(latitude={self.latitude}, longitude={self.longitude})"
