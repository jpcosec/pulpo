# 3. Architecture

## Overview

Pulpo is a **two-phase code generation framework** that transforms decorated Python code into full-stack applications.

```
Phase 1: ANALYSIS          Phase 2: GENERATION
Code → Graph               Graph → Code

@datamodel   ────┐         ┌──── generated_api.py
@operation   ────┤         │
                 ▼         ▼
            [DAG/Graph] ────┼──── generated_frontend/
                 │          │
                 └──────────┼──── prefect_flows.py
                            │
                            └──── cli/<project>
```

**Key Principle**: `core/` is the framework (never runs in production). `run_cache/` contains generated code (runs in production).

---

## Two-Phase Architecture

### Phase 1: Analysis (Code → Graph)
**Location**: `core/analysis/`

Discovers, validates, and builds directed acyclic graphs from decorated code.

```
core/analysis/
├── decorators.py          # @datamodel, @operation
├── registries.py          # ModelRegistry, OperationRegistry
├── discovery/             # Two discovery methods:
│   ├── ast_scanner.py     #   - AST-based (static analysis)
│   └── import_scanner.py  #   - Import-based (runtime)
├── graphs/                # Graph construction
│   ├── graph_generator.py #   - Mermaid visualization
│   └── hierarchy.py       #   - Hierarchy analysis
├── dataflow/              # Data flow analysis
│   ├── dataflow.py        #   - Dependency detection
│   └── sync_async.py      #   - Sync/async analysis
└── validation/            # Validation & linting
    ├── linter.py          #   - Anti-pattern detection
    └── doc_helper.py      #   - Documentation helpers
```

**Process**:
1. **Discovery**: Find all `@datamodel` and `@operation` decorators
2. **Registration**: Capture metadata in registries
3. **Graph Building**: Construct DAG where:
   - **Nodes** = `@datamodel` (data entities)
   - **Edges** = `@operation` (transformations)
4. **Validation**: Lint for type errors, missing dependencies, cycles
5. **Visualization**: Generate Mermaid graphs

**Standalone**: Analysis can run independently without generation.

---

### Phase 2: Generation (Graph → Code)
**Location**: `core/generation/`

Generates production code from graphs.

```
core/generation/
├── base.py                # CodeGenerator base class
├── codegen.py             # Orchestrates all generators
│
├── init/                  # INIT phase: Initial setup
│   ├── cli_generator.py   #   - Generate CLI if not exists
│   ├── project_init.py    #   - Create .pulpo.yml, configs
│   └── graph_generator.py #   - Generate graph visualizations
│
└── compile/               # COMPILE phase: Full generation
    ├── api_generator.py   #   - FastAPI routes
    ├── ui_generator.py    #   - React/Refine UI
    ├── compiler.py        #   - Workflow compiler
    └── prefect_codegen.py #   - Prefect flows
```

#### INIT Phase
**Command**: `./main init`

