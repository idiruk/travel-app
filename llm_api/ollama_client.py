import httpx
from fastapi import HTTPException
import logging

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"
TIMEOUT = 120  # Longer timeout for text generation

logger = logging.getLogger(__name__)

async def query_ollama(prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """Call Ollama with custom temperature and max tokens."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096,
            "num_predict": max_tokens
        }
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            return response.json()["response"]

    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API error: {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"Ollama generation failed: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Ollama connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Ollama service unavailable"
        )