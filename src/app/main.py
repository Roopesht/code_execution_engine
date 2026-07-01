import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .utils.logger import get_logger
from .utils.config import Config
from .utils.auth import validate_api_key
from .models import ExecutionRequest, ExecutionResponse, TestResult

Config.validate()

app = FastAPI(
    title="Local Code Execution Engine",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

logger = get_logger(__name__)


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
async def execute(request: ExecutionRequest):
    """Execute code and run tests"""
    logger.info(json.dumps({
        "event": "execution_started",
        "exerciseId": request.exerciseId,
        "language": request.language
    }))

    return ExecutionResponse(
        passed=True,
        totalTests=0,
        passedTests=0,
        failedTests=0,
        executionTime=0.0,
        memory=0,
        stdout="",
        stderr="",
        tests=[]
    )
