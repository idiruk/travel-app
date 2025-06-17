from fastapi import FastAPI, HTTPException
from geo_api.models import GeoRequest, GeoResponse
from geo_api.geocoder import geocode_all
import logging
import httpx

app = FastAPI(title="Geo API", version="1.0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.post("/geocode", response_model=GeoResponse)
async def geocode(data: dict):  # Accept raw dict input
    try:
        logger.info(f"Starting geocoding for {len(data['cities'])} cities")

        # Convert dict to GeoRequest model
        request = GeoRequest(**data)
        result = await geocode_all(request)

        logger.info(f"Geocoding completed for {len(result.cities)} locations")
        return result

    except Exception as e:
        logger.error(f"Geocoding failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Geocoding processing failed"
        )