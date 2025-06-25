from typing import List, Union
from pydantic import BaseModel

from src.models.address import Address
from src.models.coordinates import Coordinates


class ReverseGeocodeResponse(BaseModel):
    """Model to represent the response of a reverse geocoding request."""

    success: bool
    data: Union[List[Address], None] = None
    error: Union[str, None] = None


class GeocodeResponse(BaseModel):
    """Model to represent the response of a geocoding request."""

    success: bool
    data: Union[List[Coordinates], None] = None
    error: Union[str, None] = None


class GeocoderInfo(BaseModel):
    """Defines the structure of a geocoder in the response."""

    name: str
    url: str


class GeocodersResponse(BaseModel):
    """Response model for listing configured geocoders."""

    geocoders: List[GeocoderInfo]
