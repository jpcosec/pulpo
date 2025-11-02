# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pulpo Core** is a metadata-driven code generation framework (v0.6.0) that implements the "Define Once, Generate Everywhere" pattern. It automatically generates REST APIs (FastAPI), CLIs (Typer), React UIs (Refine.dev), and Prefect workflow orchestration from decorator-based metadata.

**Core Pattern:**
1. Define data models with `@datamodel` decorator (Beanie + MongoDB)
2. Define operations with `@operation` decorator (async functions)
3. Decorators register metadata in global registries
4. Code generators consume registries and synthesize production code
5. Pre-generated code is written to `.run_cache/` directory (excluded from git)
6. Surfaces (API, CLI, UI) consume registries at runtime

---

## Common Development Commands

### Quick Start (Project-Based)
```bash
# For example projects
cd examples/pokemon-app
./main init       # Initialize services
./main compile    # Generate code from decorators → .run_cache/
./main api        # Start API server locally (requires MongoDB)
./main up         # Start all services
./main down       # Stop services
./main help       # View documentation
```

### Docker Development (Framework-Level)
```bash
# From project root (for framework development)
make compile      # Generate code from all projects
make build        # Build Docker images
make up           # Start all services
make health       # Check status of all services
make down         # Stop services
```

### Discovery & Documentation
```bash
# View available documentation
pulpo help                      # List all framework topics
pulpo help datamodel           # View @datamodel decorator docs
./main help                     # List project models and operations
./main help model Pokemon      # View Pokemon model documentation
./main help operation pokemon.battles.execute  # View operation docs
./main help framework datamodel  # View framework docs from project
```

### Code Quality & Testing
```bash
make lint         # Run ruff linter
make format       # Auto-format with ruff
make type-check   # Run mypy type checker
make test-unit    # Run unit tests
make lint-models  # Lint @datamodel/@operation decorators
```

### Frontend Development
```bash
make compile      # Generate React code
make ui-dev       # Start React dev server (http://localhost:3000)
make ui-build     # Build React for production
```

### Database Management
```bash
make db-start     # Start MongoDB in Docker
make db-status    # Check MongoDB status
make db-shell     # Open MongoDB shell
```

### Help
```bash
make help         # Show all available commands
```

---

## Architecture & Code Organization

### Layered Architecture
```
┌─────────────────────────────────────┐
│  Surfaces (API, CLI, UI)            │
├─────────────────────────────────────┤
│  Core Framework                     │
│  ├─ Decorators (metadata collection)│
│  ├─ Registries (central storage)    │
│  └─ Code Generators (synthesis)     │
├─────────────────────────────────────┤
│  Data Layer (Beanie + MongoDB)      │
└─────────────────────────────────────┘
```

