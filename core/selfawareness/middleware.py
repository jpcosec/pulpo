"""
FastAPI middleware for framework self-awareness.

Automatically tracks API requests, errors, and performance.
"""

import time
from collections.abc import Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from .events import FrameworkEventLevel, FrameworkEventType
from .tracking import capture_event


class SelfAwarenessMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks API requests and errors.

    Captures:
    - Request errors (4xx, 5xx)
    - Slow requests (configurable threshold)
    - Request validation errors
    """

    def __init__(self, app: ASGIApp, slow_request_ms: int = 1000):
        """
        Initialize middleware.

        Args:
            app: The ASGI app
            slow_request_ms: Threshold for slow request warning (default 1000ms)
        """
        super().__init__(app)
        self.slow_request_ms = slow_request_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track events.

        Args:
            request: The incoming request
            call_next: The next middleware/handler

        Returns:
            The response
        """
        start_time = time.time()

        # Track basic request info
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Track errors
            if response.status_code >= 400:
                await capture_event(
                    level=FrameworkEventLevel.ERROR
                    if response.status_code >= 500
                    else FrameworkEventLevel.WARN,
                    event_type=FrameworkEventType.API_REQUEST_ERROR,
                    module="api",
                    message=f"{method} {path} returned {response.status_code}",
                    duration_ms=int(duration_ms),
                    metadata={
                        "path": path,
                        "method": method,
                        "status": response.status_code,
                    },
                )

            # Track slow requests
            elif duration_ms > self.slow_request_ms:
                await capture_event(
                    level=FrameworkEventLevel.WARN,
                    event_type=FrameworkEventType.API_REQUEST_SLOW,
                    module="api",
                    message=f"Slow request: {method} {path} took {duration_ms:.0f}ms",
                    duration_ms=int(duration_ms),
                    metadata={
                        "path": path,
                        "method": method,
                        "threshold_ms": self.slow_request_ms,
                    },
                )

            # Track info level for successful requests if verbose
            else:
                await capture_event(
                    level=FrameworkEventLevel.DEBUG,
                    event_type=FrameworkEventType.API_REQUEST_SLOW,  # Use as generic success
                    module="api",
                    message=f"{method} {path} -> {response.status_code}",
                    duration_ms=int(duration_ms),
                    metadata={"path": path, "method": method, "status": response.status_code},
                )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            await capture_event(
                level=FrameworkEventLevel.ERROR,
                event_type=FrameworkEventType.API_REQUEST_ERROR,
                module="api",
                message=f"Exception in {method} {path}: {e.__class__.__name__}",
                duration_ms=int(duration_ms),
                error_details={
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                },
                metadata={
                    "path": path,
                    "method": method,
                },
            )

            raise


def add_selfawareness_middleware(
    app: FastAPI,
    slow_request_ms: int = 1000,
) -> None:
    """
    Add self-awareness middleware to a FastAPI app.

    Args:
        app: FastAPI application instance
        slow_request_ms: Threshold for slow request warning
    """
    app.add_middleware(SelfAwarenessMiddleware, slow_request_ms=slow_request_ms)
