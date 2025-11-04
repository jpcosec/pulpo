# 3. Architecture

## System Architecture

Pulpo Core implements a layered architecture designed to separate concerns and enable multiple surfaces to work from the same metadata.

### The Pulpo Stack

```
┌─────────────────────────────────────────────────────┐
│          Surfaces (User Interfaces)                  │
├───────────────────┬───────────────────┬──────────────┤
│   REST API        │      CLI          │   React UI   │
│  (FastAPI)        │    (Typer)        │  (Refine.dev)│
├─────────────────────────────────────────────────────┤
│          Core Framework Layer                        │
├───────────────────────────────────────────────────────┤
│  Decorators       Registries         Code Generators │
│  (@datamodel)     (ModelRegistry)    (FastAPI)       │
│  (@operation)     (OperationRegistry)(CLI)           │
│                                      (UI)            │
│                                      (Prefect)       │
├─────────────────────────────────────────────────────┤
│          Orchestration & Observability                │
├───────────────────────────────────────────────────────┤
│  Prefect Flows    Task Tracking      Hierarchy Parser │
│  Flow Generator   Event Logging      Data Flow Analyzer│
├─────────────────────────────────────────────────────┤
│          Data Layer                                   │
├───────────────────┬───────────────────┬──────────────┤
│  Beanie ODM       │   MongoDB         │  Validation  │
│  (Pydantic)       │   Collections     │  (Pydantic)  │
└─────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns** - Each layer has a specific responsibility
2. **Single Responsibility** - Components do one thing well
3. **Declarative Over Imperative** - Decorators declare intent, framework handles execution
4. **Type Safety** - Pydantic validation at all boundaries
5. **Composability** - Components work together seamlessly
6. **Extensibility** - Easy to add custom generators or validators
7. **Non-invasive** - Decorators don't require base classes or mixins

---

## Component Breakdown

### Layer 1: Surfaces (User Interfaces)

The outermost layer where users interact with the system.

#### REST API (FastAPI)

- **Purpose:** HTTP interface for programmatic access
- **Responsibilities:**
  - Handle HTTP requests (GET, POST, PUT, DELETE)
  - Validate input using Pydantic
  - Call appropriate operations
  - Return JSON responses
  - Provide schema discovery (`/models`, `/operations`)
- **Generated Artifacts:**
  - `generated_api.py` containing all routes
  - Swagger UI at `/docs`
  - ReDoc at `/redoc`
- **Automatic Endpoints:**
  - CRUD for every `@datamodel`: `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}`
  - Operations: `POST /operations/{operation_name}`
  - Discovery: `GET /models`, `GET /operations`

#### CLI (Typer)

- **Purpose:** Command-line interface for automation and scripts
- **Responsibilities:**
  - Parse command-line arguments
  - Invoke operations
  - Format output for terminal
  - Provide help and documentation
  - Support batch operations
- **Generated Artifacts:**
  - Dynamic commands from operations
  - Help system auto-generated from decorators
  - Bash completion support
- **Automatic Commands:**
  - `./main help` - Show all available commands
  - `./main ops list` - List operations
  - `./main ops run {operation}` - Execute operation
  - `./main compile` - Generate code
  - `./main up/down` - Manage services

#### React UI (Refine.dev)

- **Purpose:** Admin interface for data management
- **Responsibilities:**
  - Display list views with filtering/sorting
  - Provide create/edit forms
  - Show detailed record views
  - Handle real-time updates
  - Manage navigation
- **Generated Artifacts:**
  - `generated_ui_config.ts` - Configuration for Refine
  - `generated_frontend/` - Complete React application
  - Pages for list, create, edit, show
  - Data provider integration with API
- **Automatic Pages:**
  - List pages with pagination and filtering
  - Create forms with validation
  - Edit forms with updates
  - Show pages with related data

### Layer 2: Core Framework

The heart of Pulpo where metadata is collected, stored, and used for code generation.

#### Decorators Module

**Files:** `decorators.py`

**Purpose:** Collect metadata from code without changing execution

**Key Components:**
- `@datamodel` decorator - Registers Beanie Documents
- `@operation` decorator - Registers async functions

**How it works:**
```python
@datamodel(name="User")
class User(Document):
    email: str
    name: str
    # Decorator registers User with ModelRegistry
