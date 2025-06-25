from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from src.models import Coordinates
from src.responses import GeocodeResponse, ReverseGeocodeResponse, GeocodersResponse
from src.services.cache import CacheManager
from src.services.geocoders import Geocoder
from src.services.reversers import GeocoderReverser

# Cache and geocoder manager instances
cache_manager = CacheManager()

# FastAPI instance with lifespan management
app = FastAPI(lifespan=cache_manager.lifespan)

# Dynamic geocoder managers
geocoder = Geocoder(cache=cache_manager)
geocoder_reverser = GeocoderReverser(cache=cache_manager)


@app.get("/geocode", response_model=GeocodeResponse)
async def geocode(
    address: str = Query(..., min_length=1),
    platform: Optional[str] = None,
):
    """
    Geocoding endpoint to convert an address into geographic coordinates.
    """
    response = await geocoder.search(address, platform)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return response


@app.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    platform: Optional[str] = None,
):
    """
    Reverse geocoding endpoint using dynamically registered platforms.
    """
    coordinates = Coordinates(latitude=latitude, longitude=longitude)
    response = await geocoder_reverser.search(coordinates, platform)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return response


@app.get("/geocoders", response_model=GeocodersResponse)
def get_geocoders():
    """
    Returns the list of configured geocoders.
    """
    if not geocoder.geocoders:
        raise HTTPException(status_code=404, detail="No geocoders are configured.")

    print(f"Available geocoders: {list(geocoder.geocoders)}")
    return GeocodersResponse(
        geocoders=[
            {"name": name, "url": geocoder.url}
            for name, geocoder in geocoder.geocoders.items()
        ]
    )


@app.get("/reversers", response_model=GeocodersResponse)
def get_reversers():
    """
    Returns the list of configured reverse geocoders.
    """
    if not geocoder_reverser.geocoders:
        raise HTTPException(
            status_code=404, detail="No reverse geocoders are configured."
        )

    return GeocodersResponse(
        geocoders=[
            {"name": name, "url": geocoder.url}
            for name, geocoder in geocoder_reverser.geocoders.items()
        ]
    )
