import json
import spacy

# Shared spaCy instance for all fallback parsing
nlp = spacy.load("en_core_web_sm")

def repair_json_structure(raw_output: str):
    """
    Tries to fix and parse broken JSON from LLM output.
    Removes any leading/trailing text, repairs common errors.
    """
    try:
        # Try direct parse
        return json.loads(raw_output)
    except Exception:
        # Try to extract a valid JSON substring
        import re
        match = re.search(r'({.*})', raw_output, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except Exception:
                pass
        # More aggressive repair could go here
    return None

def validate_parsed_output(data):
    """
    Checks for missing required top-level fields. Returns list of problems or empty list.
    """
    required_fields = [
        "sequence", "cities", "landmarks", "hotels", "roads", "transport_segments"
    ]
    errors = []
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing field: {field}")
        # More field-by-field checks could be added here (e.g. empty lists)
    return errors