```

The decorator:
1. Extracts metadata (name, description, fields, types)
2. Calls `ModelRegistry.register()`
3. Returns the original class unchanged

#### Registries Module

**Files:** `registries.py`

**Purpose:** Store and provide access to collected metadata

**Key Components:**
- `ModelRegistry` - Stores all `@datamodel` metadata
- `OperationRegistry` - Stores all `@operation` metadata
- `Registry` base class - Common interface

**Responsibilities:**
- Store metadata in memory
- Provide query interfaces (get, list, search)
- Support discovery
- Enable code generators to access metadata
- Provide runtime introspection

**How it works:**
```python
# Registration (happens at import time)
ModelRegistry.register("User", model_metadata)

# Access (happens at code generation time)
all_models = ModelRegistry.get_all()
user_model = ModelRegistry.get("User")
```

#### Code Generators Module

**Files:** `codegen.py`

**Purpose:** Synthesize code from metadata

**Key Generator Classes:**
- `FastAPIGenerator` - Generates REST API code
- `CLIGenerator` - Generates CLI commands
- `RefineConfigGenerator` - Generates React configuration
- `RefinePageGenerator` - Generates React pages
- `PrefectCodeGenerator` - Generates Prefect workflows

**How it works:**
1. Query registries for metadata
2. Analyze dependencies and relationships
3. Render Jinja2 templates with metadata
4. Write generated code to `.run_cache/`
5. Calculate hashes to detect changes

**Example - FastAPI Generation:**
```python
generator = FastAPIGenerator()
api_code = generator.generate()  # Returns Python code

# Generates routes like:
# @app.post("/users/crud/create")
# async def create_user(data: UserCreate):
#     return await User.insert_one(data.dict())
```

### Layer 3: Orchestration & Observability

Handles workflow management and tracking.

#### Prefect Integration

**Files:** `orchestration/compiler.py`, `orchestration/prefect_codegen.py`

**Purpose:** Convert hierarchical operations into Prefect flows

**Key Components:**
- `HierarchyParser` - Parse dot-notation operation names
- `DataFlowAnalyzer` - Detect data dependencies
- `OrchestrationCompiler` - Generate flow structure
- `PrefectCodeGenerator` - Generate Prefect code

**How it works:**
```python
# Operation names define hierarchy
@operation(name="pipeline.fetch.source_a")  # Level 3
@operation(name="pipeline.fetch.source_b")  # Level 3 (parallel)
@operation(name="pipeline.merge")          # Level 2 (depends on ^)

# Generates Prefect @flow:
@flow
async def pipeline():
    source_a = await fetch_source_a()  # Parallel
    source_b = await fetch_source_b()  # Parallel
    result = await merge(source_a, source_b)  # Sequential
```

#### Observability & Tracking

**Files:** `selfawareness/tracking.py`, `selfawareness/events.py`

**Purpose:** Track execution and provide audit trails

**Key Features:**
- Operation execution tracking
- Event logging
- Audit trails
- Performance metrics
- Error tracking

### Layer 4: Data Layer

Handles database operations and validation.

#### Beanie ODM Integration

**Files:** `database.py`

**Purpose:** Async MongoDB integration with type safety

**Key Features:**
- Async MongoDB driver (Motor)
- Document mapping (Beanie)
- Type validation (Pydantic)
- Query helpers
- Migration support

**Responsibilities:**
- Database connection management
- Document serialization/deserialization
- Query building
- Index management
- Transaction support

#### Validation

**Files:** `utils/validators.py`

**Purpose:** Ensure data integrity

**Key Features:**
- Input validation via Pydantic models
- Output validation
- Custom validators
- Type checking
- Error messages

---

## Data Flow Lifecycle

Understanding how data flows through the system helps you use Pulpo Core effectively.

### Request Flow (API Example)

```
User Request
    ↓
HTTP POST /operations/checkout.process
    ↓
FastAPI Route Handler (Generated)
    ↓
Input Validation (Pydantic)
    ↓
Call Operation Function
    ↓
Prefect Task Wrapping (if enabled)
    ↓
Async Operation Logic
    ↓
Database Operations (Beanie)
    ↓
