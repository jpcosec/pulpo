# Framework Self-Awareness

**Version:** 0.6.0
**Status:** Framework Core Feature
**Location:** `core/core/selfawareness/`

## Overview

The **self-awareness module** provides built-in observability for the framework infrastructure itself. It tracks errors, performance metrics, and events across all framework layers.

**This is NOT application observability** - use `TaskRun` for that. Self-awareness tracks the framework's own health and behavior.

## What It Tracks

### By Layer

| Layer | Events | Examples |
|-------|--------|----------|
| **API** | Requests, errors, performance | 404/500 errors, slow endpoints |
| **Database** | Query performance, connection issues | Slow queries (>1s), connection errors |
| **Code Generation** | Generation success/failure, performance | Failed codegen, slow template rendering |
| **Decorators** | Registration errors, validation issues | Invalid model definitions |
| **CLI** | Command execution, errors | Command failures, parsing errors |

### Event Types

```python
from core.selfawareness.events import FrameworkEventType

# API
FrameworkEventType.API_REQUEST_ERROR       # 4xx, 5xx responses
FrameworkEventType.API_REQUEST_SLOW        # Requests > threshold
FrameworkEventType.API_VALIDATION_ERROR    # Request validation failed

# Code Generation
FrameworkEventType.CODEGEN_START           # Generation started
FrameworkEventType.CODEGEN_COMPLETE        # Generation successful
FrameworkEventType.CODEGEN_ERROR           # Generation failed
FrameworkEventType.CODEGEN_SLOW            # Generation took too long

# Database
FrameworkEventType.DB_QUERY_ERROR          # Query failed
FrameworkEventType.DB_QUERY_SLOW           # Query > threshold
FrameworkEventType.DB_CONNECTION_ERROR     # Connection failed

# And more...
```

## Core Components

### 1. Events (`core.selfawareness.events`)

**FrameworkEvent** dataclass represents any framework event:

```python
from core.selfawareness.events import FrameworkEvent, FrameworkEventLevel, FrameworkEventType
from datetime import datetime

event = FrameworkEvent(
    level=FrameworkEventLevel.ERROR,
    event_type=FrameworkEventType.CODEGEN_ERROR,
    module="codegen",
    message="Template rendering failed",
    duration_ms=5000,
    error_details={"error": "Invalid Jinja2 syntax"},
    metadata={"files": 5, "template": "model_crud.j2"},
    timestamp=datetime.utcnow(),
)

# Convert to/from dict
data = event.to_dict()
restored = FrameworkEvent.from_dict(data)
```

### 2. Tracking (`core.selfawareness.tracking`)

**EventTracker** stores events in memory:

```python
from core.selfawareness.tracking import get_tracker, capture_event
from core.selfawareness.events import FrameworkEventLevel, FrameworkEventType

# Get global tracker
tracker = get_tracker()

# Capture events
event = await capture_event(
    level=FrameworkEventLevel.WARN,
    event_type=FrameworkEventType.DB_QUERY_SLOW,
    module="database",
    message="Slow query detected",
    duration_ms=2500,
    metadata={"collection": "users", "operation": "find"}
)

# Query events
errors = await tracker.get_errors(limit=10)
slow_ops = await tracker.get_slow_operations(min_duration_ms=1000, limit=20)

# Get statistics
stats = await tracker.get_stats()
# {
#   "total_events": 42,
#   "by_level": {"error": 5, "warn": 10, "info": 27},
#   "by_module": {"api": 15, "database": 12, ...},
#   "by_type": {"db_query_slow": 8, ...}
# }
```

### 3. Middleware (`core.selfawareness.middleware`)

**SelfAwarenessMiddleware** automatically tracks FastAPI requests:

```python
from fastapi import FastAPI
from core.selfawareness.middleware import add_selfawareness_middleware

app = FastAPI()

# Add middleware to track requests
add_selfawareness_middleware(
    app,
    slow_request_ms=1000  # Warn on requests > 1 second
)

# Middleware automatically captures:
# - 4xx errors (level=WARN)
# - 5xx errors (level=ERROR)
# - Slow requests (level=WARN, if > slow_request_ms)
# - Request metadata (path, method, status)
# - Exception details (if request throws)
```

## Usage Examples

