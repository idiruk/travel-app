# parser_api/ollama_client.py
import httpx
from fastapi import HTTPException
import logging

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"
TIMEOUT = 60  # Shorter timeout for parsing

logger = logging.getLogger(__name__)


async def query_ollama(prompt: str) -> str:
    """Optimized for structured parsing with strict output"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,  # More deterministic output
            "num_ctx": 2048,  # Smaller context sufficient
            "format": "json"  # Hint for JSON output
        }
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            return response.json()["response"]

    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama parsing error: {e.response.text}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse travel plan: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Ollama parsing service error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Parser service unavailable"
        )