Output Creation
    ↓
Output Validation (Pydantic)
    ↓
JSON Response
    ↓
HTTP 200 OK + JSON
```

### CLI Flow (Command Example)

```
CLI Command: ./main ops run checkout.process --input '...'
    ↓
Typer Command Handler
    ↓
Argument Parsing
    ↓
Operation Discovery (OperationRegistry)
    ↓
Input Deserialization
    ↓
Input Validation (Pydantic)
    ↓
Async Operation Logic
    ↓
Database Operations (Beanie)
    ↓
Output Formatting
    ↓
Terminal Display
```

### Code Generation Flow

```
./main compile
    ↓
Load Main Entrypoint
    ↓
Import Models & Operations
    ↓
Decorators Register Metadata
    ↓
Registries Populated
    ↓
Code Generators Query Registries
    ↓
Analyze Dependencies
    ↓
Render Templates
    ↓
Write to .run_cache/
    ↓
Calculate Hashes
    ↓
Done - Code Ready
```

### Model Creation Flow (Database)

```
Pydantic Input Model (from decorator parameters)
    ↓
User provides JSON data
    ↓
Pydantic validates and deserializes
    ↓
Field types checked
    ↓
Custom validators run
    ↓
Beanie Document created
    ↓
MongoDB insert_one()
    ↓
Document ID generated
    ↓
Success response with ID
    ↓
Pydantic Output Model
    ↓
JSON response to client
```

---

## Module Organization

The framework is organized into logical modules with clear responsibilities.

### Core Module Structure

```
core/
├── __init__.py                 # Main exports (datamodel, operation, CLI)
├── decorators.py               # @datamodel and @operation decorators
├── registries.py               # ModelRegistry and OperationRegistry
├── base.py                     # Optional base classes
├── codegen.py                  # Code generators
├── api.py                      # FastAPI integration
├── database.py                 # MongoDB/Beanie setup
│
├── cli/                        # CLI Implementation
│   ├── main.py                # Main CLI app (Typer)
│   ├── commands/
│   │   ├── ops.py            # Operation commands
│   │   ├── compile.py        # Code generation
│   │   ├── services.py       # Service management
│   │   └── ...
│   └── interface.py           # Programmatic CLI interface
│
├── orchestration/              # Prefect Integration
│   ├── compiler.py            # Generate flow structure
│   ├── dataflow.py            # Analyze dependencies
│   ├── hierarchy.py           # Parse operation hierarchy
│   └── prefect_codegen.py     # Generate Prefect code
│
├── selfawareness/              # Observability
│   ├── tracking.py            # Operation tracking
│   ├── events.py              # Event system
│   └── middleware.py          # Request/response logging
│
└── utils/                      # Utilities
    ├── config.py              # Settings management
    ├── logging.py             # Structured logging
    ├── exceptions.py          # Custom exceptions
    └── validators.py          # Validation helpers
```

### Module Responsibilities

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `decorators` | Metadata collection | `datamodel`, `operation` |
| `registries` | Metadata storage | `ModelRegistry`, `OperationRegistry` |
| `codegen` | Code synthesis | `FastAPIGenerator`, `RefineConfigGenerator` |
| `api` | HTTP interface | `FastAPI` integration, routes |
| `database` | Data persistence | `Beanie`, `Motor`, `MongoDB` integration |
| `cli` | Command-line interface | `Typer`, `CLI`, command handlers |
| `orchestration` | Workflow generation | `HierarchyParser`, `PrefectCodeGenerator` |
| `selfawareness` | Observability | `TaskTracker`, `EventLogger` |
| `utils` | Shared utilities | Config, logging, validation, exceptions |

---

## Design Patterns

Pulpo Core uses several well-known design patterns to achieve its goals.

### 1. Decorator Pattern

**Problem:** Add metadata to classes without modifying them

**Solution:** Use Python decorators to wrap classes and register metadata

```python
@datamodel(name="User")
class User(Document):
    email: str
    # Decorator registers metadata, doesn't change class behavior
```

### 2. Registry Pattern

**Problem:** Centralize access to all models and operations

**Solution:** Use in-memory registries as single source of truth

```python
class ModelRegistry:
    _models = {}  # Central storage

    @classmethod
    def register(cls, name, model):
        cls._models[name] = model

    @classmethod
    def get(cls, name):
        return cls._models.get(name)
