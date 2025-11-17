# Code Architecture Graph - File Responsibilities

This document visualizes the Pulpo framework's architecture, showing which files are responsible for what and how the code is designed for scalability.

## Overview: Two-Phase Architecture

```mermaid
graph TB
    subgraph "USER CODE"
        UM[models/*.py<br/>@datamodel]
        UO[operations/*.py<br/>@operation]
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

    subgraph "GENERATED CODE"
        CLI[./main<br/>Project CLI]
        API[generated_api.py]
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
    I --> CLI
    C --> API
    C --> UI
    C --> WF
```

---

## Phase 1: Analysis - File Responsibilities

### Discovery Layer
**Purpose**: Find and extract metadata from user code

```mermaid
graph LR
    subgraph "core/analysis/discovery/"
        AST[ast_scanner.py<br/>Static analysis<br/>No imports needed]
        IMP[import_scanner.py<br/>Runtime discovery<br/>Import decorators]
    end

    subgraph "User Code"
        UC[models/*.py<br/>operations/*.py]
    end

    subgraph "core/analysis/"
        DEC[decorators.py<br/>@datamodel<br/>@operation]
        REG[registries.py<br/>ModelRegistry<br/>OperationRegistry]
    end

    UC --> AST
    UC --> IMP
    DEC --> IMP
    AST --> REG
    IMP --> REG
```

**File Responsibilities**:
- **decorators.py** (80 lines): Defines `@datamodel` and `@operation` decorators
- **ast_scanner.py** (280 lines): Static analysis of Python files without imports
- **import_scanner.py** (150 lines): Runtime discovery by importing decorated code
- **registries.py** (250 lines): Stores discovered models and operations

**Scalability**: Discovery is O(n) where n = number of Python files. Can run in parallel for different directories.

---

### Validation Layer
**Purpose**: Lint and validate discovered code

```mermaid
graph LR
    subgraph "core/analysis/registries.py"
        MR[ModelRegistry]
        OR[OperationRegistry]
    end

    subgraph "core/analysis/validation/"
        L[linter.py<br/>Anti-pattern detection<br/>Type checking]
        DH[doc_helper.py<br/>Documentation validation]
    end

    subgraph "Output"
        ERR[List of errors]
    end

    MR --> L
    OR --> L
    L --> DH
    DH --> ERR
```

**File Responsibilities**:
- **linter.py** (300 lines): Validates models/operations for anti-patterns
- **doc_helper.py** (100 lines): Ensures proper documentation

**Scalability**: Validation is O(n) where n = registry size. Each model/operation validated independently.

---

### Graph Layer
**Purpose**: Build dependency graphs and visualizations

```mermaid
graph TD
    subgraph "core/analysis/registries.py"
        REG[ModelRegistry<br/>OperationRegistry]
    end

    subgraph "core/analysis/graphs/"
        GG[graph_generator.py<br/>Mermaid diagrams]
        H[hierarchy.py<br/>Operation hierarchy]
    end

    subgraph "core/analysis/dataflow/"
        DF[dataflow.py<br/>Dependency DAG]
        SA[sync_async.py<br/>Async analysis]
    end

    subgraph "Output"
        MMD[docs/*.mmd<br/>Mermaid files]
    end

    REG --> DF
    REG --> GG
    REG --> H
    DF --> SA
    GG --> MMD
    H --> MMD
```

**File Responsibilities**:
- **dataflow.py** (200 lines): Builds DAG, detects dependencies
- **sync_async.py** (120 lines): Analyzes sync/async compatibility
- **graph_generator.py** (400 lines): Generates Mermaid diagrams
- **hierarchy.py** (180 lines): Builds operation hierarchy trees

**Scalability**: Graph building is O(v + e) where v = models, e = operations. DAG enables parallel execution planning.

---

## Phase 2: Generation - File Responsibilities

### Init Phase
**Purpose**: First-time project setup

