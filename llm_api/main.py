from fastapi import FastAPI
from llm_api.models import TravelIdeaRequest, GeneratedTravelPlan
from llm_api.ollama_client import query_ollama
from llm_api.utils import sanitize_input, validate_text_response
import time
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Text Generation API", version="1.0")

@app.post("/generate", response_model=GeneratedTravelPlan)
async def generate_travel_text(request: TravelIdeaRequest) -> GeneratedTravelPlan:
    """Generate natural language travel plan"""
    start_time = time.time()

    # Validate and sanitize input
    clean_input = sanitize_input(request.idea)
    prompt = (
        f"Create a detailed travel itinerary including cities, landmarks, transport, and accommodations for: {clean_input}"
    )

    # Pass creativity and max_length to the LLM
    raw_response = await query_ollama(
        prompt,
        temperature=request.creativity,
        max_tokens=request.max_length
    )
    validated_text = await validate_text_response(raw_response)

    return GeneratedTravelPlan(
        raw_text=validated_text,
        user_input=request.idea,
        generation_time_ms=int((time.time() - start_time) * 1000),
        model="llama3"
    )