### Capture Application Errors

```python
from core.selfawareness.tracking import capture_exception

try:
    # ... your code ...
    pass
except Exception as e:
    await capture_exception(
        e,
        module="my_service",
        message="Failed to process data",
        metadata={"user_id": "123", "action": "import"}
    )
```

### Track Code Generation Performance

```python
import time
from core.selfawareness.tracking import capture_event
from core.selfawareness.events import FrameworkEventLevel, FrameworkEventType

async def generate_api():
    start = time.time()

    try:
        # ... generation logic ...
        duration_ms = (time.time() - start) * 1000

        await capture_event(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.CODEGEN_COMPLETE,
            module="codegen",
            message="API generation successful",
            duration_ms=int(duration_ms),
            metadata={"routes": 25, "models": 8}
        )
    except Exception as e:
        await capture_exception(
            e,
            module="codegen",
            message="API generation failed"
        )
```

### Monitor Database Performance

```python
from core.selfawareness.tracking import capture_event
from core.selfawareness.events import FrameworkEventLevel, FrameworkEventType
import time

async def find_users(query):
    start = time.time()

    try:
        results = await User.find(query).to_list()
        duration_ms = (time.time() - start) * 1000

        # Log slow queries
        if duration_ms > 500:
            await capture_event(
                level=FrameworkEventLevel.WARN,
                event_type=FrameworkEventType.DB_QUERY_SLOW,
                module="database",
                message=f"Slow query in find_users: {duration_ms:.0f}ms",
                duration_ms=int(duration_ms),
                metadata={"collection": "users", "query_fields": list(query.keys())}
            )

        return results
    except Exception as e:
        await capture_exception(e, module="database")
        raise
```

### Query Event History

```python
from core.selfawareness.tracking import get_tracker
from core.selfawareness.events import FrameworkEventLevel, FrameworkEventType

tracker = get_tracker()

# Get all errors from last hour
errors = await tracker.get_errors(limit=100)
for error in errors:
    print(f"[{error.timestamp}] {error.module}: {error.message}")

# Get slow database operations
slow_db_ops = await tracker.get_slow_operations(min_duration_ms=1000)
for op in slow_db_ops:
    print(f"{op.metadata.get('collection')}: {op.duration_ms}ms")

# Get statistics
stats = await tracker.get_stats()
print(f"Total events: {stats['total_events']}")
print(f"Errors: {stats['by_level'].get('error', 0)}")
print(f"Warnings: {stats['by_level'].get('warn', 0)}")
```

## Event Levels

```python
from core.selfawareness.events import FrameworkEventLevel

FrameworkEventLevel.DEBUG      # Development information
FrameworkEventLevel.INFO       # Informational messages
FrameworkEventLevel.WARN       # Warnings (non-critical issues)
FrameworkEventLevel.ERROR      # Errors (something failed)
FrameworkEventLevel.CRITICAL   # Critical system failures
```

## Storage

### In-Memory Storage (Default)

Events are stored in memory with configurable maximum:

```python
from core.selfawareness.tracking import EventTracker

# Create tracker with 5000 event limit (default 10000)
tracker = EventTracker(max_events=5000)

# Oldest events are dropped when limit exceeded
await tracker.capture(event)

# Clear all events
await tracker.clear()
```

### Future: External Storage

The tracking system is extensible. You can implement external storage:

```python
# Example: Send to your swisskey system
class SwissKeyEventTracker(EventTracker):
    async def capture(self, event: FrameworkEvent):
        await super().capture(event)  # Store locally

        # Also send to swisskey
        await swisskey_client.send_event(event.to_dict())
```

## Integration Points

### 1. With FastAPI Apps

```python
from fastapi import FastAPI
from core.selfawareness.middleware import add_selfawareness_middleware

app = FastAPI()

# Enable self-awareness tracking for this app
add_selfawareness_middleware(app, slow_request_ms=2000)

@app.get("/api/users")
async def get_users():
    # All requests to this endpoint are automatically tracked
    return {"users": [...]}
```

### 2. With Operations