```mermaid
graph TD
    subgraph "core/generation/init/"
        PI[project_init.py<br/>Create .pulpo.yml<br/>Setup directories]
        CG[cli_generator.py<br/>Generate ./main<br/>644 lines]
        GG[graph_generator.py<br/>Initial graphs]
    end

    subgraph "core/config/"
        CM[manager.py<br/>ConfigManager]
        S[settings.py]
        UC[user_config.py]
    end

    subgraph "Output"
        YML[.pulpo.yml]
        CLI[./main]
        DOCS[docs/*.mmd]
    end

    PI --> CM
    PI --> CG
    PI --> GG
    CM --> YML
    CG --> CLI
    GG --> DOCS
```

**File Responsibilities**:
- **project_init.py** (850 lines): Orchestrates project initialization
- **cli_generator.py** (644 lines): Generates complete operational CLI with 30+ commands
- **manager.py** (300 lines): Manages .pulpo.yml configuration
- **settings.py** (150 lines): Global settings
- **user_config.py** (100 lines): User-specific configuration

**Scalability**: Init is one-time only. Fast (< 1 second).

---

### Compile Phase
**Purpose**: Generate production code

```mermaid
graph TD
    subgraph "core/generation/"
        CO[codegen.py<br/>Orchestrator<br/>220 lines]
        B[base.py<br/>CodeGenerator<br/>Hash-based changes]
    end

    subgraph "core/generation/compile/"
        AG[api_generator.py<br/>FastAPI routes<br/>336 lines]
        UG[ui_generator.py<br/>TypeScript/React<br/>521 lines]
        PC[prefect_codegen.py<br/>Prefect flows]
        WC[compiler.py<br/>Workflow compiler]
    end

    subgraph "Output"
        API[generated_api.py]
        UI[generated_frontend/]
        PF[prefect_flows.py]
    end

    CO --> B
    CO --> AG
    CO --> UG
    CO --> PC
    CO --> WC
    AG --> API
    UG --> UI
    PC --> PF
    WC --> PF
```

**File Responsibilities**:
- **codegen.py** (220 lines): Main orchestrator, calls all generators
- **base.py** (150 lines): Base class with hash-based change detection
- **api_generator.py** (336 lines): Generates FastAPI routes from models/operations
- **ui_generator.py** (521 lines): Generates TypeScript config + React/Refine pages
- **prefect_codegen.py** (250 lines): Generates Prefect flow definitions
- **compiler.py** (300 lines): Compiles workflows into executable Prefect flows

**Scalability**:
- Hash-based regeneration: Only regenerate changed files
- Each generator is independent: Can run in parallel
- O(n) generation time where n = registry size
- Typical compile time: 4 seconds for 100 models + 200 operations

---

## CLI Architecture - Command Flow

```mermaid
graph TD
    subgraph "Framework CLI (pulpo)"
        FC[core/cli/interface.py<br/>444 lines]

        subgraph "Analysis Commands"
            LC[list-models<br/>list-operations]
            IC[inspect model/operation]
            VC[validate]
            DC[draw-graphs]
        end

        subgraph "Generation Commands"
            INIT[init]
            COMP[compile]
        end
    end

    subgraph "Project CLI (./main)"
        PC[Generated by cli_generator.py<br/>644 lines template]

        subgraph "Service Commands"
            SC[up/down/restart<br/>logs/status/health]
        end

        subgraph "Operation Commands"
            OC[ops list<br/>ops run<br/>ops show]
        end

        subgraph "Database Commands"
            DC2[db init/seed<br/>db backup/restore]
        end

        subgraph "Prefect Commands"
            PFC[prefect start/stop<br/>prefect logs]
        end
    end

    FC --> LC
    FC --> IC
    FC --> VC
    FC --> DC
    FC --> INIT
    FC --> COMP

    INIT --> PC
    COMP --> PC

    PC --> SC
    PC --> OC
    PC --> DC2
    PC --> PFC
```

**Scalability**:
- Framework CLI: Pure Python, no dependencies on generated code
- Project CLI: Generated per-project, includes only relevant commands
- Clear separation: Framework analyzes, project operates

---

## Service Layer - Docker Services

