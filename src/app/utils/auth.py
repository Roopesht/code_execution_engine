import os
from fastapi import HTTPException, Request, status

EXECUTOR_API_KEY = os.getenv("EXECUTOR_API_KEY")

if not EXECUTOR_API_KEY:
    raise ValueError("EXECUTOR_API_KEY environment variable is required")


async def validate_api_key(request: Request) -> None:
    """Validate X-API-Key header"""
    if request.url.path == "/health":
        return

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != EXECUTOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
