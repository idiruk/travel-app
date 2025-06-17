from pydantic import BaseModel
from typing import Optional

class TravelIdeaRequest(BaseModel):
    """Input model for text generation"""
    idea: str
    creativity: float = 0.7  # Default temperature
    max_length: Optional[int] = 2000  # Token limit

class GeneratedTravelPlan(BaseModel):
    """Output model for generated text"""
    raw_text: str
    user_input: str  # Echo back for reference
    generation_time_ms: int
    model: str = "llama3"
    warnings: Optional[list[str]] = None  # Quality warnings