```mermaid
graph TD
    subgraph "Generated Code (run_cache/)"
        API[generated_api.py<br/>FastAPI app]
        UI[generated_frontend/<br/>React/Refine]
        PF[prefect_flows.py<br/>Workflow definitions]
    end

    subgraph "Docker Services"
        subgraph "Data Layer"
            MONGO[MongoDB<br/>Port: 27017]
        end

        subgraph "Application Layer"
            APIS[API Service<br/>Port: 8000]
            UIS[UI Service<br/>Port: 3000]
        end

        subgraph "Orchestration Layer"
            PS[Prefect Server<br/>Port: 4200]
            PW[Prefect Worker]
        end
    end

    subgraph "Project CLI"
        CLI[./main up/down<br/>Service management]
    end

    CLI --> APIS
    CLI --> UIS
    CLI --> PS
    CLI --> PW
    CLI --> MONGO

    API --> APIS
    UI --> UIS
    PF --> PW

    APIS --> MONGO
    PW --> MONGO
    PW --> PS
```

**Scalability**:
- Services are stateless (data in MongoDB)
- Horizontal scaling: Add more API/Worker containers
- Port auto-detection: No conflicts when running multiple projects
- Docker Compose: Easy multi-service orchestration

---

## Data Flow Example

```mermaid
sequenceDiagram
    participant User
    participant CLI as pulpo CLI
    participant Reg as Registries
    participant Gen as Generators
    participant PCli as ./main CLI
    participant Docker

    User->>CLI: pulpo list-models
    CLI->>Reg: Discover models/
    Reg-->>CLI: [User, Product]
    CLI-->>User: Display models

    User->>CLI: pulpo compile
    CLI->>Reg: Load registries
    CLI->>Gen: Generate all
    Gen->>Gen: Hash check (changed?)
    Gen-->>CLI: API, UI, CLI, Workflows
    CLI-->>User: ✓ Compiled

    User->>PCli: ./main up
    PCli->>Docker: docker-compose up
    Docker-->>PCli: 5 services running
    PCli-->>User: ✓ Services started

    User->>PCli: ./main ops run create_user
    PCli->>Docker: Call API
    Docker-->>PCli: User created
    PCli-->>User: ✓ Success
```

---

## Scalability Design Principles

### 1. **Modular Generators**
Each generator is independent:
- **api_generator.py**: 336 lines, generates API only
- **ui_generator.py**: 521 lines, generates UI only
- **prefect_codegen.py**: 250 lines, generates workflows only

**Benefit**: Can add new generators (GraphQL, gRPC, etc.) without touching existing code.

### 2. **Registry Pattern**
Central storage for discovered metadata:
- **ModelRegistry**: All @datamodel classes
- **OperationRegistry**: All @operation functions

**Benefit**: Single source of truth. All generators read from registries.

### 3. **Hash-Based Regeneration**
Only regenerate changed files:
```python
# base.py
def needs_regeneration(self, output_file: Path) -> bool:
    current_hash = self.get_metadata_hash()
    stored_hash = self.load_hash(output_file)
    return current_hash != stored_hash
```

**Benefit**: Fast incremental builds. Typical recompile: < 1 second if no changes.

### 4. **Two Discovery Methods**
- **AST Scanner**: Static analysis, no imports
- **Import Scanner**: Runtime discovery

**Benefit**: Works even if user code has import errors. AST scanner is faster.

### 5. **DAG-Based Execution**
Operations form a directed acyclic graph:
```
create_user → validate_user → send_email
              ↓
            save_to_db
```

**Benefit**: Parallel execution, dependency tracking, cycle detection.

### 6. **CLI Separation**
- **Framework CLI**: Analysis + generation (stateless)
- **Project CLI**: Operations + services (stateful)

**Benefit**: Framework never needs Docker. Project CLI is self-contained.

---

## File Size Distribution

### Large Files (> 400 lines)
- **cli_generator.py**: 644 lines (generates full project CLI)
- **ui_generator.py**: 521 lines (TypeScript + React generation)
- **graph_generator.py**: 400 lines (Mermaid diagrams)

