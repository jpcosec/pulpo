# Complete Code Architecture - All Layers

This document shows **all layers** of the Pulpo framework, including the infrastructure layers that weren't in the initial architecture graph.

## Complete System Overview

```mermaid
graph TB
    subgraph "USER CODE"
        UM[models/*.py<br/>@datamodel]
        UO[operations/*.py<br/>@operation]
    end

    subgraph "INFRASTRUCTURE"
        BASE[base.py<br/>Base classes]
        UTILS[utils/<br/>exceptions, logging, validators]
        SELF[selfawareness/<br/>observability]
    end

    subgraph "PHASE 1: ANALYSIS"
        D[Discovery]
        R[Registries]
        V[Validation]
        G[Graphs]
    end

    subgraph "PHASE 2: GENERATION"
        I[Init]
        C[Compile]
    end

    subgraph "CLI LAYER"
        FCLI[Framework CLI<br/>main.py + interface.py]
        PCLI[Project CLI<br/>Generated ./main]
    end

    subgraph "GENERATED CODE"
        API[generated_api.py<br/>+ selfawareness middleware]
        UI[generated_frontend/]
        WF[prefect_flows.py]
    end

    UM --> D
    UO --> D
    D --> R
    R --> V
    R --> G
    R --> I
    R --> C

    BASE -.optional.-> UM
    BASE -.optional.-> UO
    UTILS --> D
    UTILS --> R
    UTILS --> V
    UTILS --> G
    UTILS --> I
    UTILS --> C

    I --> PCLI
    C --> API
    C --> UI
    C --> WF

    FCLI --> I
    FCLI --> C
    FCLI --> D
    FCLI --> R

    SELF --> API
```

---

## Infrastructure Layer Details

### 1. Base Classes (core/base.py - 41 lines)

```python
class DataModelBase:
    """Optional mixin for Beanie documents."""
    searchable_fields: list[str] = []
    sortable_fields: list[str] = []

    @classmethod
    def relations(cls) -> list[dict]:
        """Return relation hints."""
        return []

    @classmethod
    def indexes(cls) -> list[dict]:
        """Return index definitions."""
        return []

class OperationBase(ABC):
    """Base class for operations."""

    @abstractmethod
    async def run(self, input_model: Any) -> Any:
        """Execute the operation."""
```

**Purpose**: Optional base classes that user models/operations can inherit from.

**Usage**:
```python
# User code (optional)
from core.base import DataModelBase

@datamodel(name="User")
class User(Document, DataModelBase):
    name: str

    @classmethod
    def relations(cls):
        return [{"name": "posts", "target": "Post", "cardinality": "many"}]
```

---

### 2. Observability Layer (core/selfawareness/ - 461 lines)

#### Architecture

```mermaid
graph TD
    subgraph "core/selfawareness/"
        E[events.py<br/>118 lines]
        T[tracking.py<br/>243 lines]
        M[middleware.py<br/>140 lines]
    end

    subgraph "Event Types"
        ET[FrameworkEventType<br/>API_REQUEST_ERROR<br/>CODEGEN_SLOW<br/>DB_QUERY_ERROR<br/>etc.]
    end

    subgraph "Tracking"
        TRK[EventTracker<br/>10,000 events in memory<br/>Filtering, stats]
    end

    subgraph "Middleware"
        MW[SelfAwarenessMiddleware<br/>Auto-track API requests<br/>Error detection<br/>Performance monitoring]
    end

    E --> ET
    T --> TRK
    M --> MW
    ET --> TRK
    TRK --> MW
```

#### Events (events.py - 118 lines)

**Event Levels**:
- DEBUG, INFO, WARN, ERROR, CRITICAL

**Event Types** (17 types):
- API: `API_REQUEST_ERROR`, `API_REQUEST_SLOW`, `API_VALIDATION_ERROR`
- Codegen: `CODEGEN_START`, `CODEGEN_COMPLETE`, `CODEGEN_ERROR`, `CODEGEN_SLOW`
- Database: `DB_QUERY_ERROR`, `DB_QUERY_SLOW`, `DB_CONNECTION_ERROR`
- Decorator: `DECORATOR_REGISTRATION_ERROR`, `DECORATOR_VALIDATION_ERROR`
- CLI: `CLI_COMMAND_ERROR`, `CLI_COMMAND_COMPLETE`
- Framework: `FRAMEWORK_INIT_ERROR`, `FRAMEWORK_INIT_COMPLETE`
- Registry: `REGISTRY_ERROR`, `REGISTRY_LOOKUP`

