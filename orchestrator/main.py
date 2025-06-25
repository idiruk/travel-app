# orchestrator/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import logging
from datetime import datetime, timezone
import uuid
import json
from enum import Enum
import asyncio
import os

from fastapi.middleware.cors import CORSMiddleware


# === BEGIN: VERBOSE API LOGGING SWITCH ===
VERBOSE_API_LOG = os.getenv("VERBOSE_API_LOG", "true").lower() == "true"
# =========================================

# Color codes for tmux/ANSI terminals
API_COLORS = {
    "LLM_API": "\033[94m",      # Blue
    "PARSER_API": "\033[92m",   # Green
    "GEO_API": "\033[93m",      # Yellow
    "MAP_API": "\033[95m",      # Magenta
    "ENDC": "\033[0m"
}

def print_api_payload(api_name, label, payload):
    if VERBOSE_API_LOG:
        color = API_COLORS.get(api_name, "")
        endc = API_COLORS["ENDC"]
        print(f"{color}[{api_name}] {label}:{endc}")
        if isinstance(payload, (dict, list)):
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(str(payload))
        print(f"{color}{'='*60}{endc}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceURLs(str, Enum):
    # Environment variable: LLM_API_URL
    LLM_API = os.getenv("LLM_API_URL", "http://localhost:8000/generate")
    # Environment variable: PARSER_API_URL
    PARSER_API = os.getenv("PARSER_API_URL", "http://localhost:8001/parse")
    # Environment variable: GEO_API_URL
    GEO_API = os.getenv("GEO_API_URL", "http://localhost:8002/geocode")
    # Environment variable: MAP_API_URL
    MAP_API = os.getenv("MAP_API_URL", "http://localhost:8003/render")

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class OrchestratorRequest(BaseModel):
    user_input: str
    user_id: str
    session_id: Optional[str] = None
    callback_url: Optional[str] = None

class Notification(BaseModel):
    type: NotificationType
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    status: str
    travel_plan: Optional[str] = None
    map_html: Optional[str] = None
    enriched_data: Optional[Dict[str, Any]] = None
    notifications: List[Notification] = []
    request_id: str

app = FastAPI(title="Travel Orchestrator", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestState:
    def __init__(self):
        self.active_requests = {}

state = RequestState()

async def send_notification(request_id: str, notification: Notification, callback_url: Optional[str] = None):
    """Send notification to frontend and log it"""
    logger.info(f"[{request_id}] {notification.type.upper()}: {notification.message}")
    if notification.details:
        logger.debug(f"[{request_id}] Details: {json.dumps(notification.details, indent=2)}")
    if callback_url:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json=notification.model_dump(),
                    timeout=2
                )
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to send notification: {str(e)}")

async def call_service(
        request_id: str,
        service_url: str,
        payload: Dict[str, Any],
        callback_url: Optional[str] = None,
        retries: int = 3,
        expect_json: bool = True
) -> Dict[str, Any]:
    """Generic service caller with retries, notifications, and verbose payload logging"""
    last_error = None

    # Figure out which API is being called
    api_name = None
    for key in API_COLORS:
        if key in service_url:
            api_name = key
            break
    # fallback for exact endpoint match
    for api_key in ["LLM_API", "PARSER_API", "GEO_API", "MAP_API"]:
        if getattr(ServiceURLs, api_key).value in service_url:
            api_name = api_key

    for attempt in range(retries):
        try:
            notification = Notification(
                type=NotificationType.INFO,
                message=f"Calling {service_url} (attempt {attempt + 1})",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            await send_notification(request_id, notification, callback_url)

            # === VERBOSE OUTGOING REQUEST ===
            print_api_payload(api_name, "REQUEST", payload)

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(service_url, json=payload)
                response.raise_for_status()

                # === VERBOSE INCOMING RESPONSE ===
                if expect_json:
                    resp_json = response.json()
                else:
                    resp_json = response.text
                print_api_payload(api_name, "RESPONSE", resp_json)

                notification = Notification(
                    type=NotificationType.SUCCESS,
                    message=f"Service {service_url} completed successfully",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                await send_notification(request_id, notification, callback_url)

                return resp_json

        except httpx.HTTPStatusError as e:
            last_error = f"HTTP error from {service_url}: {e.response.text}"
            logger.error(f"[{request_id}] {last_error}")
        except httpx.RequestError as e:
            last_error = f"Connection error to {service_url}: {str(e)}"
            logger.error(f"[{request_id}] {last_error}")
        except Exception as e:
            last_error = f"Unexpected error with {service_url}: {str(e)}"
            logger.error(f"[{request_id}] {last_error}")

        if attempt < retries - 1:
            await asyncio.sleep(1 * (attempt + 1))

    error_notification = Notification(
        type=NotificationType.ERROR,
        message=f"Failed to call {service_url} after {retries} attempts",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={"error": last_error} # last_error already contains specific details
    )
    await send_notification(request_id, error_notification, callback_url)
    # Use the detailed last_error message for the HTTPException
    raise HTTPException(status_code=503, detail=last_error)

async def process_travel_request(
        request_id: str,
        user_input: str,
        callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """Orchestrate the entire travel planning workflow"""
    try:
        llm_response = await call_service(
            request_id,
            ServiceURLs.LLM_API,
            {"idea": user_input},
            callback_url,
            expect_json=True
        )
        travel_plan_text = llm_response.get("raw_text", "")

        notification = Notification(
            type=NotificationType.SUCCESS,
            message="Travel plan generated successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"travel_plan": travel_plan_text[:200] + "..." if len(travel_plan_text) > 200 else travel_plan_text}
        )
        await send_notification(request_id, notification, callback_url)

        parser_response = await call_service(
            request_id,
            ServiceURLs.PARSER_API,
            {
                "raw_text": travel_plan_text,
                "user_input": user_input
            },
            callback_url,
            expect_json=True
        )
        notification = Notification(
            type=NotificationType.SUCCESS,
            message="Travel plan parsed successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"parsed_data": {k: len(v) if isinstance(v, list) else v for k, v in parser_response.items()}}
        )
        await send_notification(request_id, notification, callback_url)

        geo_response = await call_service(
            request_id,
            ServiceURLs.GEO_API,
            parser_response,
            callback_url,
            expect_json=True
        )
        notification = Notification(
            type=NotificationType.SUCCESS,
            message="Geotagging completed successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"geo_data": {k: len(v) if isinstance(v, list) else v for k, v in geo_response.items()}}
        )
        await send_notification(request_id, notification, callback_url)

        map_response = await call_service(
            request_id,
            ServiceURLs.MAP_API,
            geo_response,
            callback_url,
            expect_json=False
        )
        notification = Notification(
            type=NotificationType.SUCCESS,
            message="Map rendered successfully",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        await send_notification(request_id, notification, callback_url)

        return {
            "status": "completed",
            "travel_plan": travel_plan_text,
            "map_html": map_response,
            "enriched_data": geo_response
        }

    except HTTPException as e:
        logger.error(f"[{request_id}] Orchestration failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected orchestration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Orchestration process failed")

@app.post("/plan-trip", response_model=OrchestratorResponse)
async def plan_trip(
        request: OrchestratorRequest,
        background_tasks: BackgroundTasks
):
    """Main endpoint for trip planning orchestration"""
    request_id = str(uuid.uuid4())
    request.session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"[{request_id}] Starting trip planning for user {request.user_id}")
    logger.debug(f"[{request_id}] User input: {request.user_input}")

    state.active_requests[request_id] = {
        "status": "processing",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "user_id": request.user_id
    }

    notification = Notification(
        type=NotificationType.INFO,
        message="Starting trip planning process",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={"request_id": request_id}
    )
    await send_notification(request_id, notification, request.callback_url)

    background_tasks.add_task(
        process_request_background,
        request_id,
        request.user_input,
        request.callback_url
    )

    return OrchestratorResponse(
        status="processing",
        request_id=request_id,
        notifications=[notification]
    )

async def process_request_background(
        request_id: str,
        user_input: str,
        callback_url: Optional[str]
):
    """Background task handler for request processing"""
    try:
        result = await process_travel_request(request_id, user_input, callback_url)
        state.active_requests[request_id].update({
            "status": "completed",
            "end_time": datetime.now(timezone.utc).isoformat(),
            "result": result
        })
    except Exception as e:
        state.active_requests[request_id].update({
            "status": "error",
            "end_time": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        })

@app.get("/status/{request_id}")
def get_status(request_id: str):
    """Check the status of a trip planning request"""
    req = state.active_requests.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request ID not found")
    return req

@app.get("/debug/logs")
def get_logs(lines: int = 100):
    """Retrieve recent logs for debugging"""
    try:
        with open('orchestrator.log', 'r') as f:
            log_lines = f.readlines()
        return {"logs": log_lines[-lines:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))