### Medium Files (200-400 lines)
- **api_generator.py**: 336 lines
- **linter.py**: 300 lines
- **manager.py**: 300 lines
- **compiler.py**: 300 lines
- **ast_scanner.py**: 280 lines
- **registries.py**: 250 lines
- **prefect_codegen.py**: 250 lines
- **codegen.py**: 220 lines (orchestrator only - was 1230 lines!)
- **dataflow.py**: 200 lines

### Small Files (< 200 lines)
- **base.py**: 150 lines
- **import_scanner.py**: 150 lines
- **settings.py**: 150 lines
- **sync_async.py**: 120 lines
- **hierarchy.py**: 180 lines
- **doc_helper.py**: 100 lines
- **user_config.py**: 100 lines
- **decorators.py**: 80 lines

**Design**: No file > 650 lines. Average file size: ~250 lines.

---

## Performance Characteristics

### Discovery
- **Time**: O(n) where n = number of Python files
- **Typical**: 100 files in ~500ms
- **Parallelizable**: Yes (different directories)

### Graph Building
- **Time**: O(v + e) where v = models, e = operations
- **Typical**: 100 models + 200 ops in ~200ms
- **Parallelizable**: No (needs complete graph)

### Generation
- **Time**: O(n) where n = registry size
- **Typical**: 100 models + 200 ops
  - API: ~1s
  - UI: ~2s
  - Workflows: ~1s
  - **Total**: ~4s
- **Parallelizable**: Yes (generators are independent)

### Hash Checking
- **Time**: O(1) per file
- **Typical**: < 100ms for all files
- **Benefit**: Skip generation if unchanged

---

## Extension Points

### Add Custom Generator
```python
# core/generation/compile/my_generator.py
from ..base import CodeGenerator

class MyGenerator(CodeGenerator):
    def generate(self) -> Path:
        # Your generation logic
        return output_path
```

### Add Custom Validator
```python
# core/analysis/validation/my_validator.py
from .linter import Validator

class MyValidator(Validator):
    def validate(self, registry):
        # Your validation logic
        return errors
```

### Add Custom Discovery
```python
# core/analysis/discovery/my_scanner.py
class MyScanner:
    def discover(self, path: Path):
        # Your discovery logic
        yield model_metadata
```

---

## Summary

### File Responsibility Matrix

| Phase | Layer | Files | Responsibility | Lines |
|-------|-------|-------|----------------|-------|
| Analysis | Discovery | decorators.py, ast_scanner.py, import_scanner.py | Find @datamodel/@operation | 510 |
| Analysis | Registry | registries.py | Store metadata | 250 |
| Analysis | Validation | linter.py, doc_helper.py | Validate code | 400 |
| Analysis | Graphs | graph_generator.py, hierarchy.py, dataflow.py, sync_async.py | Build DAG, visualize | 900 |
| Generation | Init | project_init.py, cli_generator.py | First-time setup | 1494 |
| Generation | Compile | codegen.py, base.py, api_generator.py, ui_generator.py, prefect_codegen.py, compiler.py | Generate code | 1756 |
| Config | - | manager.py, settings.py, user_config.py | Configuration | 550 |
| CLI | Framework | interface.py | Analysis + generation commands | 444 |
| CLI | Project | Generated by cli_generator.py | Operational commands | 644 (template) |

**Total Framework Code**: ~5,500 lines
**Generated Code per Project**: ~2,000-10,000 lines (depends on models/operations)

### Scalability Summary

✅ **Modular**: Each file has single responsibility
✅ **Parallel**: Generators can run concurrently
✅ **Incremental**: Hash-based change detection
✅ **Extensible**: Easy to add new generators/validators
✅ **Performance**: O(n) operations, typical compile < 5s
✅ **Clean Separation**: Framework code never runs in production

---

## Next Steps

- [CLI Architecture](04_CLI_Architecture.md) - Detailed CLI command reference
- [Architecture](03_Architecture.md) - High-level architecture overview
- [Core Concepts](02_Core_Concepts.md) - Decorators and registries
