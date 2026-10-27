import secrets
import logging
from typing import Optional
from fastapi import Request, Header, HTTPException, status
from app.core.config import settings

logger = logging.getLogger("insightflow.security")


def get_client_ip(request: Request) -> str:
    """Extracts client IP safely, accounting for reverse proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """
    Enforces API authentication when configured.
    Supports either 'X-API-Key: <key>' or 'Authorization: Bearer <key>'.

    In development mode with no API_AUTH_KEY set, access is permitted
    with an audit log to maintain zero-friction local developer experience.
    When API_AUTH_KEY is configured (or in production), invalid keys return 401.
    """
    is_production = settings.ENVIRONMENT.strip().lower() == "production"
    configured_key = settings.API_AUTH_KEY.strip()
    enforce_auth = settings.ENABLE_API_KEY_AUTH or bool(configured_key) or is_production

    if is_production and not configured_key:
        logger.critical(
            f"PRODUCTION SECURITY VIOLATION: Request rejected from {get_client_ip(request)} on {request.url.path} - "
            "ENVIRONMENT is set to 'production' but API_AUTH_KEY is not configured!"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security configuration error. API authentication key must be configured in production.",
        )

    if not enforce_auth:
        # Development permissive mode
        return True

    provided_key: Optional[str] = None
    if x_api_key:
        provided_key = x_api_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        provided_key = authorization[7:].strip()

    if not provided_key:
        logger.warning(
            f"Unauthorized request blocked from {get_client_ip(request)} on {request.url.path} (missing API key)"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required API key. Provide via 'X-API-Key' header or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing attack vulnerabilities
    if not secrets.compare_digest(provided_key, configured_key):
        logger.warning(
            f"Unauthorized request blocked from {get_client_ip(request)} on {request.url.path} (invalid API key)"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