```python
from core.decorators import operation
from core.selfawareness.tracking import capture_event
from core.selfawareness.events import FrameworkEventLevel, FrameworkEventType

@operation(name="import_data")
async def import_data(input: ImportInput) -> ImportOutput:
    start = time.time()

    try:
        result = await do_import(input)
        duration = (time.time() - start) * 1000

        await capture_event(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.CLI_COMMAND_COMPLETE,  # or API_REQUEST_SUCCESS
            module="operations",
            message="Data import completed",
            duration_ms=int(duration),
            metadata={"records": result.count}
        )

        return result
    except Exception as e:
        await capture_exception(e, module="operations")
        raise
```

### 3. With Codegen

```python
# In core/codegen.py
from core.selfawareness.tracking import capture_event, capture_exception

async def compile_all():
    start = time.time()

    try:
        # ... codegen logic ...

        duration_ms = (time.time() - start) * 1000
        await capture_event(
            level=FrameworkEventLevel.INFO,
            event_type=FrameworkEventType.CODEGEN_COMPLETE,
            module="codegen",
            message="Code generation complete",
            duration_ms=int(duration_ms)
        )
    except Exception as e:
        await capture_exception(e, module="codegen")
        raise
```

## Performance Considerations

### Memory Usage

- Default: 10,000 events max (~50MB with typical event size)
- Events are stored in memory only
- Configure via `EventTracker(max_events=N)`

### Async Safety

- All operations are async and thread-safe
- Uses `asyncio.Lock` internally
- Safe to call from multiple coroutines simultaneously

### Logging Integration

- Events are logged via Python `logging` module
- Configure logging level to suppress verbose events:

```python
import logging

# Suppress DEBUG level framework events
logging.getLogger("core.selfawareness").setLevel(logging.INFO)
```

## Testing

All self-awareness components are comprehensively tested:

```bash
poetry run pytest tests/unit/test_selfawareness_*.py -v
```

**Test coverage:**
- ✅ Event creation and serialization (10 tests)
- ✅ Event tracking and queries (21 tests)
- ✅ Middleware integration (7 tests)
- **Total: 38 tests, 100% pass rate**

## Architecture

```
┌─────────────────────────────────────────┐
│  Framework Layers                       │
│  ├── API (FastAPI)                      │
│  ├── Codegen                            │
│  ├── Database                           │
│  └── Decorators                         │
└────────────────┬────────────────────────┘
                 │ emit events
┌────────────────▼────────────────────────┐
│  SelfAwareness Module                   │
│  ├── FrameworkEvent (dataclass)         │
│  ├── EventTracker (in-memory storage)   │
│  └── SelfAwarenessMiddleware (FastAPI)  │
└────────────────┬────────────────────────┘
                 │ store & query
┌────────────────▼────────────────────────┐
│  Event Storage                          │
│  ├── In-memory (default)                │
│  ├── External: swisskey (future)        │
│  └── External: Database (future)        │
└─────────────────────────────────────────┘
```

## Key Design Decisions

1. **Separate from TaskRun**: TaskRun is for operation audit trail. Self-awareness is for framework infrastructure monitoring.

2. **In-Memory First**: Simplest implementation, no external dependencies. Can be extended for external storage.

3. **Middleware-Based API Tracking**: Automatically captures all FastAPI requests without code changes.

4. **Async-First**: Aligns with framework's async architecture. Non-blocking event capture.

5. **No Database Dependency**: Events don't require MongoDB. Can work standalone.

6. **Optional Integration**: Can be enabled/disabled per component. Framework works fine without it.

## Future Enhancements

- [ ] Persist events to MongoDB collection
- [ ] Dashboard/query API endpoint
- [ ] Integration with external services (Sentry, DataDog)
- [ ] Real-time event streaming via WebSocket
- [ ] Custom event types and filters
- [ ] Event aggregation and analytics

## Summary

The self-awareness module provides **zero-configuration framework observability**:

✅ **Automatic request tracking** via middleware
✅ **Exception capture** with full context
✅ **Performance metrics** with duration tracking
✅ **Event querying** with filtering
✅ **Statistics generation** across layers
✅ **Extensible design** for external storage
✅ **Fully tested** (38 tests)
✅ **Async-safe** and production-ready

---

**Next Steps:**
- [Use in your generated API](./ARCHITECTURE_OVERVIEW.md)
- [Integrate with custom middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Query event history programmatically](./selfawareness_examples.py)
