"""
API Middleware
==============

Middleware components for the FastAPI application.

Teaching Points:
- Middleware wraps every request/response cycle
- Order matters: first added = outermost layer
- Use middleware for cross-cutting concerns (logging, auth, rate limiting)
"""

import time
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("smart_home_api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every request with method, path, status code, and duration.

    Teaching Point:
        Observability is critical for debugging production issues.
        This middleware provides basic request-level logging.

    Example log output:
        INFO: POST /api/v1/chat 200 (0.523s)
        INFO: GET /api/v1/health 200 (0.012s)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log the request
        logger.info(
            "%s %s %d (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        # Add timing header for debugging
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple token-bucket rate limiter (teaching-level implementation).

    Teaching Points:
        - Token bucket: each client gets N tokens, refilled over time
        - Tokens are consumed per request
        - When tokens run out, return 429 Too Many Requests

    Note:
        This is a simplified in-memory implementation for teaching.
        Production systems use Redis or similar distributed stores.
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        """
        Args:
            app: The ASGI application
            max_requests: Maximum requests per window per client
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # client_ip -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean up old entries outside the window
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if now - ts < self.window_seconds
        ]

        # Check if over limit
        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Maximum {self.max_requests} requests per {self.window_seconds} seconds",
                },
            )

        # Record this request
        self._requests[client_ip].append(now)

        # Process the request
        return await call_next(request)
