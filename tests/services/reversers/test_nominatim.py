import pytest
from unittest.mock import AsyncMock, patch
from src.models import Coordinates, Success, Failure
from src.services.reversers.nominatim import NominatimReverseGeocoder


@pytest.mark.asyncio
async def test_nominatim_reverse_geocoder_success():
    """Test successful reverse geocoding with Nominatim."""
    # Arrange
    mock_response = {
        "place_id": 259193717,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "way",
        "osm_id": 424573716,
        "lat": "40.712776",
        "lon": "-74.005974",
        "display_name": "New York, United States",
        "address": {
            "city": "New York",
            "state": "New York",
            "postcode": "10007",
            "country": "United States",
            "country_code": "us",
        },
    }

    geocoder = NominatimReverseGeocoder(user_agent="TestApp/1.0")
    coordinates = Coordinates(latitude=40.7128, longitude=-74.0060)

    # Act
    with patch.object(
        geocoder, "_make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = Success(mock_response)
        result = await geocoder.get_addresses(coordinates)

    # Assert
    assert result.is_success()
    addresses = result.unwrap()
    assert len(addresses) == 1
    assert addresses[0].city == "New York"
    assert addresses[0].country == "United States"


@pytest.mark.asyncio
async def test_nominatim_reverse_geocoder_failure():
    """Test failed reverse geocoding with Nominatim."""
    # Arrange
    geocoder = NominatimReverseGeocoder(user_agent="TestApp/1.0")
    coordinates = Coordinates(latitude=0, longitude=0)

    # Act
    with patch.object(
        geocoder, "_make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = Failure("API Error")
        result = await geocoder.get_addresses(coordinates)

    # Assert
    assert result.is_failure()
    assert result.unwrap_err() == "API Error"


@pytest.mark.asyncio
async def test_nominatim_reverse_geocoder_empty_response():
    """Test reverse geocoding with an empty response from Nominatim."""
    # Arrange
    geocoder = NominatimReverseGeocoder(user_agent="TestApp/1.0")
    coordinates = Coordinates(latitude=0, longitude=0)

    # Act
    with patch.object(
        geocoder, "_make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = Success({})
        result = await geocoder.get_addresses(coordinates)

    # Assert
    assert result.is_failure()
    assert "No address found" in result.unwrap_err()