**FrameworkEvent class**:
```python
@dataclass
class FrameworkEvent:
    level: FrameworkEventLevel
    event_type: FrameworkEventType
    module: str  # "api", "codegen", "database", etc.
    message: str
    timestamp: datetime
    duration_ms: int | None = None
    error_details: dict[str, Any]
    metadata: dict[str, Any]
```

#### Tracking (tracking.py - 243 lines)

**EventTracker class**:
- Stores up to 10,000 events in memory (oldest dropped)
- Async operations with lock for thread safety
- Filtering: by module, level, event type
- Queries: `get_errors()`, `get_warnings()`, `get_slow_operations()`
- Statistics: event counts by level/module/type

**Usage**:
```python
from core.selfawareness.tracking import capture_event, get_tracker

# Capture event
await capture_event(
    level=FrameworkEventLevel.WARN,
    event_type=FrameworkEventType.CODEGEN_SLOW,
    module="codegen",
    message="API generation took 2.5s",
    duration_ms=2500
)

# Query events
tracker = get_tracker()
errors = await tracker.get_errors(limit=50)
stats = await tracker.get_stats()
```

#### Middleware (middleware.py - 140 lines)

**SelfAwarenessMiddleware**:
- Automatically tracks all API requests
- Detects errors (4xx, 5xx status codes)
- Detects slow requests (configurable threshold, default 1000ms)
- Captures exceptions

**Usage**:
```python
from core.selfawareness.middleware import add_selfawareness_middleware

app = FastAPI()
add_selfawareness_middleware(app, slow_request_ms=1000)
```

**What it tracks**:
- Request path, method, status code
- Duration in milliseconds
- Errors with exception details
- Slow requests above threshold

---

### 3. Utils Layer (core/utils/ - ~1,400 lines)

#### Architecture

```mermaid
graph TD
    subgraph "core/utils/"
        EX[exceptions.py<br/>530 lines]
        LOG[logging.py<br/>Logging utilities]
        LOGC[logging_config.py<br/>Configuration]
        VAL[validators.py<br/>Field validators]
    end

    subgraph "Exception Hierarchy"
        BASE_EX[PulpoException]
        CAT1[ExternalServiceError]
        CAT2[InternalError]
        CAT3[UserInputError]
        CAT4[OperationalError]
    end

    subgraph "Specific Exceptions"
        EX1[ScrapingError<br/>TimeoutError<br/>RateLimitError<br/>AuthenticationError]
        EX2[DatabaseError<br/>ProcessingError]
        EX3[ValidationError<br/>ConfigurationError]
        EX4[ApplicationError]
    end

    EX --> BASE_EX
    BASE_EX --> CAT1
    BASE_EX --> CAT2
    BASE_EX --> CAT3
    BASE_EX --> CAT4

    CAT1 --> EX1
    CAT2 --> EX2
    CAT3 --> EX3
    CAT4 --> EX4
```

#### Exceptions (exceptions.py - 530 lines)

**Base Exception**:
```python
class PulpoException(Exception, ABC):
    """Base exception for all Pulpo errors."""
    category: str = "general"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}

    def with_detail(self, key: str, value: Any) -> "PulpoException":
        """Add detail (chainable)."""
        self.details[key] = value
        return self
```

**Exception Categories** (4 abstract bases):
1. **ExternalServiceError**: Scraping, API, network errors
2. **InternalError**: Database, processing errors
3. **UserInputError**: Validation, configuration errors
4. **OperationalError**: Application submission errors

**Specific Exceptions** (9 concrete):
- `ScrapingError`, `TimeoutError`, `RateLimitError`, `AuthenticationError`
- `DatabaseError`, `ProcessingError`
- `ValidationError`, `ConfigurationError`
- `ApplicationError`
- `RetryableError` (special marker for retry logic)