### Key Directories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| **core/** | Framework core | `__init__.py`, `decorators.py`, `registries.py`, `base.py`, `codegen.py` |
| **core/cli/** | CLI implementation (Typer) | `main.py`, `commands/ops.py`, `commands/lint.py` |
| **core/orchestration/** | Prefect flow generation | `compiler.py`, `dataflow.py`, `prefect_codegen.py` |
| **core/selfawareness/** | Framework monitoring | `tracking.py`, `events.py`, `middleware.py` |
| **core/utils/** | Utilities | `config.py`, `logging.py`, `exceptions.py`, `validators.py` |
| **docs/** | Developer documentation | Architecture guides, integration guides |
| **tests/** | Test suite | `unit/`, `integration/`, `phase3/` (4,145 lines) |
| **scripts/** | Discovery & utilities | `discover.py`, `init_project.py`, `service_manager.py` |
| **docker/** | Container orchestration | `docker-compose.yml`, Dockerfiles |
| **.run_cache/** | Generated code (git-ignored) | `generated_api.py`, `generated_ui_config.ts`, `generated_frontend/` |

---

## Key Design Patterns

### 1. Decorator Pattern (Metadata Collection)
```python
from beanie import Document
from core import datamodel, operation

@datamodel(name="Item", tags=["items"])
class Item(Document):
    name: str
    status: str

@operation(name="process_item", inputs=ProcessInput, outputs=ProcessOutput)
async def process_item(input: ProcessInput) -> ProcessOutput:
    return ProcessOutput(success=True, message="Processed")
```

### 2. Registry Pattern (Single Source of Truth)
- `ModelRegistry`: Stores all `@datamodel` metadata
- `OperationRegistry`: Stores all `@operation` metadata
- Both are populated at import time (state is in memory, not database)

### 3. Code Generation Pattern (Pre-generation, Not Runtime)
- Generators read registries and synthesize code
- Output written to `.run_cache/` directory
- Hash-based change detection (regenerate only if metadata changed)
- Enables static analysis, type checking, caching

### 4. Hierarchical Naming for Orchestration
```python
@operation(name="pipeline.source_a.fetch")  # Level 3
@operation(name="pipeline.source_b.fetch")  # Level 3 (can parallelize)
@operation(name="pipeline.merge")           # Level 2 (depends on ^)
```
- Dot-separated naming automatically creates flow hierarchy
- Framework auto-generates Prefect flows from this structure

### 5. Async-First Design
- All operations must be `async def`
- Built on Beanie (async MongoDB ODM)
- Integrates with Prefect (async orchestration)

---

## Core Concepts & APIs

### @datamodel Decorator
**Purpose:** Register a Beanie Document for code generation

```python
@datamodel(
    name="Item",                         # Required: registry name
    description="Generic item model",    # Optional
    tags=["items"],                      # Optional: for organization
    ui_order=1                           # Optional: UI field ordering
)
class Item(Document):
    name: str
    status: str

    class Settings:
        name = "items"  # MongoDB collection name
```

**Enables:**
- CRUD API endpoints: `GET /items`, `POST /items`, `PUT /items/{id}`, `DELETE /items/{id}`
- UI pages: list, create, edit, show
- Type validation via Pydantic

### @operation Decorator
**Purpose:** Register an async operation for API/CLI/orchestration

```python
@operation(
    name="process_item",                 # Required: unique operation name
    description="Process an item",       # Optional
    category="processing",               # Optional
    inputs=ProcessInput,                 # Required: Pydantic model
    outputs=ProcessOutput,               # Required: Pydantic model
    models_in=["Item"],                 # Optional: models read
    models_out=[]                       # Optional: models written
)
async def process_item(input: ProcessInput) -> ProcessOutput:
    return ProcessOutput(success=True, message="Processed")
```

**Enables:**
- API endpoint: `POST /operations/process_item` with input validation
- CLI command: `<PROJECT_CLI> ops process_item --input '{"item_id": "123", ...}'`
- Prefect task integration
- Operation tracking via TaskRun

### ModelRegistry
```python
from core.registries import ModelRegistry

# Access all registered models
models = ModelRegistry.get_all()          # List[ModelInfo]
model = ModelRegistry.get("Item")          # ModelInfo | None
fields = ModelRegistry.get_fields("Item")  # Dict[str, FieldInfo]
```

### OperationRegistry
```python
from core.registries import OperationRegistry

# Access all registered operations
ops = OperationRegistry.get_all()          # List[OperationMetadata]
op = OperationRegistry.get("process_item") # OperationMetadata | None
```

---

## Code Generation Pipeline

### Generation Trigger Points

1. **make compile** (manual)
   ```bash
   PYTHONPATH=.:$PYTHONPATH python3 -m core.codegen
   ```

2. **make api / make up** (automatic)
   - Calls `make compile` before starting services

3. **Direct API** (in code)
   ```python
   from core.codegen import FastAPIGenerator, RefineConfigGenerator

   api_gen = FastAPIGenerator()
   api_code = api_gen.generate()  # → .run_cache/generated_api.py

   ui_gen = RefineConfigGenerator()
   ui_config = ui_gen.generate()  # → .run_cache/generated_ui_config.ts
   ```

### Generated Output Structure
```
.run_cache/
├── generated_api.py              # FastAPI routes (CRUD + operations)
├── generated_ui_config.ts        # TypeScript config for React
├── generated_frontend/           # Complete React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
└── .gitkeep
```

### Generation Process
1. **Discovery**: Scan registries for models and operations
2. **Analysis**: Build dependency graph, relationship map
3. **Synthesis**: Generate code from templates (Jinja2)
4. **Writing**: Output to `.run_cache/` with hash-based caching
5. **Validation**: Verify generated code is valid Python/TypeScript

---

## Testing Strategy

### Test Organization
```
tests/
├── unit/              # Framework behavior (decorators, registries)
├── integration/       # CLI/API integration
└── phase3/           # Real-world scenarios, performance
```

### Running Tests
```bash
make test-unit        # Unit tests with coverage
make test-integration # Integration tests
make test-all         # All tests
make test-coverage    # Coverage report
```

### Test Fixtures & Mocking
```python
# In tests, use:
from mongomock_motor import AsyncMongoMockClient  # Mock MongoDB

@pytest.fixture
async def mock_db():
    client = AsyncMongoMockClient()
    return client.test_db
```

---

## Key Dependencies & Versions

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **Data Models** | Pydantic | ^2.6.0 | Type validation |
| | Beanie | ^1.25.0 | Async MongoDB ODM |
| | Motor | ^3.3.2 | Async MongoDB driver |
| **API** | FastAPI | ^0.109.0 | REST API generation |
| | Uvicorn | ^0.27.0 | ASGI server |
| **CLI** | Typer | ^0.19.0 | CLI framework |
| | Rich | ^13.7.0 | Terminal formatting |
| **Orchestration** | Prefect | ^3.0.0 | (optional) Workflow orchestration |
| **Code Gen** | Jinja2 | ^3.1.3 | Template rendering |
| **Utilities** | Structlog | ^24.1.0 | Structured logging |
| | Pydantic-Settings | ^2.1.0 | Configuration management |
| | Python-dotenv | ^1.0.1 | .env file support |

### Optional Dependencies
To use Prefect orchestration:
```bash
poetry install -E workflow
# or
poetry install -E all
```

---

## Configuration Management

### Settings Hierarchy
```python
from core.utils.config import get_settings

settings = get_settings()  # Merges: .env → environment vars → defaults
```

### Configuration Files
- `.env` (root): Database connection, API settings, Prefect config
- `pyproject.toml`: Package metadata, dependencies, tool config
- `.pulpo.yml` (projects): Per-project discovery paths, ports (configurable via CONFIG_FILE)

### Required Settings
```env
MONGODB_DATABASE=pulpo
MONGODB_URL=mongodb://localhost:27017
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Development Workflow

### 1. Define New Model
```python
# in core/examples/models/new_model.py
from beanie import Document
from core import datamodel

@datamodel(name="MyModel", tags=["example"])
class MyModel(Document):
    name: str
    value: int

    class Settings:
        name = "my_models"
```

### 2. Define New Operation
```python
# in core/examples/operations/new_ops.py
from pydantic import BaseModel
from core import operation

class MyInput(BaseModel):
    name: str

class MyOutput(BaseModel):
    result: str

@operation(
    name="my_operation",
    inputs=MyInput,
    outputs=MyOutput,
    models_in=["MyModel"]
)
async def my_operation(input: MyInput) -> MyOutput:
    return MyOutput(result=f"Processed {input.name}")
```

### 3. Generate & Test
```bash
make compile              # Generate code
make test-unit           # Run unit tests
make api                 # Test API locally
```

### 4. Verify Discovery
```bash
make discover            # Shows all registered models/operations
```

---

## Debugging & Troubleshooting

### Check Registry State
```python
from core.registries import ModelRegistry, OperationRegistry

# In Python REPL:
ModelRegistry.list()              # All models
OperationRegistry.list()          # All operations
ModelRegistry.get_schema("Item")   # JSON schema
```

### View Generated Code
```bash
cat .run_cache/generated_api.py       # Generated FastAPI routes
cat .run_cache/generated_ui_config.ts # Generated UI config
```

### Enable Debug Logging
```python
# In code:
import structlog
structlog.configure(...)  # See core/utils/logging.py

# Or environment:
LOG_LEVEL=DEBUG make api
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Model not found in registry" | Run `make discover` to check if model is detected |
| Generated code has import errors | Check Pydantic model definitions, run `make type-check` |
| API won't start | Check MongoDB is running: `make db-status` |
| Tests fail with async errors | Ensure all operations are `async def`, check `pytest.ini_options.asyncio_mode` |
| Prefect flows don't appear | Check hierarchical naming uses dots (e.g., `pipeline.fetch`) |

---

## Code Style & Standards

### Python Style
- **Line Length:** 100 characters (ruff)
- **Python Version:** 3.11+ (f-strings, async/await, type hints)
- **Type Hints:** Required on function signatures
- **Async/Await:** All operations must be `async def`

### Ruff Configuration
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]  # Line too long
```

### Type Checking
```bash
mypy core/                # Full type check
mypy --strict core/       # Strict mode (not required)
```

### Formatting & Linting
```bash
ruff format core/         # Auto-format
ruff check core/ --fix    # Auto-fix linting issues
```

---

## Documentation Structure

### Key Documentation Files
- `README.md` - Project overview and quick start
- `docs/ARCHITECTURE_OVERVIEW.md` - System design
- `docs/HOW_CORE_WORKS.md` - Implementation details
- `docs/CLI_ARCHITECTURE.md` - CLI design
- `docs/DATAMODEL_DECORATOR.md` - `@datamodel` reference
- `docs/OPERATION_DECORATOR.md` - `@operation` reference
- `docs/ORCHESTRATION.md` - Hierarchical naming & Prefect
- `docs/externals/` - Integration guides (Frontend, CLI, Prefect)

### Adding Documentation
1. General docs go in `docs/` folder
2. Module-specific docs go in the module folder
3. Link from main README.md
4. Update CHANGELOG.md for major changes

---

## Important Notes

### Framework Characteristics
- **Stateless at Runtime**: All state is in registries (built at import time)
- **Pre-Compiled Code**: Generators produce code written to disk (not runtime generation)
- **Non-Invasive**: Decorators don't change execution, just register metadata
- **Optional Base Classes**: Framework works with plain Pydantic/Beanie docs

### What Core Does NOT Do
- No heavy ORM magic (use Beanie's native API)
- No automatic relationship loading (explicit is better)
- No vendor lock-in (standard FastAPI, React, MongoDB)
- No magic field validation (use Pydantic validators)

### Git Ignore Rules
`.gitignore` excludes:
- `.run_cache/` - Generated code (always regenerate)
- `__pycache__/` - Python bytecode
- `.env` - Local config (use .env.example)
- `.pytest_cache/` - Test artifacts

---

## Useful Commands at a Glance

```bash
# Development
make compile && make api              # Generate code + start API
make lint && make type-check          # Code quality check
make test-unit                        # Run unit tests

# Debugging
make discover                         # Show registry state
cat .run_cache/generated_api.py      # View generated code

# Docker
make build && make up                 # Full Docker setup
make health                           # Check all services
make logs                             # Watch service logs

# Database
make db-start                         # Start MongoDB
make db-shell                         # Open MongoDB CLI
```

---

## When to Escalate or Ask for Help

- Framework design questions: Check `docs/ARCHITECTURE_OVERVIEW.md`
- Decorator usage questions: Check `docs/DATAMODEL_DECORATOR.md` and `docs/OPERATION_DECORATOR.md`
- Integration questions: Check `docs/externals/`
- If stuck on a bug: Try `make clean-cache` then `make compile`
