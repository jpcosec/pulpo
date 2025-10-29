"""
Event tracking and capture functionality.

Handles tracking framework events and storing them.
"""

import asyncio
import logging
import traceback
from typing import Any

from .events import FrameworkEvent, FrameworkEventLevel, FrameworkEventType

logger = logging.getLogger(__name__)


class EventTracker:
    """
    Tracks framework events.

    Stores events in memory with a configurable max size.
    Can be extended to send events to external systems.
    """

    def __init__(self, max_events: int = 10000):
        """
        Initialize event tracker.

        Args:
            max_events: Maximum events to store in memory. Oldest dropped when exceeded.
        """
        self.max_events = max_events
        self.events: list[FrameworkEvent] = []
        self._lock = asyncio.Lock()

    async def capture(self, event: FrameworkEvent) -> None:
        """
        Capture and store an event.

        Args:
            event: The framework event to capture
        """
        async with self._lock:
            self.events.append(event)

            # Keep only recent events
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events :]

            # Log the event
            logger.log(
                level=_get_log_level(event.level),
                msg=f"[{event.module}] {event.message}",
                extra={"event_type": event.event_type.value},
            )

    async def get_events(
        self,
        module: str | None = None,
        level: FrameworkEventLevel | None = None,
        event_type: FrameworkEventType | None = None,
        limit: int = 100,
    ) -> list[FrameworkEvent]:
        """
        Retrieve events with optional filtering.

        Args:
            module: Filter by module name
            level: Filter by event level
            event_type: Filter by event type
            limit: Maximum events to return

        Returns:
            List of matching events (most recent first)
        """
        async with self._lock:
            results = self.events

            if module:
                results = [e for e in results if e.module == module]

            if level:
                results = [e for e in results if e.level == level]

            if event_type:
                results = [e for e in results if e.event_type == event_type]

            # Return most recent first
            return list(reversed(results))[-limit:]

    async def get_errors(self, limit: int = 100) -> list[FrameworkEvent]:
        """Get recent errors."""
        return await self.get_events(level=FrameworkEventLevel.ERROR, limit=limit)

    async def get_warnings(self, limit: int = 100) -> list[FrameworkEvent]:
        """Get recent warnings."""
        return await self.get_events(level=FrameworkEventLevel.WARN, limit=limit)

    async def get_slow_operations(
        self, min_duration_ms: int = 1000, limit: int = 100
    ) -> list[FrameworkEvent]:
        """Get operations that took longer than threshold."""
        async with self._lock:
            results = [e for e in self.events if e.duration_ms and e.duration_ms > min_duration_ms]
            return list(reversed(results))[-limit:]

    async def clear(self) -> None:
        """Clear all stored events."""
        async with self._lock:
            self.events.clear()

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about tracked events."""
        async with self._lock:
            if not self.events:
                return {
                    "total_events": 0,
                    "by_level": {},
                    "by_module": {},
                    "by_type": {},
                }

            stats = {
                "total_events": len(self.events),
                "by_level": {},
                "by_module": {},
                "by_type": {},
            }

            for event in self.events:
                # By level
                level_key = event.level.value
                stats["by_level"][level_key] = stats["by_level"].get(level_key, 0) + 1

                # By module
                stats["by_module"][event.module] = stats["by_module"].get(event.module, 0) + 1

                # By type
                type_key = event.event_type.value
                stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1

            return stats

    def __len__(self) -> int:
        """Return number of tracked events."""
        return len(self.events)


# Global tracker instance
_tracker: EventTracker | None = None


def get_tracker() -> EventTracker:
    """Get or create the global event tracker."""
    global _tracker
    if _tracker is None:
        _tracker = EventTracker()
    return _tracker


async def capture_event(
    level: FrameworkEventLevel,
    event_type: FrameworkEventType,
    module: str,
    message: str,
    duration_ms: int | None = None,
    error_details: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> FrameworkEvent:
    """
    Capture a framework event.

    Convenience function to create and capture an event in one call.

    Args:
        level: Event severity level
        event_type: Type of event
        module: Module/component where event occurred
        message: Human-readable message
        duration_ms: Duration if this is a performance event
        error_details: Error-specific details (stack trace, etc.)
        metadata: Additional context

    Returns:
        The captured event
    """
    event = FrameworkEvent(
        level=level,
        event_type=event_type,
        module=module,
        message=message,
        duration_ms=duration_ms,
        error_details=error_details or {},
        metadata=metadata or {},
    )

    tracker = get_tracker()
    await tracker.capture(event)
    return event


async def capture_exception(
    exception: Exception,
    module: str,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> FrameworkEvent:
    """
    Capture an exception as a framework event.

    Args:
        exception: The exception that occurred
        module: Module where exception occurred
        message: Optional custom message (defaults to exception message)
        metadata: Additional context

    Returns:
        The captured event
    """
    return await capture_event(
        level=FrameworkEventLevel.ERROR,
        event_type=FrameworkEventType.FRAMEWORK_INIT_ERROR,  # Generic error type
        module=module,
        message=message or str(exception),
        error_details={
            "exception_type": exception.__class__.__name__,
            "traceback": traceback.format_exc(),
        },
        metadata=metadata or {},
    )


def _get_log_level(event_level: FrameworkEventLevel) -> int:
    """Convert FrameworkEventLevel to logging level."""
    mapping = {
        FrameworkEventLevel.DEBUG: logging.DEBUG,
        FrameworkEventLevel.INFO: logging.INFO,
        FrameworkEventLevel.WARN: logging.WARNING,
        FrameworkEventLevel.ERROR: logging.ERROR,
        FrameworkEventLevel.CRITICAL: logging.CRITICAL,
    }
    return mapping.get(event_level, logging.INFO)
