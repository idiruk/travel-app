import asyncio
import httpx
import logging
import os  # Import the os module
from typing import List, Optional
from geo_api.models import GeoEntity, GeoRequest, GeoResponse, GeoTransportSegment

# Fetch Nominatim URL from environment variable, with a default
NOMINATIM_URL = os.getenv("NOMINATIM_URL_ENV", "https://nominatim.openstreetmap.org/search")
# Fetch User-Agent from environment variable, with a default
NOMINATIM_USER_AGENT = os.getenv("NOMINATIM_USER_AGENT_ENV", "travel-app/1.0")
HEADERS = {"User-Agent": NOMINATIM_USER_AGENT}
DELAY_BETWEEN_REQUESTS = 1  # seconds
MAX_RETRIES = 3

logger = logging.getLogger(__name__)


async def fetch_coordinates(name: str) -> Optional[GeoEntity]:
    """Enhanced with retries and better error handling"""
    params = {"q": name, "format": "json", "limit": 1}

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(NOMINATIM_URL, params=params, headers=HEADERS)
                response.raise_for_status()

                if data := response.json():
                    return GeoEntity(
                        name=name,
                        lat=float(data[0]["lat"]),
                        lon=float(data[0]["lon"])
                    )

                logger.warning(f"No coordinates found for: {name}")
                return None

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to geocode {name} after {MAX_RETRIES} attempts")
                return None
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS * (attempt + 1))


async def geocode_items(items: List[str]) -> List[GeoEntity]:
    """Batch geocoding with rate limiting"""
    results = []
    for item in set(items):  # Deduplicate first
        if entity := await fetch_coordinates(item):
            results.append(entity)
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    return results


async def geocode_all(data: GeoRequest) -> GeoResponse:
    """Handle both model instances and raw dicts"""
    # Convert all cities to names (handles both dict and model input)
    city_names = [
        city['name'] if isinstance(city, dict) else city.name
        for city in data.cities
    ]

    # Convert transport segments
    transport_segments = []
    for seg in data.transport_segments:
        if isinstance(seg, dict):
            transport_segments.append(TransportSegment(**seg))
        else:
            transport_segments.append(seg)

    # Geocode all locations
    cities = await geocode_items(city_names)
    landmarks = await geocode_items(data.landmarks)
    hotels = await geocode_items(data.hotels)
    roads = await geocode_items(data.roads)

    # Process transport segments
    geo_transport_segments = []
    for seg in transport_segments:
        from_entity = await fetch_coordinates(seg.from_city) or GeoEntity(name=seg.from_city)
        to_entity = await fetch_coordinates(seg.to_city) or GeoEntity(name=seg.to_city)

        geo_transport_segments.append(GeoTransportSegment(
            from_city=from_entity,
            to_city=to_entity,
            mode=seg.mode,
            time=seg.duration,
            notes=seg.notes
        ))

    return GeoResponse(
        cities=cities,
        landmarks=landmarks,
        hotels=hotels,
        roads=roads,
        transport_segments=geo_transport_segments
    )