**ExceptionFactory**:
```python
class ExceptionFactory:
    @staticmethod
    def validation_failed(field: str, value: Any, reason: str) -> ValidationError:
        return ValidationError(
            f"Validation failed for field '{field}': {reason}",
            details={"field": field, "value": value, "reason": reason}
        )

    @staticmethod
    def database_connection_failed(uri: str, error: str) -> DatabaseError: ...

    @staticmethod
    def rate_limit_exceeded(limit: int, current: int) -> RateLimitError: ...
```

**Context Managers**:
```python
# Convert exceptions
with handle_errors(ValueError, KeyError, reraise_as=ValidationError):
    int("not a number")

# Retry logic
with retry_on_error(ConnectionError, max_retries=3, on_retry=log_retry):
    fetch_data()
```

**Utility Functions**:
- `is_retryable(error)`: Check if error can be retried
- `get_error_category(error)`: Get error category string

---

### 4. CLI Layer Details (core/cli/ - ~844 lines)

#### Architecture

```mermaid
graph TD
    subgraph "Entry Points"
        MM[__main__.py<br/>python -m core.cli]
        BIN[bin/pulpo<br/>CLI entry script]
    end

    subgraph "Main CLI"
        MAIN[main.py<br/>321 lines<br/>Typer app]
    end

    subgraph "CLI Interface"
        INT[interface.py<br/>444 lines<br/>CLI class]
    end

    subgraph "Command Groups"
        LINT[commands/lint.py<br/>Linting commands]
        OPS[commands/ops.py<br/>Operation commands]
    end

    MM --> MAIN
    BIN --> MAIN
    MAIN --> INT
    MAIN --> LINT
    MAIN --> OPS
```

#### main.py (321 lines) - Typer CLI

**Commands** (20 commands):

| Command | Description | Lines |
|---------|-------------|-------|
| `version` | Show version info | 7 |
| `status` | Show project status | 5 |
| `models` | List registered models | 15 |
| `graph` | Generate relationship graphs | 20 |
| `flows` | Generate operation flow diagrams | 20 |
| `docs` | Generate documentation | 8 |
| `compile` | Compile all artifacts | 8 |
| `api` | Start FastAPI server | 12 |
| `init` | Initialize database & services | 12 |
| `up` | Start all services | 12 |
| `down` | Stop all services | 12 |
| `prefect` | Manage Prefect server | 10 |
| `db` | Manage database service | 10 |
| `clean` | Remove generated artifacts | 10 |
| `ui` | Launch web UI | 20 |
| `help` | Show framework documentation | 30 |
| `ops` | Command group (from commands/ops.py) | - |
| `lint` | Command group (from commands/lint.py) | - |

**Technology**:
- **Typer**: Modern CLI framework (type hints)
- **Rich**: Beautiful terminal output
- Delegates to `CLI` class from `interface.py`

**Example**:
```python
@app.command()
def compile():
    """Compile all artifacts to run_cache."""
    cli = get_cli()
    console.print("[cyan]Compiling...[/cyan]")
    cache_dir = cli.compile()
    console.print(f"[green]✓[/green] Compiled to {cache_dir}")
```

---

## Complete Layer Breakdown

### Summary Table

| Layer | Purpose | Files | Lines | Key Responsibilities |
|-------|---------|-------|-------|---------------------|
| **Base** | Optional mixins | 1 | 41 | DataModelBase, OperationBase |
| **Utils** | Infrastructure | 4 | ~1,400 | Exceptions, logging, validators |
| **Observability** | Self-awareness | 3 | 461 | Event tracking, middleware |
| **Analysis** | Phase 1 | 10 | 2,060 | Discovery, registries, validation, graphs |
| **Generation** | Phase 2 | 8 | 3,250 | Init, compile, code generators |
| **Config** | Configuration | 3 | 550 | Settings, user config, manager |
| **CLI** | User interface | 5+ | ~844 | Framework commands, Typer app |
| **Total** | **All layers** | **34+** | **~8,600** | **Complete framework** |

---

## Data Flow: Complete Picture

