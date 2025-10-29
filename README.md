# Pulpo Core Framework

**Version:** 0.6.0 (First iteration toward pip-installable library)
**A metadata-driven code generation framework for building full-stack applications**

## Overview

Pulpo Core is a domain-agnostic framework that implements the **"Define Once, Generate Everywhere"** pattern with hierarchical orchestration. Write your data models and operations once using Python decorators, and automatically generate:

- **REST API** (FastAPI with auto-generated CRUD endpoints)
- **CLI** (Dynamic, introspection-capable command-line interface)
- **UI** (React + Refine.dev admin interface)
- **Prefect Orchestration** (Auto-generated from hierarchical operation naming)
- **Data Flow Graphs** (Automatic relationship visualization)
- **Operation Flow Graphs** (Automatic orchestration visualization)

The framework uses decorator-based metadata collection and code generation to eliminate boilerplate while maintaining full type safety and customization capabilities. Prefect handles all orchestration, logging, and observability automatically.

## Key Features

- **Decorator-Based**: Simple `@datamodel` and `@operation` decorators for registration
- **Type-Safe**: Full Pydantic validation and type hints throughout
- **Auto-Generated APIs**: CRUD endpoints for all models with filtering, sorting, pagination
- **Auto-Generated UI**: React admin interface with create/edit/list/show pages
- **CLI Integration**: Operations automatically become CLI commands
- **Database**: MongoDB with Beanie ODM (async, type-safe)
- **Workflow Support**: Prefect integration for orchestration (auto-generated from operation hierarchy)
- **Observability**: Prefect handles all logging, tracking, and audit trails automatically

## Quick Start (3 Commands!)

From the **project root**:

```bash
make compile    # Compile: scan decorators → generate code
make build      # Build: build Docker images
make up         # Start: run services
```

**Your API, UI, and CLI are ready!**

Then for detailed framework development, install locally:

```bash
# Install with poetry (for development)
cd core
poetry install

# Or install with pip
pip install -e .

# With workflow support
poetry install -E workflow
```

---

## Define Once, Generate Everywhere

### 1. Define a Data Model

```python
from beanie import Document
from core import datamodel

@datamodel(
    name="Job",
    description="Job posting model",
    tags=["jobs", "recruiting"]
)
class Job(Document):
    """Job posting from external sources."""

    source: str
    external_id: str
    title: str
    company: str
    url: str

    class Settings:
        name = "jobs"  # MongoDB collection name
```

**What happens:**
- Model is registered in `ModelRegistry`
- CRUD API endpoints are generated: `GET /jobs`, `POST /jobs`, etc.
- UI pages are generated: list, create, edit, show
- Full type validation via Pydantic

### 2. Define an Operation

```python
from pydantic import BaseModel
from core import operation

class MatchInput(BaseModel):
    user_id: str
    job_id: str

class MatchOutput(BaseModel):
    score: float
    reasons: list[str]

@operation(
    name="match_job",
    description="Compute job match score for user",
    category="matching",
    inputs=MatchInput,
    outputs=MatchOutput,
    models_in=["User", "Job"],
    models_out=[]
)
async def match_job(input: MatchInput) -> MatchOutput:
    """Calculate how well a job matches a user's profile."""
    # Your logic here
    return MatchOutput(
        score=0.85,
        reasons=["Skills match", "Location match"]
    )
```

**What happens:**
- Operation is registered in `OperationRegistry`
- API endpoint is created: `POST /operations/match_job`
- CLI command is created: `jobhunter ops match_job`
- Operation is tracked via TaskRun for observability

### 3. Generate Surfaces

```python
# Generate API
from core.codegen import FastAPIGenerator

api_gen = FastAPIGenerator()
api_code = api_gen.generate()

# Generate UI config
from core.codegen import RefineConfigGenerator

ui_gen = RefineConfigGenerator()
ui_config = ui_gen.generate()

# Or use the CLI
jobhunter generate api
jobhunter generate ui-config
jobhunter generate ui-pages
```

### 4. Run Your Application

```bash
# Start API server
jobhunter api start

# Or run directly
python -m core.api

# Use CLI
jobhunter ops list
jobhunter ops run match_job --input '{"user_id": "123", "job_id": "456"}'
```

## Architecture

```
core/
├── decorators.py          # @datamodel and @operation decorators
├── registries.py          # ModelRegistry and OperationRegistry
├── base.py                # Optional base classes
├── codegen.py             # Code generators (API, UI, CLI)
├── api.py                 # FastAPI integration
├── database.py            # MongoDB/Beanie connection
├── cli/                   # CLI framework (Typer)
│   ├── main.py           # Main CLI app
│   └── commands/         # Command modules
├── utils/                 # Utilities
│   ├── config.py         # Settings management
│   ├── logging.py        # Logging setup
│   ├── exceptions.py     # Custom exceptions
│   └── validators.py     # Validation helpers
├── examples/              # Example models and operations
│   ├── models/           # Example data models
│   └── operations/       # Example operations
├── frontend_template/     # React/Refine.dev templates
└── docs/                  # Documentation
    ├── ARCHITECTURE_OVERVIEW.md
    ├── HOW_CORE_WORKS.md
    ├── DATAMODEL_DECORATOR.md
    ├── OPERATION_DECORATOR.md
    └── externals/        # Integration guides
```

## Core Concepts

### Decorators

**`@datamodel`**: Registers a Beanie Document for code generation
- Collects metadata (name, description, tags, UI hints)
- Enables CRUD API generation
- Enables UI page generation

**`@operation`**: Registers a typed operation (function or class)
- Defines inputs/outputs with Pydantic models
- Supports categorization and tagging
- Enables API endpoint and CLI command generation

