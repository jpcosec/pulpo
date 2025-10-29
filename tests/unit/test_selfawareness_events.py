"""
Tests for selfawareness event models.
"""

from datetime import datetime

from core.selfawareness.events import (
    FrameworkEvent,
    FrameworkEventLevel,
    FrameworkEventType,
)


class TestFrameworkEventLevel:
    """Test FrameworkEventLevel enum."""

    def test_all_levels_exist(self):
        """Test that all expected levels exist."""
        assert FrameworkEventLevel.DEBUG
        assert FrameworkEventLevel.INFO
        assert FrameworkEventLevel.WARN
        assert FrameworkEventLevel.ERROR
        assert FrameworkEventLevel.CRITICAL

    def test_level_string_values(self):
        """Test string values of levels."""
        assert FrameworkEventLevel.DEBUG.value == "debug"
        assert FrameworkEventLevel.INFO.value == "info"
        assert FrameworkEventLevel.WARN.value == "warn"
        assert FrameworkEventLevel.ERROR.value == "error"
        assert FrameworkEventLevel.CRITICAL.value == "critical"


class TestFrameworkEventType:
    """Test FrameworkEventType enum."""

    def test_api_events_exist(self):
        """Test API event types."""
        assert FrameworkEventType.API_REQUEST_ERROR
        assert FrameworkEventType.API_REQUEST_SLOW
        assert FrameworkEventType.API_VALIDATION_ERROR

    def test_codegen_events_exist(self):
        """Test codegen event types."""
        assert FrameworkEventType.CODEGEN_START
        assert FrameworkEventType.CODEGEN_COMPLETE
        assert FrameworkEventType.CODEGEN_ERROR
        assert FrameworkEventType.CODEGEN_SLOW

    def test_database_events_exist(self):
        """Test database event types."""
        assert FrameworkEventType.DB_QUERY_ERROR
        assert FrameworkEventType.DB_QUERY_SLOW
        assert FrameworkEventType.DB_CONNECTION_ERROR

    def test_decorator_events_exist(self):
        """Test decorator event types."""
        assert FrameworkEventType.DECORATOR_REGISTRATION_ERROR
        assert FrameworkEventType.DECORATOR_REGISTRATION_SUCCESS
        assert FrameworkEventType.DECORATOR_VALIDATION_ERROR

    def test_cli_events_exist(self):
        """Test CLI event types."""
        assert FrameworkEventType.CLI_COMMAND_ERROR
        assert FrameworkEventType.CLI_COMMAND_COMPLETE

    def test_initialization_events_exist(self):
        """Test initialization event types."""
        assert FrameworkEventType.FRAMEWORK_INIT_ERROR
        assert FrameworkEventType.FRAMEWORK_INIT_COMPLETE

    def test_registry_events_exist(self):
        """Test registry event types."""
        assert FrameworkEventType.REGISTRY_ERROR
        assert FrameworkEventType.REGISTRY_LOOKUP


class TestFrameworkEvent:
    """Test FrameworkEvent model."""

    def test_create_minimal_event(self):
        """Test creating event with minimal fields."""
        event = FrameworkEvent(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Test message",
        )

        assert event.level == FrameworkEventLevel.INFO
        assert event.event_type == FrameworkEventType.API_REQUEST_ERROR
        assert event.module == "api"
        assert event.message == "Test message"
        assert event.duration_ms is None
        assert event.error_details == {}
        assert event.metadata == {}
        assert isinstance(event.timestamp, datetime)

    def test_create_full_event(self):
        """Test creating event with all fields."""
        timestamp = datetime.utcnow()
        error_details = {"exception_type": "ValueError", "traceback": "..."}
        metadata = {"path": "/api/test", "method": "GET"}

        event = FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.API_REQUEST_ERROR,
            module="api",
            message="Request failed",
            timestamp=timestamp,
            duration_ms=5000,
            error_details=error_details,
            metadata=metadata,
        )

        assert event.level == FrameworkEventLevel.ERROR
        assert event.event_type == FrameworkEventType.API_REQUEST_ERROR
        assert event.module == "api"
        assert event.message == "Request failed"
        assert event.timestamp == timestamp
        assert event.duration_ms == 5000
        assert event.error_details == error_details
        assert event.metadata == metadata

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Generation failed",
            duration_ms=1500,
            error_details={"error": "Invalid template"},
            metadata={"files": 5},
        )

        data = event.to_dict()

        assert data["level"] == "error"
        assert data["event_type"] == "codegen_error"
        assert data["module"] == "codegen"
        assert data["message"] == "Generation failed"
        assert data["duration_ms"] == 1500
        assert data["error_details"] == {"error": "Invalid template"}
        assert data["metadata"] == {"files": 5}
        assert "timestamp" in data

    def test_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            "level": "error",
            "event_type": "db_query_error",
            "module": "database",
            "message": "Query failed",
            "duration_ms": 2000,
            "error_details": {"db_error": "Connection timeout"},
            "metadata": {"collection": "users"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        event = FrameworkEvent.from_dict(data)

        assert event.level == FrameworkEventLevel.ERROR
        assert event.event_type == FrameworkEventType.DB_QUERY_ERROR
        assert event.module == "database"
        assert event.message == "Query failed"
        assert event.duration_ms == 2000
        assert event.error_details == {"db_error": "Connection timeout"}
        assert event.metadata == {"collection": "users"}

    def test_roundtrip_serialization(self):
        """Test that event survives to_dict/from_dict roundtrip."""
        original = FrameworkEvent(
            level=FrameworkEventLevel.WARN,
            event_type=FrameworkEventType.API_REQUEST_SLOW,
            module="api",
            message="Slow endpoint",
            duration_ms=3000,
            error_details={"threshold": 1000},
            metadata={"path": "/api/users"},
        )

        data = original.to_dict()
        restored = FrameworkEvent.from_dict(data)

        assert restored.level == original.level
        assert restored.event_type == original.event_type
        assert restored.module == original.module
        assert restored.message == original.message
        assert restored.duration_ms == original.duration_ms
        assert restored.error_details == original.error_details
        assert restored.metadata == original.metadata

    def test_repr(self):
        """Test string representation."""
        event = FrameworkEvent(
            level=FrameworkEventLevel.ERROR,
            event_type=FrameworkEventType.CODEGEN_ERROR,
            module="codegen",
            message="Generation failed",
        )

        repr_str = repr(event)

        assert "FrameworkEvent" in repr_str
        assert "error" in repr_str
        assert "codegen_error" in repr_str
        assert "codegen" in repr_str
        assert "Generation failed" in repr_str
