import time
import logging
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, status

from app.core.config import settings
from app.core.security import get_client_ip

logger = logging.getLogger("insightflow.middleware")


class SecurityAndRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production security middleware providing:
    1. Request payload size enforcement (blocks oversized JSON attacks).
    2. In-memory sliding-window rate limiting per IP address.
    3. Security response headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy).
    """

    def __init__(self, app):
        super().__init__(app)
        # Store timestamp history per IP: Dict[ip_str, List[timestamp_float]]
        self.request_history: Dict[str, List[float]] = {}
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        path = request.url.path
        now = time.time()

        # 1. Periodic cleanup of stale rate-limit history every 5 minutes
        if now - self.last_cleanup > 300:
            self._cleanup_stale_history(now)
            self.last_cleanup = now

        # 2. Enforce Request Body Size Limits (except for document uploads which have 20MB limit)
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("Content-Length")
            if content_length:
                try:
                    size_bytes = int(content_length)
                    # File and dataset upload routes have 50MB limit; all other routes have 2MB limit
                    max_allowed = 50 * 1024 * 1024 if ("/upload" in path or "/datasets" in path) else settings.MAX_REQUEST_SIZE_BYTES
                    if size_bytes > max_allowed:
                        logger.warning(
                            f"Blocked oversized request from {client_ip} to {path} ({size_bytes} bytes > {max_allowed} max)"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={"detail": f"Request payload exceeds maximum allowed size of {max_allowed // (1024*1024)}MB."},
                        )
                except ValueError:
                    pass

        # 3. Sliding-window Rate Limiting (exempt /health and static root)
        if path not in ("/health", "/", "/docs", "/openapi.json"):
            rate_limit = settings.RATE_LIMIT_PER_MINUTE
            history = self.request_history.setdefault(client_ip, [])

            # Filter out requests older than 60 seconds
            window_start = now - 60.0
            history = [t for t in history if t > window_start]
            self.request_history[client_ip] = history

            if len(history) >= rate_limit:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {path} ({len(history)} req/min)")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Please slow down and try again in 1 minute."},
                    headers={"Retry-After": "60"},
                )

            history.append(now)

        # 4. Proceed with request execution
        response = await call_next(request)

        # 5. Attach Security Hardening Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    def _cleanup_stale_history(self, now: float):
        cutoff = now - 120.0
        keys_to_delete = []
        for ip, times in self.request_history.items():
            fresh_times = [t for t in times if t > cutoff]
            if fresh_times:
                self.request_history[ip] = fresh_times
            else:
                keys_to_delete.append(ip)
        for ip in keys_to_delete:
            del self.request_history[ip]
