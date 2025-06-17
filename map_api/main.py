# map_api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from map_api.models import MapRenderRequest
from map_api.renderer import render_map
import logging

app = FastAPI(title="Map API", version="0.1")

logging.basicConfig(level=logging.INFO)

@app.post("/render", response_class=HTMLResponse)
def render_map_endpoint(data: MapRenderRequest):
    logging.info("🗺️ Received map render request")
    try:
        html = render_map(data)
        return HTMLResponse(content=html)
    except Exception as e:
        logging.error(f"❌ Map rendering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Map rendering error: {e}")