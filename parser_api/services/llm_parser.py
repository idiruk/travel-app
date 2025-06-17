# parser_api/services/llm_parser.py
from typing import Dict, Any
from ..ollama_client import query_ollama
import json
from ..utils import repair_json_structure


class LLMParser:
    """Handles all LLM-based structured extraction with validation"""

    @staticmethod
    async def extract_structured_info(text: str, user_input: str) -> Dict[str, Any]:
        prompt = f"""
You are a structured data extraction engine.

Your task is to analyze a block of natural language text describing a travel plan and extract the required fields into a strict JSON format.

Do not explain. Do not comment. Return only a valid JSON object with the following structure:

{{
  "sequence": ["city1", "city2", ...],
  "cities": [
    {{"name": "CityName", "priority": "mandatory" | "optional"}}
  ],
  "landmarks": ["Landmark 1", "Landmark 2", ...],
  "hotels": ["Hotel 1", "Hotel 2", ...],
  "roads": ["A2", "R66", "E40"...],
  "transport_segments": [
    {{"from_city": "CityA", "to_city": "CityB", "mode": "transport mode" , "time": "number of hours", "notes": "optional text"}}
  ]
}}

Field definitions:
- "sequence": order of cities as mentioned in the trip.
- "cities": all mentioned cities with a priority:
  - "Mandatory" if directly stated in the user input.
  - "Optional" if only suggested or loosely mentioned.
- "landmarks": specific named points of interest (e.g., monuments, attractions, plazas, streets).
- "hotels": names of accommodations.
- "roads": name of roads or highways.
- "transport_segments": describe how the user moves between cities. "mode": "train" or "car" or "bus" or "flight" or "boat" or "ferry" or any other mode of transport

Make sure to cross-check against the user input below for city priority tagging.

User input:
\"\"\"
{user_input}
\"\"\"

Text to analyze:
\"\"\"
{text}
\"\"\"

Return only the JSON.
"""

        try:
            # Get raw LLM response
            llm_output = await query_ollama(prompt)

            # Repair and validate JSON structure
            parsed_data = repair_json_structure(llm_output)

            if not parsed_data:
                raise ValueError("LLM returned invalid JSON structure")

            return parsed_data

        except Exception as e:
            # Log detailed error for debugging
            error_info = {
                "error": str(e),
                "user_input": user_input[:200] + "..." if len(user_input) > 200 else user_input,
                "llm_output": llm_output[:500] + "..." if llm_output and len(llm_output) > 500 else llm_output
            }
            raise ValueError(f"LLM Parsing failed: {json.dumps(error_info)}")