### Registries

**`ModelRegistry`**: Central registry for all data models
- Stores model metadata and schemas
- Used by code generators to create APIs and UIs
- Supports runtime inspection

**`OperationRegistry`**: Central registry for all operations
- Stores operation metadata, inputs, outputs
- Used to generate API endpoints and CLI commands
- Supports dependency graph analysis

### Code Generators

**`FastAPIGenerator`**: Generates REST API code
- CRUD endpoints for all models
- Operation endpoints
- Discovery endpoints (`/models`, `/operations`)

**`RefineConfigGenerator`**: Generates TypeScript UI configuration
- Resource definitions
- Navigation structure
- Data provider configuration

**`RefinePageGenerator`**: Generates React UI pages
- List pages with filtering and pagination
- Show pages with related data
- Create/Edit forms with validation

## Advanced Features

### Optional Base Classes

```python
from core.base import DataModelBase, OperationBase

class Job(Document, DataModelBase):
    """Enhanced model with additional methods."""

    @classmethod
    def relations(cls) -> list[dict]:
        return [{"field": "company_id", "model": "Company"}]

    @classmethod
    def indexes(cls) -> list:
        return ["source", "external_id"]

class ComplexOperation(OperationBase):
    """Multi-step operation with planning."""

    async def validate(self, input):
        # Pre-execution validation
        pass

    async def plan(self, input):
        # Generate execution plan
        pass

    async def run(self, input):
        # Execute operation
        pass
```

### Workflow Integration

```python
from prefect import flow, task

@operation(
    name="process_batch",
    orchestrator="prefect"
)
@flow
async def process_batch(input: BatchInput) -> BatchOutput:
    results = await process_items.map(input.items)
    return BatchOutput(results=results)

@task
async def process_items(item):
    # Process single item
    pass
```

### Observability & Orchestration

All operations are automatically tracked and orchestrated via **Prefect**:

```python
# Prefect provides:
# - Automatic task run tracking with full lineage
# - Execution history and logs
# - State management and retry logic
# - Flow visualization in Prefect UI
# - Automatic parallelization of same-level operations
# - Dependency injection based on operation inputs/outputs
```

Operations use hierarchical naming for automatic flow composition:

```python
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(): ...

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(): ...

@operation(name="scraping.merge")
async def merge(stepstone, linkedin):
    # Dependencies auto-injected, parallel fetches handled by framework
    ...

# Framework generates Prefect @flow with parallel fetch tasks
# Prefect UI shows full dependency graph and execution history
```

## Documentation

### Getting Started

- **[Main README](README.md)** - Framework overview (this file)
- **[CLAUDE.md](CLAUDE.md)** - Developer guide

### Core Concepts

- **[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)** - System design and separation of concerns
- **[CLI Architecture](docs/CLI_ARCHITECTURE.md)** - Dynamic discovery and smart compilation
- **[How Core Works](docs/HOW_CORE_WORKS.md)** - Implementation details
- **[Datamodel Decorator](docs/DATAMODEL_DECORATOR.md)** - `@datamodel` reference
- **[Operation Decorator](docs/OPERATION_DECORATOR.md)** - `@operation` reference
- **[Hierarchy & Orchestration](docs/ORCHESTRATION.md)** - Hierarchical naming and Prefect flows

### Integration Guides

- **[Frontend Integration](docs/externals/FRONTEND_INTEGRATION.md)** - React/Refine.dev setup
- **[CLI Integration](docs/externals/CLI_INTEGRATION.md)** - CLI usage patterns
- **[Prefect Integration](docs/externals/PREFECT_INTEGRATION.md)** - Orchestration and flows

## Testing

```bash
# Run all tests
poetry run pytest

# Run specific test types
poetry run pytest tests/unit/
poetry run pytest tests/integration/

# With coverage
poetry run pytest --cov=core --cov-report=html
```

## Philosophy

### Design Principles

1. **Define Once**: Write models and operations once using decorators
2. **Generate Everywhere**: Auto-generate API, CLI, and UI from metadata
3. **Type Safety**: Full Pydantic validation throughout
4. **Domain Agnostic**: Core is reusable across different domains
5. **Minimal Boilerplate**: Decorators handle registration and generation
6. **Incremental Adoption**: Use what you need, opt-in to features

### What Core Does NOT Do

- **No Repository Pattern**: Beanie already provides this
- **No Heavy ORM**: Use Beanie's native query API
- **No Magic**: Everything is explicit and inspectable
- **No Vendor Lock-in**: Standard FastAPI, React, MongoDB

### When to Use Core

✅ **Good fit:**
- Admin interfaces and CRUD applications
- Data management tools
- Internal tools and dashboards
- Microservices with standard operations
- Prototypes that need to scale

❌ **Not ideal for:**
- Simple scripts (use Beanie directly)
- Highly custom UIs (core generates admin interfaces)
- Applications without data models
- Projects that don't need API + UI + CLI

## Examples

The `core/examples/` directory contains working examples:

```python
# Example model
from core.examples.models.test_model import TestItem

# Example operations
from core.examples.operations.test_ops import create_test_item

# Run example
await create_test_item(CreateTestInput(name="example", value=42))
```

## Contributing

The core framework is designed to be extended:

1. **Add new generators**: Implement new code generators in `codegen.py`
2. **Add new decorators**: Create new decorators for specific use cases
3. **Add new CLI commands**: Extend `cli/commands/` with new modules
4. **Add new validators**: Extend `utils/validators.py`

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: Report issues in the main repository

---

**Built with:** Python 3.11+, FastAPI, Beanie, Prefect, Typer, Pydantic, React, Refine.dev
