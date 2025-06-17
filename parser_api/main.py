# parser_api/main.py
from fastapi import FastAPI, HTTPException
from .services.llm_parser import LLMParser
from .parser_fallback import ParserFallback
from .models import ParserInput, ParsedOutput
from .utils import validate_parsed_output
import logging

# Configure logger
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/parse", response_model=ParsedOutput)
async def parse_travel_plan(data: ParserInput):
    try:
        llm_result = await LLMParser.extract_structured_info(
            data.raw_text,
            data.user_input
        )

        validated_data = await ParserFallback.apply_fallbacks(
            llm_result,
            data.raw_text
        )

        if errors := validate_parsed_output(validated_data):
            logger.warning("Validation issues: %s", errors)

        return ParsedOutput(
            **validated_data,
            parse_strategy="hybrid",
            confidence_score=0.9
        )

    except Exception as e:
        logger.error("LLM parsing failed: %s", str(e), exc_info=True)
        fallback_data = await ParserFallback.full_fallback_parse(data.raw_text)
        return ParsedOutput(
            **fallback_data,
            parse_strategy="fallback",
            confidence_score=0.6
        )