# geo_api/models.py
from pydantic import BaseModel
from typing import List, Literal, Optional, Union

class City(BaseModel):
    name: str
    priority: Literal["mandatory", "optional"]

class GeoEntity(BaseModel):
    """Represents a geocoded location with coordinates"""
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    type: Optional[str] = None  # Can be 'city', 'landmark', 'hotel', etc.

class TransportSegment(BaseModel):
    """Input transport model from parser"""
    from_city: str
    to_city: str
    mode: Literal["train", "car", "bus", "flight", "boat", "ferry", "unknown"]
    duration: Optional[str] = None  # Changed from 'time' to match parser_api
    notes: Optional[str] = None

class GeoTransportSegment(BaseModel):
    """Geocoded transport segment with coordinates"""
    from_city: GeoEntity
    to_city: GeoEntity
    mode: str
    duration: Optional[str] = None
    notes: Optional[str] = None

class BoundingBox(BaseModel):
    """Geographic bounds for map rendering"""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

class GeoRequest(BaseModel):
    """Input model matching parser_api's output"""
    sequence: List[str]
    cities: List[Union[City, dict]]  # Accepts both models and raw dicts
    landmarks: List[str]
    hotels: List[str]
    roads: List[str]
    transport_segments: List[Union[TransportSegment, dict]]

class GeoResponse(BaseModel):
    """Complete geocoding output model"""
    cities: List[GeoEntity]
    landmarks: List[GeoEntity]
    hotels: List[GeoEntity]
    roads: List[GeoEntity]
    transport_segments: List[GeoTransportSegment]
    bounding_box: Optional[BoundingBox] = None
    warnings: Optional[List[str]] = None  # For reporting partial failures

    class Config:
        json_schema_extra = {
            "example": {
                "cities": [
                    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "type": "city"}
                ],
                "landmarks": [
                    {"name": "Eiffel Tower", "lat": 48.8584, "lon": 2.2945, "type": "landmark"}
                ],
                "transport_segments": [
                    {
                        "from_city": {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
                        "to_city": {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
                        "mode": "train",
                        "duration": "2 hours"
                    }
                ],
                "bounding_box": {
                    "min_lat": 45.7640,
                    "max_lat": 48.8584,
                    "min_lon": 2.2945,
                    "max_lon": 4.8357
                }
            }
        }