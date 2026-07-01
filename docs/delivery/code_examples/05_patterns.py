# Common Implementation Patterns
# Reference these when implementing stories

import json
import shutil
from asyncio import Lock
from fastapi import FastAPI

# ============================================
# 1. Logging Pattern
# ============================================
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Log structured events as JSON
logger.info(json.dumps({
    "event": "execution_started",
    "exerciseId": "python_001",
    "language": "python",
    "timestamp": "2026-07-01T12:00:00Z"
}))


# ============================================
# 2. Cleanup Pattern (Always in finally)
# ============================================
async def handle_execution(request):
    workspace = None
    container = None
    try:
        # Do work
        workspace = await create_workspace()
        container = await run_container(workspace)
        result = await collect_results(container)
        return result
    finally:
        # Always cleanup, even on error
        if container:
            await docker_client.cleanup_container(container)
        if workspace:
            shutil.rmtree(workspace, ignore_errors=True)


# ============================================
# 3. Concurrency Pattern (Docker Lock)
# ============================================
docker_execution_lock = Lock()


async def execute_docker(workspace):
    """Only one Docker execution at a time"""
    async with docker_execution_lock:
        container = docker_client.containers.run(...)
        result = await wait_for_completion(container)
        return result


# ============================================
# 4. Async Endpoint Pattern
# ============================================
@FastAPI.post("/execute")
async def execute(request):
    # 1. Validate (async)
    await validate_api_key(request)

    # 2. Prepare (sync, fast)
    workspace = prepare_workspace(request)

    # 3. Execute (async, waits for Docker)
    result = await execute_in_docker(workspace)

    # 4. Cleanup (async)
    await cleanup(workspace)

    return result


# ============================================
# 5. File Handling Pattern (UTF-8)
# ============================================
def write_files(workspace, code, tests):
    """Write code and tests with UTF-8 encoding"""
    with open(f"{workspace}/user_code.py", "w", encoding="utf-8") as f:
        f.write(code)

    with open(f"{workspace}/test_solution.py", "w", encoding="utf-8") as f:
        f.write(tests)


# ============================================
# 6. Error Response Pattern (200 with error)
# ============================================
execution_error_response = {
    "passed": False,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "error": {
        "type": "SyntaxError",
        "message": "...",
        "line": 1
    },
    "tests": [],
    "stdout": "",
    "stderr": "..."
}


# ============================================
# 7. Middleware Pattern (API Key)
# ============================================
@app.middleware("http")
async def api_key_middleware(request, call_next):
    """Validate API key for all endpoints except /health"""
    try:
        await validate_api_key(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    return await call_next(request)