```mermaid
sequenceDiagram
    participant User
    participant CLI as pulpo CLI (main.py)
    participant Iface as CLI Interface
    participant Utils as Utils Layer
    participant Reg as Registries
    participant Self as SelfAwareness
    participant Gen as Generators
    participant Docker

    User->>CLI: pulpo compile
    CLI->>Iface: cli.compile()
    Iface->>Self: capture_event(CODEGEN_START)
    Iface->>Reg: Load registries

    alt Error during discovery
        Reg-->>Utils: Raise ValidationError
        Utils-->>Iface: Exception with details
        Iface->>Self: capture_event(CODEGEN_ERROR)
        Iface-->>User: ❌ Error message
    else Success
        Iface->>Gen: Generate all (API, UI, CLI)
        Gen->>Self: capture_event(duration_ms)
        Gen-->>Iface: Generated files
        Iface->>Self: capture_event(CODEGEN_COMPLETE)
        Iface-->>User: ✅ Compiled
    end

    User->>User: ./main up
    User->>Docker: Start services
    Docker-->>User: API running with SelfAwarenessMiddleware

    User->>Docker: POST /api/users
    Docker->>Self: Track request (middleware)

    alt Slow request (> 1s)
        Self->>Self: capture_event(API_REQUEST_SLOW)
    else Error (5xx)
        Self->>Self: capture_event(API_REQUEST_ERROR)
    end
```

---

## Missing from Initial Graph

The initial architecture graph (05_Code_Architecture_Graph.md) was missing:

### Missing Modules (~2,300 lines)

1. **core/base.py** (41 lines)
   - Purpose: Optional base classes
   - Impact: Users can extend for relations/indexes

2. **core/selfawareness/** (461 lines)
   - Purpose: Observability and monitoring
   - Impact: Production insights, error tracking, performance monitoring

3. **core/cli/main.py** (321 lines)
   - Purpose: Typer-based CLI entry point
   - Impact: Beautiful CLI with Rich output

4. **core/cli/commands/** (~100 lines)
   - Purpose: Command groups (lint, ops)
   - Impact: Organized command structure

5. **core/utils/** (~1,400 lines)
   - Purpose: Infrastructure utilities
   - Impact: Exception handling, logging, validation

### Why These Matter

1. **Observability** is critical for production:
   - Track API errors automatically
   - Identify slow operations
   - Debug issues with event history

2. **Exception hierarchy** provides clean error handling:
   - Structured exception types
   - Factory methods for common errors
   - Context managers for retry logic

3. **CLI main.py** gives professional UX:
   - Rich terminal output (colors, formatting)
   - Typer for modern CLI (vs argparse)
   - Better help messages

4. **Base classes** enable advanced features:
   - Relations between models
   - Custom index definitions
   - Searchable/sortable fields

---

## Scalability: Complete Picture

### With All Layers

**Performance**:
- Discovery: O(n) files × discovery
- Validation: O(n) models/ops × validators
- Graph building: O(v + e) DAG construction
- Generation: O(n) models/ops × generators
- **Event tracking**: O(1) capture, O(n) queries

**Resource Usage**:
- EventTracker: ~10,000 events × ~1KB = ~10MB memory
- Exception handling: Minimal overhead
- CLI: Fast (Typer startup ~50ms)

**Extension Points**:
1. Add custom generators → compile/ directory
2. Add custom validators → validation/ directory
3. Add custom exceptions → inherit from PulpoException
4. Add custom CLI commands → commands/ directory
5. Add custom event types → FrameworkEventType enum
6. Add custom middleware → SelfAwarenessMiddleware

---

## Next Steps

1. **For Production**: Enable observability
   ```python
   # In generated_api.py
   from core.selfawareness.middleware import add_selfawareness_middleware
   add_selfawareness_middleware(app, slow_request_ms=500)
   ```

2. **For Error Handling**: Use exception hierarchy
   ```python
   from core.utils.exceptions import ValidationError, ExceptionFactory
   raise ExceptionFactory.validation_failed("email", value, "invalid format")
   ```

3. **For CLI**: Add custom commands
   ```python
   # In commands/mycmd.py
   @app.command()
   def mycmd():
       """My custom command."""
       pass
   ```

4. **For Monitoring**: Query event tracker
   ```python
   from core.selfawareness.tracking import get_tracker
   tracker = get_tracker()
   errors = await tracker.get_errors(limit=100)
   stats = await tracker.get_stats()
   ```

---

## References

- [Architecture Graph (Initial)](05_Code_Architecture_Graph.md) - Phase 1 & 2 only
- [CLI Architecture](04_CLI_Architecture.md) - Framework vs Project CLI
- [Architecture Overview](03_Architecture.md) - High-level design