```

### 3. Code Generation Pattern

**Problem:** Generate boilerplate code from metadata

**Solution:** Use templates and generators to synthesize code

```python
class FastAPIGenerator:
    def generate(self) -> str:
        models = ModelRegistry.get_all()
        template = load_template('api.jinja2')
        return template.render(models=models)
```

### 4. Factory Pattern

**Problem:** Create different types of generators for different outputs

**Solution:** Use factory methods to instantiate appropriate generators

```python
generators = {
    'api': FastAPIGenerator(),
    'cli': CLIGenerator(),
    'ui': RefineConfigGenerator(),
    'prefect': PrefectCodeGenerator(),
}
```

### 5. Chain of Responsibility

**Problem:** Process requests through multiple handlers

**Solution:** Chain handlers together, each handles part of the request

```
Request → Validation → Operation Logic → Response Creation → JSON → HTTP
```

### 6. Strategy Pattern

**Problem:** Handle different operation types (sync vs async, simple vs complex)

**Solution:** Use different strategies based on operation characteristics

```python
if operation.is_async:
    strategy = AsyncOperationStrategy()
else:
    strategy = SyncOperationStrategy()

strategy.execute(operation, input)
```

### 7. Adapter Pattern

**Problem:** Work with different backends (FastAPI, Typer, React)

**Solution:** Create adapters that translate between core concepts and backend APIs

```python
class FastAPIAdapter:
    def generate_route(operation):
        # Adapt operation to FastAPI route

class TypierAdapter:
    def generate_command(operation):
        # Adapt operation to Typer command
```

---

## Data Models Overview

The framework works with several types of data throughout its lifecycle:

### Model Metadata

Information about a `@datamodel` decorated class:

```python
ModelInfo = {
    "name": "User",
    "description": "A user account",
    "fields": {
        "email": {"type": "str", "required": True},
        "name": {"type": "str", "required": True},
        "age": {"type": "int", "required": False, "default": 0},
    },
    "tags": ["users"],
    "schema": {...}  # JSON schema
}
```

### Operation Metadata

Information about an `@operation` decorated function:

```python
OperationMetadata = {
    "name": "user.create",
    "description": "Create a new user",
    "inputs": {...},      # Pydantic model schema
    "outputs": {...},     # Pydantic model schema
    "category": "user-management",
    "models_in": ["User"],
    "models_out": [],
    "function": <async function>,
}
```

---

## Key Architectural Decisions

### Decision 1: Pre-Generated Code (Not Runtime)

**Why:** Generated code can be version controlled, type-checked, and deployed reliably

**Trade-off:** Requires running `compile` after model/operation changes

**Benefit:** Production code is identical to what developers review and test

### Decision 2: Metadata-Driven (Not Magic)

**Why:** Makes framework behavior explicit and debuggable

**Trade-off:** More explicit syntax (decorators) needed

**Benefit:** Easy to understand what's happening behind the scenes

### Decision 3: Async-First

**Why:** Enables efficient resource usage and scales better

**Trade-off:** All operations must be `async def`

**Benefit:** Better performance, easier to add concurrent operations

### Decision 4: Main Entrypoint Discovery (Not File Scanning)

**Why:** Explicit imports = clear dependencies and faster discovery

**Trade-off:** Must manually import models/operations in main

**Benefit:** No magic file scanning, clear what's included, pip-installable

### Decision 5: Multiple Surfaces (Not One-Size-Fits-All)

**Why:** Different users need different interfaces (API, CLI, UI)

**Trade-off:** Three surfaces to manage instead of one

**Benefit:** One definition works everywhere, users choose their interface

---

## Summary

Pulpo Core's architecture is designed around:

1. **Metadata Collection** via decorators
2. **Centralized Storage** in registries
3. **Code Generation** from templates
4. **Multiple Surfaces** from one definition
5. **Type Safety** throughout
6. **Clear Separation of Concerns** in layered architecture

This enables developers to write business logic once and automatically get API, CLI, UI, and workflows.

---

**Next:** Learn how to define decorators in [Decorator Reference](04_Decorator_Reference.md)
