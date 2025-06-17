# geo_api/utils.py

from typing import Any

def extract_unique_items(items: list[Any]) -> list[Any]:
    """
    Removes duplicates while preserving order.
    """
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique