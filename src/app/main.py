import json
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils.logger import get_logger
from .utils.config import Config
from .utils.auth import validate_api_key
from .models import ExecutionRequest, ExecutionResponse
from .services.execution import execute_code

Config.validate()

app = FastAPI(
    title="Local Code Execution Engine",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

logger = get_logger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Log all HTTP requests and responses"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.info(json.dumps({
        "event": "request_received",
        "method": request.method,
        "path": request.url.path,
        "request_id": request_id
    }))

    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(json.dumps({
        "event": "response_sent",
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(process_time * 1000),
        "request_id": request_id
    }))

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


@app.middleware("http")
async def api_key_middleware(request, call_next):
    """Validate API key for all endpoints except /health"""
    try:
        await validate_api_key(request)
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"}
        )
    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info(json.dumps({
        "event": "health_check",
        "status": "running"
    }))
    return {"status": "running"}


@app.post("/execute")
async def execute(request: ExecutionRequest) -> ExecutionResponse:
    """Execute code and run tests"""
    logger.info(json.dumps({
        "event": "request_received",
        "exerciseId": request.exerciseId,
        "language": request.language
    }))

    response = await execute_code(request)

    logger.info(json.dumps({
        "event": "response_sent",
        "exerciseId": request.exerciseId,
        "passed": response.passed
    }))

    return response
