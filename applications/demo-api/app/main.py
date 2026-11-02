import asyncio
import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from app.core.config import Settings, get_settings

SERVICE_NAME = "demo-api"
SERVICE_VERSION = "1.0.0"
DEFAULT_DELAY_SECONDS = 5
REQUEST_ID_HEADER = "X-Request-ID"
# Client-supplied request IDs are only reused when short and log-safe
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

# 1. Structured JSON Logger Setup
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("demo_api")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

core_router = APIRouter()
demo_router = APIRouter(prefix="/demo", tags=["Failure Simulation"])

def _route_of(request: Request) -> str:
    """Route template (e.g. /demo/failure/{mode}) when matched, raw path otherwise."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)

def _error_category(status_code: int) -> Optional[str]:
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return None

# Request logging middleware (registered in create_app)
async def log_requests(request: Request, call_next):
    incoming_id = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming_id if REQUEST_ID_PATTERN.match(incoming_id) else str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"{request.method} {_route_of(request)} raised an unhandled exception",
            exc_info=True,
            extra={
                "extra": {
                    "request_id": request_id,
                    "method": request.method,
                    "route": _route_of(request),
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "error_category": "unhandled_exception",
                    "exception_type": type(exc).__name__,
                }
            }
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    log_fields = {
        "request_id": request_id,
        "method": request.method,
        "route": _route_of(request),
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }
    error_category = _error_category(response.status_code)
    if error_category:
        log_fields["error_category"] = error_category

    logger.info(f"{request.method} {_route_of(request)} handled", extra={"extra": log_fields})
    response.headers[REQUEST_ID_HEADER] = request_id
    return response

# --- Endpoints ---

# Main Endpoint
@core_router.get("/", tags=["Main"])
async def root():
    return {"message": "Demo API operational", "version": SERVICE_VERSION}

# Liveness Probe (Health Check)
@core_router.get("/healthz", tags=["Health"])
async def health_check():
    """Verifies process liveness."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Readiness Probe
@core_router.get("/readyz", tags=["Health"])
async def readiness_check(request: Request):
    """Verifies if the application can accept traffic."""
    app_state = request.app.state.readiness
    if not app_state["is_ready"] or not app_state["database_connected"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "reason": "Database connection offline"}
        )
    return {"status": "ready", "database": "connected"}

# Controlled Failures
@demo_router.get("/failure/{mode}")
async def trigger_failure(request: Request, mode: str, delay: Optional[int] = None):
    """Simulates 500 errors, unhandled exceptions, or response timeouts."""
    if mode == "500":
        logger.error("Simulated 500 error triggered", extra={"extra": {"failure_mode": "500"}})
        raise HTTPException(status_code=500, detail="Controlled internal server error")
    elif mode == "exception":
        logger.critical("Simulated uncaught exception triggered", extra={"extra": {"failure_mode": "uncaught_exception"}})
        raise RuntimeError("Controlled unhandled application exception")
    elif mode == "timeout":
        max_delay = request.app.state.settings.max_delay_seconds
        if delay is None:
            delay = min(DEFAULT_DELAY_SECONDS, max_delay)
        if not 0 <= delay <= max_delay:
            raise HTTPException(status_code=422, detail=f"delay must be between 0 and {max_delay} seconds")
        await asyncio.sleep(delay)
        return {"status": "delayed", "delay_seconds": delay}
    else:
        raise HTTPException(status_code=400, detail="Modes: '500', 'exception', 'timeout'")

# Readiness State Toggle
@demo_router.post("/toggle-ready")
async def toggle_readiness(request: Request, ready: bool):
    """Manually toggle readiness to test load balancer behavior."""
    app_state = request.app.state.readiness
    app_state["is_ready"] = ready
    app_state["database_connected"] = ready
    logger.warning(f"Readiness manually set to {ready}", extra={"extra": {"is_ready": ready}})
    return {"message": f"Readiness state updated to {ready}", "app_state": app_state}

# --- App Factory ---

def create_app(settings: Settings | None = None) -> FastAPI:
    """Builds the app; /demo/* routes are only registered when fault simulation is enabled."""
    settings = settings or get_settings()

    app = FastAPI(title="Observability Demo API", version=SERVICE_VERSION)
    app.state.settings = settings
    # Simulated dependency state, per app instance so tests stay isolated
    app.state.readiness = {"is_ready": True, "database_connected": True}
    app.middleware("http")(log_requests)
    app.include_router(core_router)

    if settings.fault_simulation_enabled:
        logger.warning(
            "Fault simulation ENABLED: /demo/* routes are exposed",
            extra={"extra": {"fault_simulation_enabled": True}},
        )
        app.include_router(demo_router)

    return app
