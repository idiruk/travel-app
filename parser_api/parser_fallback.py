# parser_api/parser_fallback.py
from typing import Dict, List
import spacy
from parser_api.utils import nlp  # Import the shared spaCy instance from utils


class ParserFallback:
    @staticmethod
    async def apply_fallbacks(llm_data: Dict, raw_text: str) -> Dict:
        """Fill in any missing fields from LLM output"""
        fields = [
            "sequence", "cities", "landmarks",
            "hotels", "roads", "transport_segments"
        ]

        result = llm_data.copy()

        for field in fields:
            if not result.get(field):
                result[field] = await getattr(ParserFallback, f"extract_{field}")(raw_text)

        return result

    @staticmethod
    async def full_fallback_parse(text: str) -> Dict:
        """Complete fallback when LLM parsing fails"""
        return {
            "sequence": await ParserFallback.extract_sequence(text),
            "cities": await ParserFallback.extract_cities(text),
            "landmarks": await ParserFallback.extract_landmarks(text),
            "hotels": await ParserFallback.extract_hotels(text),
            "roads": await ParserFallback.extract_roads(text),
            "transport_segments": await ParserFallback.extract_transport_segments(text)
        }

    @staticmethod
    async def extract_sequence(text: str) -> List[str]:
        doc = nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    @staticmethod
    async def extract_cities(text: str) -> List[Dict[str, str]]:
        return [{"name": city, "priority": "optional"}
                for city in await ParserFallback.extract_sequence(text)]

    @staticmethod
    async def extract_landmarks(text: str) -> List[str]:
        doc = nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ in ["FAC", "LOC", "ORG"]]

    @staticmethod
    async def extract_hotels(text: str) -> List[str]:
        doc = nlp(text)
        return [ent.text for ent in doc.ents if "hotel" in ent.text.lower()]

    @staticmethod
    async def extract_roads(text: str) -> List[str]:
        import re
        return list(set(re.findall(r"\b[A-Z]{1,3}\s?\d{1,4}\b", text)))

    @staticmethod
    async def extract_transport_segments(text: str) -> List[Dict[str, str]]:
        segments = []
        doc = nlp(text)

        for sent in doc.sents:
            if " from " in sent.text.lower() and " to " in sent.text.lower():
                parts = [p.strip() for p in sent.text.lower().split("from")[1].split("to")]
                if len(parts) == 2:
                    segments.append({
                        "from_city": parts[0],
                        "to_city": parts[1],
                        "mode": "unknown"
                    })
        return segments