from pydantic import BaseModel
from typing import List, Optional, Literal
from geo_api.models import GeoEntity as GeoEntityBase  # Reuse from geo_api

# Extended GeoEntity with map-specific fields
class GeoEntity(GeoEntityBase):
    marker_color: Optional[str] = None

class GeoTransportSegment(BaseModel):
    from_city: GeoEntity
    to_city: GeoEntity
    mode: Literal["train", "car", "bus", "flight", "boat", "ferry", "unknown"]
    duration: Optional[str] = None  # Changed to match geo_api
    notes: Optional[str] = None

class MapRenderRequest(BaseModel):
    cities: List[GeoEntity]
    landmarks: List[GeoEntity]
    hotels: List[GeoEntity]
    roads: List[GeoEntity]
    transport_segments: List[GeoTransportSegment]
    bounding_box: Optional[dict] = None  # Added to match geo_api
    style_preferences: Optional[dict] = None  # New field for customization