"""
Framework event models and types.

Defines what framework events look like and how they're structured.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FrameworkEventLevel(str, Enum):
    """Event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class FrameworkEventType(str, Enum):
    """Types of framework events."""

    # API events
    API_REQUEST_ERROR = "api_request_error"
    API_REQUEST_SLOW = "api_request_slow"
    API_VALIDATION_ERROR = "api_validation_error"

    # Code generation events
    CODEGEN_START = "codegen_start"
    CODEGEN_COMPLETE = "codegen_complete"
    CODEGEN_ERROR = "codegen_error"
    CODEGEN_SLOW = "codegen_slow"

    # Database events
    DB_QUERY_ERROR = "db_query_error"
    DB_QUERY_SLOW = "db_query_slow"
    DB_CONNECTION_ERROR = "db_connection_error"

    # Decorator events
    DECORATOR_REGISTRATION_ERROR = "decorator_registration_error"
    DECORATOR_REGISTRATION_SUCCESS = "decorator_registration_success"
    DECORATOR_VALIDATION_ERROR = "decorator_validation_error"

    # CLI events
    CLI_COMMAND_ERROR = "cli_command_error"
    CLI_COMMAND_COMPLETE = "cli_command_complete"

    # Framework initialization
    FRAMEWORK_INIT_ERROR = "framework_init_error"
    FRAMEWORK_INIT_COMPLETE = "framework_init_complete"

    # Registry events
    REGISTRY_ERROR = "registry_error"
    REGISTRY_LOOKUP = "registry_lookup"


@dataclass
class FrameworkEvent:
    """
    A framework observability event.

    Represents something that happened in the framework infrastructure.
    Can be an error, performance metric, or informational event.
    """

    # Required fields
    level: FrameworkEventLevel
    event_type: FrameworkEventType
    module: str  # "api", "codegen", "database", "decorator", "cli"
    message: str

    # Optional fields
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: int | None = None  # For performance events
    error_details: dict[str, Any] = field(default_factory=dict)  # Stack trace, exception
    metadata: dict[str, Any] = field(default_factory=dict)  # Context-specific data

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage/serialization."""
        return {
            "level": self.level.value,
            "event_type": self.event_type.value,
            "module": self.module,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error_details": self.error_details,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrameworkEvent":
        """Create event from dictionary."""
        return cls(
            level=FrameworkEventLevel(data["level"]),
            event_type=FrameworkEventType(data["event_type"]),
            module=data["module"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            duration_ms=data.get("duration_ms"),
            error_details=data.get("error_details", {}),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FrameworkEvent("
            f"level={self.level.value}, "
            f"type={self.event_type.value}, "
            f"module={self.module}, "
            f"message={self.message!r}"
            f")"
        )
