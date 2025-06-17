import re
from fastapi import HTTPException

async def validate_text_response(text: str) -> str:
    """Validate raw LLM output meets minimum quality standards"""
    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="LLM response too short to be valid"
        )
    if not any(c.isalpha() for c in text):
        raise HTTPException(
            status_code=422,
            detail="LLM response does not contain valid content"
        )
    return text

def sanitize_input(prompt: str) -> str:
    """Prevent prompt injection attacks"""
    return re.sub(r"[^\w\s,.!?\-']", "", prompt)[:2000]