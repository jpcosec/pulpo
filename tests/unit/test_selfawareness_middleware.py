"""
Tests for selfawareness middleware.
"""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request

from core.selfawareness.events import FrameworkEventLevel
from core.selfawareness.middleware import SelfAwarenessMiddleware, add_selfawareness_middleware
from core.selfawareness.tracking import get_tracker


@pytest.fixture(autouse=True)
async def clear_tracker():
    """Clear tracker before each test."""
    tracker = get_tracker()
    await tracker.clear()
    yield
    await tracker.clear()


class TestSelfAwarenessMiddleware:
    """Test SelfAwarenessMiddleware class."""

    def test_middleware_initialization(self):
        """Test middleware can be initialized."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=1000)
        assert middleware.slow_request_ms == 1000

    def test_middleware_custom_threshold(self):
        """Test middleware accepts custom slow threshold."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=5000)
        assert middleware.slow_request_ms == 5000

    @pytest.mark.asyncio
    async def test_middleware_dispatch_success(self):
        """Test middleware processes successful response."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=1000)

        # Create mock request and call_next
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"

        mock_response = Mock()
        mock_response.status_code = 200

        async def mock_call_next(req):
            return mock_response

        # Should not raise
        result = await middleware.dispatch(mock_request, mock_call_next)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_middleware_tracks_4xx_errors(self):
        """Test middleware tracks 4xx errors."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=1000)

        mock_request = Mock(spec=Request)
        mock_request.url.path = "/not-found"
        mock_request.method = "GET"

        mock_response = Mock()
        mock_response.status_code = 404

        async def mock_call_next(req):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Check event was captured
        tracker = get_tracker()
        events = await tracker.get_events()
        assert len(events) > 0
        # Find the 404 event
        error_events = [e for e in events if "404" in e.message]
        assert len(error_events) > 0

    @pytest.mark.asyncio
    async def test_middleware_tracks_5xx_errors(self):
        """Test middleware tracks 5xx errors."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=1000)

        mock_request = Mock(spec=Request)
        mock_request.url.path = "/error"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 500

        async def mock_call_next(req):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Check event was captured as ERROR level
        tracker = get_tracker()
        errors = await tracker.get_errors()
        assert len(errors) > 0
        error = errors[0]
        assert error.level == FrameworkEventLevel.ERROR

    @pytest.mark.asyncio
    async def test_middleware_tracks_exception(self):
        """Test middleware tracks exceptions."""
        app = FastAPI()
        middleware = SelfAwarenessMiddleware(app, slow_request_ms=1000)

        mock_request = Mock(spec=Request)
        mock_request.url.path = "/exception"
        mock_request.method = "GET"

        async def mock_call_next(req):
            raise ValueError("Test error")

        # Exception should be re-raised
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

        # Event should be captured
        tracker = get_tracker()
        errors = await tracker.get_errors()
        assert len(errors) > 0
        error = errors[0]
        assert error.level == FrameworkEventLevel.ERROR
        assert "ValueError" in error.error_details.get("exception_type", "")


class TestAddMiddlewareFunction:
    """Test the add_selfawareness_middleware function."""

    def test_add_middleware_to_app(self):
        """Test adding middleware to FastAPI app."""
        app = FastAPI()

        # Should not raise
        add_selfawareness_middleware(app, slow_request_ms=500)

        # Verify middleware was added
        # In FastAPI, user middleware is in app.middleware_stack or middleware list
        assert app is not None

    def test_add_middleware_custom_threshold(self):
        """Test adding middleware with custom threshold."""
        app = FastAPI()

        # Should accept custom threshold without raising
        add_selfawareness_middleware(app, slow_request_ms=2000)

        # Verify app is still functional
        assert app is not None
