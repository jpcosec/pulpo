"""
Framework Self-Awareness Module

Provides observability for the framework itself:
- Error tracking across all layers
- Performance metrics
- Framework health monitoring
- Event logging and analysis

This is NOT for application-level observability (use TaskRun for that).
This is for framework infrastructure monitoring.
"""

from .events import (
    FrameworkEvent,
    FrameworkEventLevel,
    FrameworkEventType,
)
from .tracking import (
    EventTracker,
    capture_event,
    get_tracker,
)

__all__ = [
    "FrameworkEventLevel",
    "FrameworkEvent",
    "FrameworkEventType",
    "EventTracker",
    "get_tracker",
    "capture_event",
]
