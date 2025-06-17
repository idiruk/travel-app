# map_api/utils.py

from typing import List, Tuple
from .models import GeoEntity
import logging

from typing import List, Tuple, Union
import logging


def estimate_center(places: List[Union['GeoEntity', Tuple[float, float]]]) -> Tuple[float, float]:
    """
    Calculate geographic center point from a list of locations.

    Args:
        places: List of GeoEntity objects with lat/lon coordinates OR (lat, lon) tuples
    Returns:
        Tuple of (latitude, longitude) for the center point
    Raises:
        ValueError: If input contains invalid coordinate formats
    """
    if not places:
        logging.warning("No places provided to estimate center. Using default Rome.")
        return (41.9028, 12.4964)  # Default to Rome

    valid_coords = []

    for place in places:
        try:
            # Handle GeoEntity objects
            if hasattr(place, 'lat') and hasattr(place, 'lon'):
                if place.lat is not None and place.lon is not None:
                    valid_coords.append((float(place.lat), float(place.lon)))
            # Handle coordinate tuples
            elif isinstance(place, (tuple, list)) and len(place) == 2:
                lat, lon = place
                if lat is not None and lon is not None:
                    valid_coords.append((float(lat), float(lon)))
            else:
                logging.warning(f"Skipping invalid place: {place}")
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping place due to conversion error: {e}")

    if not valid_coords:
        logging.warning("No valid coordinates in places list. Using default center.")
        return (41.9028, 12.4964)

    try:
        avg_lat = sum(lat for lat, lon in valid_coords) / len(valid_coords)
        avg_lon = sum(lon for lat, lon in valid_coords) / len(valid_coords)

        # Validate the calculated coordinates
        if not (-90 <= avg_lat <= 90 and -180 <= avg_lon <= 180):
            raise ValueError("Calculated center is outside valid coordinate ranges")

        logging.info(f"Calculated center from {len(valid_coords)} points: ({avg_lat:.6f}, {avg_lon:.6f})")
        return (avg_lat, avg_lon)
    except Exception as e:
        logging.error(f"Center calculation failed: {str(e)}")
        return (41.9028, 12.4964)  # Fallback to Rome


def calculate_zoom(bbox: dict) -> int:
    """Calculate optimal zoom level based on bounding box"""
    lat_diff = bbox['max_lat'] - bbox['min_lat']
    lon_diff = bbox['max_lon'] - bbox['min_lon']
    max_diff = max(lat_diff, lon_diff)

    if max_diff > 20:
        return 4
    elif max_diff > 10:
        return 5
    elif max_diff > 5:
        return 6
    elif max_diff > 2:
        return 7
    else:
        return 8