"""
Tests for selfawareness event tracking.
"""


import pytest

from core.selfawareness.events import (
    FrameworkEvent,
    FrameworkEventLevel,
    FrameworkEventType,
)
from core.selfawareness.tracking import (
    EventTracker,
    capture_event,
    capture_exception,
    get_tracker,
)


@pytest.fixture
def tracker():
    """Create a fresh tracker for each test."""
    return EventTracker(max_events=100)


@pytest.fixture
async def async_tracker():
    """Create an async tracker for async tests."""
    tracker = EventTracker(max_events=100)
    yield tracker
    await tracker.clear()


class TestEventTracker:
    """Test EventTracker class."""

    @pytest.mark.asyncio
    async def test_capture_event(self, tracker):
        """Test capturing a single event."""
        event = FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Test event",
        )

        await tracker.capture(event)

        assert len(tracker) == 1
        assert tracker.events[0].message == "Test event"

    @pytest.mark.asyncio
    async def test_capture_multiple_events(self, tracker):
        """Test capturing multiple events."""
        for i in range(5):
            event = FrameworkEvent(
                level=FrameworkEventLevel.INFO,
                event_type=FrameworkEventType.API_REQUEST_ERROR,
                module="api",
                message=f"Event {i}",
            )
            await tracker.capture(event)

        assert len(tracker) == 5

    @pytest.mark.asyncio
    async def test_max_events_limit(self):
        """Test that tracker respects max_events limit."""
        tracker = EventTracker(max_events=10)

        # Add more than max
        for i in range(20):
            event = FrameworkEvent(
                level=FrameworkEventLevel.INFO,
                event_type=FrameworkEventType.API_REQUEST_ERROR,
                module="api",
                message=f"Event {i}",
            )
            await tracker.capture(event)

        # Should only have last 10
        assert len(tracker) == 10
        # Should be events 10-19
        assert tracker.events[0].message == "Event 10"
        assert tracker.events[9].message == "Event 19"

    @pytest.mark.asyncio
    async def test_get_events_all(self, tracker):
        """Test retrieving all events."""
        for i in range(5):
            event = FrameworkEvent(
                level=FrameworkEventLevel.INFO,
                event_type=FrameworkEventType.API_REQUEST_ERROR,
                module="api",
                message=f"Event {i}",
            )
            await tracker.capture(event)

        events = await tracker.get_events()

        assert len(events) == 5
        # Should be reverse order (most recent first)
        assert events[0].message == "Event 4"
        assert events[4].message == "Event 0"

    @pytest.mark.asyncio
    async def test_get_events_filter_by_module(self, tracker):
        """Test filtering events by module."""
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="API event",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Codegen event",
        ))

        api_events = await tracker.get_events(module="api")
        codegen_events = await tracker.get_events(module="codegen")

        assert len(api_events) == 1
        assert api_events[0].module == "api"
        assert len(codegen_events) == 1
        assert codegen_events[0].module == "codegen"

    @pytest.mark.asyncio
    async def test_get_events_filter_by_level(self, tracker):
        """Test filtering events by level."""
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Error",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Info",
        ))

        errors = await tracker.get_events(level=FrameworkEventLevel.ERROR)
        infos = await tracker.get_events(level=FrameworkEventLevel.INFO)

        assert len(errors) == 1
        assert errors[0].level == FrameworkEventLevel.ERROR
        assert len(infos) == 1
        assert infos[0].level == FrameworkEventLevel.INFO

    @pytest.mark.asyncio
    async def test_get_errors(self, tracker):
        """Test getting only error events."""
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Error 1",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Info",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Error 2",
        ))

        errors = await tracker.get_errors()

        assert len(errors) == 2
        assert all(e.level == FrameworkEventLevel.ERROR for e in errors)

    @pytest.mark.asyncio
    async def test_get_slow_operations(self, tracker):
        """Test getting slow operations."""
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_SLOW,
            module="api",
            message="Slow",
            duration_ms=2000,
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Fast",
            duration_ms=100,
        ))

        slow = await tracker.get_slow_operations(min_duration_ms=1000)

        assert len(slow) == 1
        assert slow[0].duration_ms == 2000

    @pytest.mark.asyncio
    async def test_clear(self, tracker):
        """Test clearing tracker."""
        for i in range(5):
            await tracker.capture(FrameworkEvent(
                level=FrameworkEventLevel.INFO,
                event_type=FrameworkEventType.API_REQUEST_ERROR,
                module="api",
                message=f"Event {i}",
            ))

        assert len(tracker) == 5

        await tracker.clear()

        assert len(tracker) == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, tracker):
        """Test getting statistics."""
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Error",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Error",
        ))
        await tracker.capture(FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Info",
        ))

        stats = await tracker.get_stats()

        assert stats["total_events"] == 3
        assert stats["by_level"]["error"] == 2
        assert stats["by_level"]["info"] == 1
        assert stats["by_module"]["api"] == 2
        assert stats["by_module"]["codegen"] == 1
        assert stats["by_type"]["api_request_error"] == 2
        assert stats["by_type"]["codegen_error"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, tracker):
        """Test stats on empty tracker."""
        stats = await tracker.get_stats()

        assert stats["total_events"] == 0
        assert stats["by_level"] == {}
        assert stats["by_module"] == {}
        assert stats["by_type"] == {}


class TestCaptureEventFunction:
    """Test the capture_event helper function."""

    @pytest.mark.asyncio
    async def test_capture_event_function(self):
        """Test capturing event via helper function."""
        event = await capture_event(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Generation failed",
            duration_ms=5000,
            error_details={"error": "Invalid template"},
            metadata={"files": 5},
        )

        assert event.level == FrameworkEventLevel.ERROR
        assert event.event_type == FrameworkEventType.CODEGEN_ERROR
        assert event.module == "codegen"
        assert event.message == "Generation failed"
        assert event.duration_ms == 5000
        assert event.error_details == {"error": "Invalid template"}
        assert event.metadata == {"files": 5}

        # Check it was captured
        tracker = get_tracker()
        events = await tracker.get_events()
        assert len(events) > 0


class TestCaptureExceptionFunction:
    """Test the capture_exception helper function."""

    @pytest.mark.asyncio
    async def test_capture_exception(self):
        """Test capturing exception as event."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            event = await capture_exception(
                e,
                module="test",
                message="Custom message",
                metadata={"context": "test"},
            )

        assert event.level == FrameworkEventLevel.ERROR
        assert event.module == "test"
        assert event.message == "Custom message"
        assert event.error_details["exception_type"] == "ValueError"
        assert "traceback" in event.error_details
        assert event.metadata == {"context": "test"}

    @pytest.mark.asyncio
    async def test_capture_exception_default_message(self):
        """Test capturing exception with default message."""
        try:
            raise RuntimeError("Something went wrong")
        except RuntimeError as e:
            event = await capture_exception(e, module="test")

        assert event.message == "Something went wrong"


class TestGetTracker:
    """Test the global tracker."""

    def test_get_tracker_singleton(self):
        """Test that get_tracker returns same instance."""
        tracker1 = get_tracker()
        tracker2 = get_tracker()

        assert tracker1 is tracker2
