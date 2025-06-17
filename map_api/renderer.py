# map_api/renderer.py
import folium
from folium import Map, Marker
from map_api.models import MapRenderRequest
from map_api.utils import estimate_center
import logging
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('map_rendering.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default colors and icons for different entity types
DEFAULT_COLORS = {
    'cities': 'blue',
    'landmarks': 'green',
    'hotels': 'orange',
    'roads': 'gray',
    'transport': 'red'
}

ENTITY_ICONS = {
    'cities': 'home',
    'landmarks': 'info-sign',
    'hotels': 'bed',
    'roads': 'road'
}


def validate_coordinates(lat: Any, lon: Any) -> bool:
    """Validate that coordinates are within valid ranges."""
    try:
        return (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180)
    except (ValueError, TypeError):
        return False


def calculate_optimal_zoom(locations: List[Tuple[float, float]]) -> int:
    """
    Calculate optimal zoom level based on geographical spread of points.
    Args:
        locations: List of (lat, lon) tuples
    Returns:
        int: Zoom level between 6 (wide) and 14 (close)
    """
    if not locations:
        logger.debug("No locations provided for zoom calculation, using default zoom 6")
        return 6

    try:
        lats = [loc[0] for loc in locations]
        lons = [loc[1] for loc in locations]

        lat_span = max(lats) - min(lats)
        lon_span = max(lons) - min(lons)
        max_span = max(lat_span, lon_span)

        if max_span > 20:
            return 6
        elif max_span > 10:
            return 7
        elif max_span > 5:
            return 8
        elif max_span > 2:
            return 9
        elif max_span > 1:
            return 10
        elif max_span > 0.5:
            return 11
        elif max_span > 0.2:
            return 12
        else:
            return 13
    except Exception as e:
        logger.warning(f"Zoom calculation failed: {str(e)}, using default zoom 8")
        return 8


def extract_valid_entities(entities: Dict[str, List[Any]]) -> Tuple[List[Any], List[Tuple[float, float]]]:
    """
    Extract valid entities and their coordinates.
    Args:
        entities: Dictionary of entity types and their items
    Returns:
        Tuple of (valid_entities, valid_coordinates)
    """
    valid_entities = []
    valid_coordinates = []

    for entity_type, items in entities.items():
        if not isinstance(items, list):
            logger.warning(f"Expected list for {entity_type}, got {type(items)}")
            continue

        for item in items:
            try:
                if (hasattr(item, 'lat') and hasattr(item, 'lon') and
                        item.lat is not None and item.lon is not None and
                        validate_coordinates(item.lat, item.lon)):
                    valid_entities.append(item)
                    valid_coordinates.append((item.lat, item.lon))
                else:
                    logger.debug(f"Skipping invalid coordinates for {getattr(item, 'name', 'unnamed')} entity")
            except Exception as e:
                logger.warning(f"Error processing entity: {str(e)}")

    return valid_entities, valid_coordinates


def create_base_map(center: Tuple[float, float], zoom: int) -> Map:
    """Create and configure the base Folium map."""
    try:
        return Map(
            location=center,
            zoom_start=zoom,
            control_scale=True,
            tiles='CartoDB Positron',
            prefer_canvas=True
        )
    except Exception as e:
        logger.error(f"Failed to create base map: {str(e)}")
        raise


def add_entity_markers(fmap: Map, entities: Dict[str, List[Any]]) -> None:
    """Add markers for all entities to the map."""
    for entity_type, items in entities.items():
        if not isinstance(items, list):
            continue

        for item in items:
            try:
                if (hasattr(item, 'lat') and hasattr(item, 'lon') and
                        hasattr(item, 'name') and
                        item.lat is not None and item.lon is not None and
                        validate_coordinates(item.lat, item.lon)):
                    Marker(
                        location=[item.lat, item.lon],
                        popup=f"{entity_type[:-1].title()}: {item.name}",
                        icon=folium.Icon(
                            color=getattr(item, 'marker_color', None) or DEFAULT_COLORS.get(entity_type, 'blue'),
                            icon=getattr(item, 'marker_icon', None) or ENTITY_ICONS.get(entity_type, 'info-sign')
                        )
                    ).add_to(fmap)
            except Exception as e:
                logger.warning(f"Failed to add marker for {entity_type}: {str(e)}")


def add_transport_routes(fmap: Map, transport_segments: List[Any]) -> None:
    """Add transport routes to the map."""
    if not isinstance(transport_segments, list):
        logger.warning("Transport segments is not a list")
        return

    for seg in transport_segments:
        try:
            if (hasattr(seg, 'from_city') and hasattr(seg, 'to_city') and
                    hasattr(seg.from_city, 'lat') and hasattr(seg.from_city, 'lon') and
                    hasattr(seg.from_city, 'name') and
                    hasattr(seg.to_city, 'lat') and hasattr(seg.to_city, 'lon') and
                    hasattr(seg.to_city, 'name') and
                    seg.from_city.lat is not None and seg.from_city.lon is not None and
                    seg.to_city.lat is not None and seg.to_city.lon is not None and
                    validate_coordinates(seg.from_city.lat, seg.from_city.lon) and
                    validate_coordinates(seg.to_city.lat, seg.to_city.lon)):

                folium.PolyLine(
                    locations=[
                        [seg.from_city.lat, seg.from_city.lon],
                        [seg.to_city.lat, seg.to_city.lon]
                    ],
                    color=getattr(seg, 'color', None) or DEFAULT_COLORS['transport'],
                    weight=3,
                    opacity=0.7,
                    tooltip=f"{getattr(seg, 'mode', 'route')}: {seg.from_city.name} → {seg.to_city.name}"
                ).add_to(fmap)
            else:
                from_name = getattr(getattr(seg, 'from_city', None), 'name', 'unknown')
                to_name = getattr(getattr(seg, 'to_city', None), 'name', 'unknown')
                logger.warning(f"Skipping transport segment {from_name} → {to_name} - invalid data")
        except Exception as e:
            logger.warning(f"Failed to process transport segment: {str(e)}")


def render_map(data: MapRenderRequest) -> str:
    """
    Render a Folium map with all geographic entities.
    Args:
        data: MapRenderRequest containing all locations and routes
    Returns:
        str: HTML representation of the map
    """
    logger.info("Starting map rendering process")

    try:
        if not isinstance(data, MapRenderRequest):
            raise ValueError("Input data must be a MapRenderRequest instance")

        entities = {
            'cities': getattr(data, 'cities', []),
            'landmarks': getattr(data, 'landmarks', []),
            'hotels': getattr(data, 'hotels', []),
            'roads': getattr(data, 'roads', [])
        }

        valid_entities, valid_coordinates = extract_valid_entities(entities)

        if not valid_coordinates:
            logger.warning("No valid coordinates found - using default center")
            center = (41.9028, 12.4964)
            zoom = 6
        else:
            try:
                center = estimate_center(valid_coordinates)
                zoom = calculate_optimal_zoom(valid_coordinates)
            except Exception as e:
                logger.warning(f"Failed to calculate center/zoom: {str(e)}")
                center = valid_coordinates[0]
                zoom = 10

        fmap = create_base_map(center, zoom)
        add_entity_markers(fmap, entities)

        if hasattr(data, 'transport_segments'):
            add_transport_routes(fmap, data.transport_segments)

        folium.TileLayer('Stamen Terrain').add_to(fmap)
        folium.TileLayer('OpenStreetMap').add_to(fmap)
        folium.LayerControl().add_to(fmap)

        logger.info("Map rendering completed successfully")
        return fmap._repr_html_()

    except Exception as e:
        logger.error(f"❌ Map rendering failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Map rendering failed: {str(e)}") from e