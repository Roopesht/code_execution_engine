import os
import re
import logging
from fastapi import HTTPException, Request, status

EXECUTOR_API_KEY = os.getenv("EXECUTOR_API_KEY")

if not EXECUTOR_API_KEY:
    raise ValueError("EXECUTOR_API_KEY environment variable is required")


def validate_api_key_strength(api_key: str) -> bool:
    """Validate API key meets minimum security requirements"""
    if len(api_key) < 32:
        return False
    if not re.search(r'[a-zA-Z]', api_key):
        return False
    if not re.search(r'[0-9]', api_key):
        return False
    return True


# Validate key strength on startup and warn if weak
if not validate_api_key_strength(EXECUTOR_API_KEY):
    logger = logging.getLogger(__name__)
    logger.warning(
        "⚠️  API key is weak (min 32 chars, mix of letters+numbers). "
        "This works for development but MUST be changed in production."
    )


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
