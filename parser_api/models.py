from pydantic import BaseModel
from typing import List, Dict, Optional, Literal

class ParserInput(BaseModel):
    raw_text: str
    user_input: Optional[str] = None  # Provided by orchestrator

class TransportSegment(BaseModel):
    from_city: str
    to_city: str
    mode: Optional[str] = None
    time: Optional[str] = None
    notes: Optional[str] = None

class CityItem(BaseModel):
    name: str
    priority: Literal["mandatory", "optional"]

class ParsedOutput(BaseModel):
    sequence: List[str]
    cities: List[CityItem]
    landmarks: List[str]
    hotels: List[str]
    roads: List[str]
    transport_segments: List[TransportSegment]
    parse_strategy: str = "hybrid"
    confidence_score: float = 1.0