**Generates**:
- CLI executable (if doesn't exist): `run_cache/cli/<project_name>`
- Configuration: `.pulpo.yml`
- Graphs: `docs/*.mmd`

**Purpose**: First-time project setup.

#### COMPILE Phase
**Command**: `./main compile`

**Generates**:
- **API**: `run_cache/generated_api.py` (FastAPI)
- **UI**: `run_cache/generated_frontend/` (React/Refine)
- **Workflows**: `run_cache/prefect_flows.py` (Prefect)
- **CLI**: `run_cache/cli/<project_name>` (Typer)
- **Graphs**: `docs/` (Mermaid)

**Purpose**: Full code generation from updated models/operations.

---

## Configuration Management
**Location**: `core/config/`

```
core/config/
├── manager.py             # ConfigManager (.pulpo.yml)
├── settings.py            # Global settings
└── user_config.py         # User-specific config
```

**Configuration File**: `.pulpo.yml`
```yaml
project_name: my-app
version: 1.0
ports:
  api: 8000
  ui: 3000
  mongodb: 27017
  prefect_server: 4200
discovery:
  models_dirs: [models]
  operations_dirs: [operations]
```

---

## Services (Operate from `run_cache/`)

The 5 Docker services execute **generated code**, not framework code:

### 1. MongoDB
- **Port**: 27017
- **Purpose**: Data persistence
- **Image**: `mongo:7.0`

### 2. API Server (FastAPI)
- **Port**: 8000
- **Runs**: `run_cache/generated_api.py`
- **Endpoints**:
  - `/docs` - Swagger UI
  - `/health` - Health check
  - `/api/v1/*` - Auto-generated CRUD

### 3. UI (React/Refine)
- **Port**: 3000
- **Runs**: `run_cache/generated_frontend/`
- **Features**: Admin panel with CRUD operations

### 4. Prefect Server
- **Port**: 4200
- **Purpose**: Workflow orchestration server
- **UI**: http://localhost:4200

### 5. Prefect Worker
- **Runs**: `run_cache/prefect_flows.py`
- **Purpose**: Execute workflows

---

## Data Flow

### 1. User writes code:
```python
# models/user.py
from core import datamodel

@datamodel
class User:
    email: str
    name: str
```

```python
# operations/create_user.py
from core import operation

@operation
async def create_user(email: str, name: str) -> User:
    user = User(email=email, name=name)
    await user.save()
    return user
```

### 2. User imports in entrypoint:
```python
# main
from models.user import User
from operations.create_user import create_user
from core import CLI

if __name__ == "__main__":
    cli = CLI()
    cli.run()
```

### 3. User runs init:
```bash
./main init
```
**Output**: CLI created, `.pulpo.yml` created, graphs generated.

### 4. User runs compile:
```bash
./main compile
```
**Output**: API, UI, workflows, CLI generated in `run_cache/`.

### 5. User runs services:
```bash
./main up
```
**Output**: 5 Docker containers running generated code.

---

## Directory Structure

```
project/
├── models/                # User's @datamodel classes
│   ├── __init__.py
│   └── user.py
├── operations/            # User's @operation functions
│   ├── __init__.py
│   └── create_user.py
├── .pulpo.yml             # Generated config
├── main                   # User's entrypoint
│
├── run_cache/             # Generated (not in git)
│   ├── generated_api.py
│   ├── generated_frontend/
│   ├── prefect_flows.py
│   └── cli/<project>
│
└── docs/                  # Generated graphs
    ├── models.mmd
    └── operations.mmd
```

```
pulpo/                     # Framework (in git)
├── core/
│   ├── analysis/          # Phase 1
│   ├── generation/        # Phase 2
│   ├── config/
│   ├── cli/
│   ├── utils/
│   └── selfawareness/
├── examples/              # Compressed examples
├── templates/             # Jinja2 templates
└── README.md
```

---

## Key Design Principles

### 1. **Framework Never Runs in Production**
- `core/` generates code
- `run_cache/` runs in production
- Clean separation

### 2. **Graph-Based Architecture**
- All operations analyzed as DAG
- Validates dependencies
- Detects cycles
- Enables parallel execution

### 3. **Two Discovery Methods**
- **AST Scanner**: Static analysis, no imports
- **Import Scanner**: Runtime discovery via decorators

### 4. **Hash-Based Regeneration**
- Only regenerate when models/operations change
- Fast incremental builds
- Cached in `.hash` files

### 5. **Declarative Over Imperative**
- Decorators declare intent
- Framework handles implementation
- No boilerplate

### 6. **Type Safety**
- Pydantic validation everywhere
- Type hints required
- Runtime type checking

---

## Extension Points

### Add Custom Generator
```python
from core.generation.base import CodeGenerator

class MyGenerator(CodeGenerator):
    def generate(self) -> Path:
        # Your generation logic
        pass
```

### Add Custom Discovery
```python
from core.analysis.discovery import DiscoveryMethod

class MyDiscovery(DiscoveryMethod):
    def discover(self, path: Path):
        # Your discovery logic
        pass
```

### Add Custom Validator
```python
from core.analysis.validation import Validator

class MyValidator(Validator):
    def validate(self, registry):
        # Your validation logic
        pass
```

---

## Performance Characteristics

- **Discovery**: O(n) where n = number of Python files
- **Graph Building**: O(v + e) where v = models, e = operations
- **Generation**: O(n) where n = registry size
- **Caching**: O(1) hash lookup to detect changes

**Typical Times** (100 models, 200 operations):
- Discovery: ~500ms
- Graph building: ~200ms
- API generation: ~1s
- UI generation: ~2s
- Total compile: ~4s

---

## Next Steps

- [Getting Started](01_Getting_Started.md) - Install and run
- [Core Concepts](02_Core_Concepts.md) - Decorators and registries
- [Examples](../examples/) - Complete applications
