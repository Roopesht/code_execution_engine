import json
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils.logger import get_logger
from .utils.config import Config
from .utils.auth import validate_api_key
from .models import ExecutionRequest, ExecutionResponse
from .models.feedback import (
    FeedbackRequest, FeedbackResponse, ErrorResponse, ErrorDetail,
    GenericFeedbackRequest, GenericFeedbackResponse, TokenUsage
)
from .services.execution import execute_code
from .services.feedback import (
    get_llm_feedback, get_generic_feedback, FeedbackError, LLMError,
    LLMUnavailableError, LLMTimeoutError
)

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
    """Validate API key for all endpoints except /health and CORS preflight"""
    # Skip validation for CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    try:
        await validate_api_key(request)
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"}
        )
    return await call_next(request)

@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Log all HTTP requests and responses"""
    # Skip middleware for CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

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

# Add CORS middleware (must be added last so it runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

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


@app.post("/feedback")
async def generic_feedback(request: GenericFeedbackRequest) -> GenericFeedbackResponse:
    """Generic AI feedback - like ChatGPT API

    Ask any question about code, debugging, concepts, etc.
    Responses are tailored to the user's level (beginner/intermediate/advanced).
    """

    logger.info(json.dumps({
        "event": "generic_feedback_request",
        "level": request.level,
        "language": request.language,
        "prompt_length": len(request.prompt)
    }))

    try:
        # Call LLM service for generic feedback
        result = await get_generic_feedback(
            prompt=request.prompt,
            language=request.language,
            level=request.level,
            context=request.context,
            max_tokens_override=request.max_tokens,
            temperature_override=request.temperature
        )

        logger.info(json.dumps({
            "event": "generic_feedback_success",
            "level": request.level,
            "latency_ms": result["latency_ms"],
            "tokens": result["tokens"]["total"]
        }))

        return GenericFeedbackResponse(
            status="success",
            response=result["response"],
            model=result["model"],
            tokens=TokenUsage(**result["tokens"]),
            latency_ms=result["latency_ms"],
            generatedAt=datetime.utcnow()
        )

    except LLMTimeoutError as e:
        logger.error(json.dumps({"event": "feedback_error", "code": e.code, "error": e.message}))
        raise HTTPException(
            status_code=504,
            detail={
                "status": "error",
                "code": "LLM_TIMEOUT",
                "error": "Gateway Timeout: LLM generation did not complete within 30 seconds",
                "details": {"timeout_seconds": 30}
            }
        )

    except LLMUnavailableError as e:
        logger.error(json.dumps({"event": "feedback_error", "code": e.code, "error": e.message}))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "code": "LLM_UNAVAILABLE",
                "error": "Service Unavailable: LLM service unreachable on port 8001",
                "details": {"llm_port": 8001, "timeout_seconds": 30}
            }
        )

    except LLMError as e:
        logger.error(json.dumps({"event": "feedback_error", "code": e.code, "error": e.message}))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "LLM_ERROR",
                "error": "Internal Server Error: LLM generation failed",
                "details": {"reason": e.message[:100]}
            }
        )

    except Exception as e:
        logger.error(json.dumps({"event": "unexpected_error", "error": str(e), "type": type(e).__name__}))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "INTERNAL_ERROR",
                "error": "Internal server error",
                "details": {}
            }
        )


@app.post("/feedback-test")
async def feedback_test(request: FeedbackRequest) -> FeedbackResponse:
    """Get AI feedback on failed code"""

    logger.info(json.dumps({
        "event": "feedback_request",
        "exerciseId": request.exerciseId,
        "language": request.language,
        "num_failed_tests": len(request.failedTests)
    }))

    try:
        # Call LLM service for feedback
        response = await get_llm_feedback(request)

        logger.info(json.dumps({
            "event": "feedback_success",
            "exerciseId": request.exerciseId,
            "latency_ms": response.latency_ms,
            "tokens": response.tokens.total
        }))

        return response

    except LLMTimeoutError as e:
        logger.error(json.dumps({
            "event": "feedback_error",
            "code": e.code,
            "error": e.message
        }))
        raise HTTPException(
            status_code=504,
            detail={
                "status": "error",
                "code": "LLM_TIMEOUT",
                "error": f"Gateway Timeout: LLM generation did not complete within 30 seconds",
                "details": {"timeout_seconds": 30}
            }
        )

    except LLMUnavailableError as e:
        logger.error(json.dumps({
            "event": "feedback_error",
            "code": e.code,
            "error": e.message
        }))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "code": "LLM_UNAVAILABLE",
                "error": f"Service Unavailable: LLM service unreachable on port 8001",
                "details": {"llm_port": 8001, "timeout_seconds": 30}
            }
        )

    except LLMError as e:
        logger.error(json.dumps({
            "event": "feedback_error",
            "code": e.code,
            "error": e.message
        }))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "LLM_ERROR",
                "error": f"Internal Server Error: LLM generation failed",
                "details": {"reason": e.message[:100]}
            }
        )

    except FeedbackError as e:
        logger.error(json.dumps({
            "event": "feedback_error",
            "code": e.code,
            "error": e.message
        }))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": e.code,
                "error": e.message,
                "details": e.details
            }
        )

    except Exception as e:
        logger.error(json.dumps({
            "event": "unexpected_error",
            "error": str(e),
            "type": type(e).__name__
        }))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "INTERNAL_ERROR",
                "error": "Internal server error",
                "details": {}
            }
        )
