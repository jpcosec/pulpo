# CLI Architecture: Main Entrypoint Discovery with Smart Compilation

## Overview

The `CLI` class is the main interface to the Pulpo framework. It's designed to be:
- **Explicit**: Discovers decorators via main.py imports only (not file scanning)
- **Smart**: Only generates required artifacts when needed
- **Flexible**: Supports inspection without full compilation
- **Modular**: Users can integrate operations directly without full stack

---

## Discovery Architecture

### Primary Method: Main Entrypoint Imports

Discovery happens exclusively through **explicit imports in main.py**:

```python
# main entrypoint file (e.g., ./main)
#!/usr/bin/env python
from models.user import User              # @datamodel decorator executes
from models.post import Post              # @datamodel decorator executes
from operations.create_user import create_user  # @operation decorator executes
from operations.publish import publish_post     # @operation decorator executes

from core import CLI

# When main.py is imported, all decorators execute and register models/operations
# Registry is populated at import time (no scanning needed)

if __name__ == "__main__":
    cli = CLI()  # CLI() reads already-populated registries
    cli.compile()
```

**Key Points:**
- Only imports in main.py trigger decorator registration
- File scanning is NOT performed automatically
- Registry state is built at import time, reused by CLI
- Same discovery method applies to all example projects

### Secondary Method: File Scanning (Debug/Bootstrap)

File scanning is available for debugging and generating a bootstrap main.py:

```python
from core.discovery import discover_via_scan

# Scan entire codebase (slower, for debugging)
models, operations = discover_via_scan("./models", "./operations")

# Or use to generate main.py as bootstrap:
# python -m core.discovery --generate-main
```

**When to use:**
- Debugging: "What did the file scanner find?"
- Bootstrapping: Generating initial main.py when starting new project
- CI/CD: Validating all decorators are properly imported

---

## CLI Instantiation & Registry Population

```python
from core import CLI

# Before CLI instantiation:
# 1. main.py is imported (triggers all @datamodel/@operation decorators)
# 2. Registries are populated automatically by decorators
# 3. Registry state persists for the Python process

cli = CLI()  # On instantiation:
# 1. Reads already-populated registries (no discovery step)
# 2. Does NOT scan files
# 3. Does NOT create run_cache/ or generate artifacts
```

**Key Point:** Discovery happens at import time, not CLI instantiation. CLI uses the registries that were populated by decorators.

---

## CLI Operations

### Category 1: Inspection (No run_cache Required)

These operations inspect decorators directly without needing compilation:

#### `list_models()`
```python
cli.list_models()  # Returns list of model names
# Works immediately, uses decorator metadata
```

#### `list_operations()`
```python
cli.list_operations()  # Returns list of operation names
# Works immediately, uses decorator metadata
```

#### `inspect_model(name: str)`
```python
cli.inspect_model("Job")  # Returns model metadata and schema
# Works immediately, displays:
# - Model name, description
# - Fields and types
# - Relationships (if defined)
```

#### `inspect_operation(name: str)`
```python
cli.inspect_operation("search_jobs")  # Returns operation metadata
# Works immediately, displays:
# - Operation name, category, description
# - Input/output Pydantic schemas
# - Async status
# - Dependencies inferred from types
```

#### `draw_graphs()` / `draw_dataflow()`
```python
cli.draw_graphs()  # Generates data relationship graphs
# Works immediately - scans decorators to build graph
# Output: SVG/PNG in run_cache/graphs/ (creates folder if needed)
```

#### `draw_operationflow()` / `draw_flowgraph()`
```python
cli.draw_operationflow()  # Generates operation flow graphs
# Works immediately - parses operation hierarchy
# Output: SVG/PNG in run_cache/graphs/
```

#### `docs()`
```python
cli.docs()  # Generates documentation from decorators
# Works immediately
# Output: Markdown files in run_cache/docs/
```

#### `check_version()`
```python
cli.check_version()  # Checks for version mismatches
# Works immediately
# Compares framework version with other components
```

#### `get_model_registry()` / `get_operation_registry()`
```python
registry = cli.get_model_registry()
registry = cli.get_operation_registry()
# Returns fresh registries, works immediately
```

#### `summary()`
```python
cli.summary()  # Show project status
# Works immediately
# Displays number of models, operations, and registries
```

---

## Help System & Documentation

### Framework-Level Help

The Pulpo CLI provides comprehensive framework documentation:

```bash
# List all available framework documentation
pulpo help

# Get specific framework documentation
pulpo help datamodel          # @datamodel decorator reference
pulpo help operation          # @operation decorator reference
pulpo help cli                # CLI architecture (this file)
pulpo help architecture       # Framework architecture overview
pulpo help orchestration      # Hierarchical naming and Prefect flows
```

### Project-Level Help

Each project CLI includes help for its models and operations:

```bash
# List all available documentation (models, operations, framework)
./main help

# Get model documentation (with fields, CRUD endpoints, relationships)
./main help model User
./main help model Post

# Get operation documentation (with inputs, outputs, API endpoint)
./main help operation users.create
./main help operation posts.publish

# Get framework documentation (same as pulpo framework docs)
./main help framework datamodel
./main help framework architecture
```

### Documentation Extraction

The `DocHelper` class extracts documentation from multiple sources:

```python
from core.doc_helper import DocHelper

helper = DocHelper()

# Framework documentation (from .md files in docs/)
framework_doc = helper.get_framework_doc("datamodel")

# Model documentation (from @datamodel decorator + class docstring)
model_doc = helper.get_model_docs("User")

# Operation documentation (from @operation decorator + function docstring)
op_doc = helper.get_operation_docs("users.create")

# List all available documentation
all_docs = helper.list_all_docs()
# Returns:
# {
#     "framework": ["datamodel", "operation", "cli", ...],
#     "models": ["User", "Post", "Comment", ...],
#     "operations": ["users.create", "posts.publish", ...]
# }
```

**What gets extracted:**

For Models:
- Class docstring and @datamodel description
- Field names, types, and descriptions
- Metadata (tags, searchable fields, sortable fields)
- Auto-generated CRUD endpoints

For Operations:
- Function docstring and @operation description
- Input/output Pydantic schemas
- Category and metadata
- Auto-generated API endpoint
- Auto-generated CLI command

### Registry Auditing with registry.json

After compilation, `.run_cache/registry.json` contains the complete discovery results:

```json
{
  "timestamp": "2024-03-15T10:30:45.123456",
  "discovery_method": "main.py entrypoint",
  "models": [
    {
      "name": "User",
      "description": "User account",
      "fields": {
        "name": "str",
        "email": "str",
        "created_at": "datetime"
      }
    }
  ],
  "operations": [
    {
      "name": "users.create",
      "category": "users",
      "description": "Create new user",
      "input_schema": "UserCreateInput",
      "output_schema": "UserCreateOutput"
    }
  ]
}
```

**Use cases:**
- CI/CD validation: "Were all decorators properly imported?"
- Auditing: "What was the exact state when this was generated?"
- Debugging: "Which models/operations were discovered?"

### Category 2: Full Stack (Requires run_cache)

These operations require compilation. They automatically create `run_cache/` if it doesn't exist.

#### `compile()`
```python
cli.compile()  # Main compilation step
# Creates: run_cache/ (if doesn't exist)
# Generates:
# - generated_api.py (FastAPI routes)
# - generated_ui_config.ts (TypeScript UI config)
# - generated_database.py (Database models)
# - orchestration/ folder (Prefect flows from hierarchy)
# - docker/ folder (Dockerfile templates)
# - models_graph.svg, operations_graph.svg (diagrams)
# Idempotent - safe to call multiple times
```

#### `build()`
```python
cli.build()  # Build Docker images
# Requires: run_cache/ must exist (calls compile() first if needed)
# Generates:
# - Docker images for API, UI, Prefect
# - docker-compose.yml
```

#### `api()` / `serve_api()`
```python
cli.api()  # Serve FastAPI
# Requires: run_cache/ and generated_api.py
# Auto-calls compile() if run_cache/ missing
# Starts FastAPI server on port 8000
```

#### `init()`
```python
cli.init()  # Initialize database
# Requires: run_cache/ and generated_database.py
# Auto-calls compile() if run_cache/ missing
# Creates database connection and indexes
```

#### `prefect()` / `orchestrate()`
```python
cli.prefect()  # Run Prefect orchestration
# Requires: run_cache/orchestration/ with Prefect flows
# Auto-calls compile() if run_cache/ missing
# Starts Prefect server with auto-generated flows
```

#### `interact()` / `shell()`
```python
cli.interact()  # Interactive Python shell with access to models/operations
# Requires: run_cache/
# Auto-calls compile() if run_cache/ missing
```

#### `clean()`
```python
cli.clean()  # Remove generated artifacts
# Deletes run_cache/ folder
# Safe - compile() will regenerate if needed
```

---

## Smart run_cache Creation

When an operation that requires `run_cache/` is called:

```python
# User code
cli = CLI()

# This normally would require run_cache/
cli.api()

# Framework behavior:
# 1. Check if run_cache/ exists
# 2. If not: call compile() automatically (silent)
# 3. Then: start API server
```

**No explicit compile() call needed** - it happens automatically when required.

---

## Compilation Strategy

The `compile()` operation is **idempotent and safe**:

```python
# Safe to call multiple times
cli.compile()
cli.compile()  # Just overwrites generated files
cli.compile()  # No errors, same result

# Safe to call before any operation that needs it
cli.api()      # Auto-calls compile() if needed
cli.prefect()  # Auto-calls compile() if needed
```

**Generated files in run_cache/**:
- `generated_api.py` - FastAPI with CRUD routes
- `generated_ui_config.ts` - UI resource configuration
- `generated_database.py` - Beanie document models
- `orchestration/` - Prefect @flow and @task files
- `graphs/` - SVG/PNG relationship and flow diagrams
- `docs/` - Auto-generated documentation
- `Dockerfile` - Container template
- `docker-compose.yml` - Multi-container orchestration

---

## User Integration Patterns

### Pattern 1: Full Stack (Simplest)

```python
from pulpo import CLI, datamodel, operation
from pydantic import BaseModel

@datamodel(name="Job")
class Job:
    title: str
    company: str

@operation(name="search_jobs")
async def search(keywords: str):
    return []

# Main entrypoint
if __name__ == "__main__":
    cli = CLI()

    # Inspect (no compilation needed)
    cli.list_models()
    cli.list_operations()

    # Run full stack
    cli.compile()
    cli.build()
    cli.api()  # Starts server
    # OR
    cli.prefect()  # Starts Prefect with auto-generated flows
```

### Pattern 2: Inspection Only

```python
cli = CLI()

# Immediate inspection - no compilation
models = cli.list_models()
operations = cli.list_operations()
cli.inspect_operation("search_jobs")
cli.draw_graphs()  # Generate diagrams without full compilation
```

### Pattern 3: Direct Operation Integration

User creates own CLI-like interface without full framework overhead:

```python
from pulpo.core.registries import OperationRegistry
from pulpo import datamodel, operation

@operation(name="fetch_data")
async def fetch():
    return {"data": []}

# User's custom CLI
registry = OperationRegistry()
op_info = registry.get("fetch_data")
result = await op_info.func()  # Invoke directly
```

### Pattern 4: Programmatic Control

```python
cli = CLI()

# Inspect before deciding what to do
ops = cli.get_operation_registry().get_all()

if "my_operation" in ops:
    cli.compile()  # Generate files
    cli.api()      # Start API if that operation exposed as endpoint
```

---

## Hierarchy-Based Orchestration (Extended Proposal C)

When using hierarchical operation names, `compile()` automatically generates Prefect flows:

```python
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(): ...

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(): ...

@operation(name="scraping.merge")
async def merge(stepstone, linkedin): ...

cli = CLI()
cli.compile()  # Creates run_cache/orchestration/

# Generated structure:
# run_cache/orchestration/
# ├── scraping_flow.py      # @flow with parallel fetches
# ├── scraping_merge.py     # Merge task
# └── __init__.py
```

Prefect flows:
- Parse hierarchy from operation names
- Create nested @flow structure
- Detect same-level parallelization (fetch operations)
- Auto-inject dependencies from operation inputs
- Wrap sync functions with run_in_executor

---

## CLI Method Summary

| Method | Requires run_cache | Creates run_cache | Purpose |
|--------|-------------------|------------------|---------|
| `list_models()` | ❌ | ❌ | List decorated models |
| `list_operations()` | ❌ | ❌ | List decorated operations |
| `inspect_model()` | ❌ | ❌ | Get model metadata |
| `inspect_operation()` | ❌ | ❌ | Get operation metadata |
| `draw_graphs()` | ❌ | ✅ | Generate diagrams |
| `draw_operationflow()` | ❌ | ✅ | Generate operation graphs |
| `docs()` | ❌ | ✅ | Generate documentation |
| `check_version()` | ❌ | ❌ | Check version compatibility |
| `compile()` | ❌ | ✅ | Generate all artifacts |
| `build()` | ✅ | ✅ | Build Docker images |
| `api()` | ✅ | ✅ | Serve FastAPI |
| `init()` | ✅ | ✅ | Initialize database |
| `prefect()` | ✅ | ✅ | Run Prefect orchestration |
| `interact()` | ✅ | ✅ | Interactive shell |
| `clean()` | ✓ (optional) | ❌ | Delete run_cache |

---

## Error Handling

Operations gracefully handle missing run_cache:

```python
cli.api()  # run_cache/ doesn't exist

# Framework behavior:
# 1. Silently calls compile()
# 2. Generates all required files
# 3. Starts API server
# 4. User sees: "Starting API server on http://localhost:8000"
```

Invalid operations fail with clear messages:

```python
cli.inspect_operation("nonexistent")
# Error: Operation 'nonexistent' not found in registry
# Available operations: [list of operations]
```

---

## Lifecycle Example

```python
from pulpo import CLI, datamodel, operation

@datamodel(name="User")
class User:
    name: str

@operation(name="create_user")
async def create(name: str):
    return {"id": "123", "name": name}

# Day 1: Inspection
cli = CLI()
print(cli.list_models())      # ["User"] - immediate
print(cli.list_operations())  # ["create_user"] - immediate

# Day 2: First full run
cli.compile()     # Generate code (once)
cli.build()       # Build images (once)
cli.api()         # Start server (interactive)

# Day 3: Modify code
# (User edits decorators or operation logic)
cli2 = CLI()
cli2.compile()    # Regenerates with new code
cli2.api()        # Uses updated code

# Day 4: Use Prefect instead
cli3 = CLI()
cli3.prefect()    # Auto-calls compile(), starts Prefect

# Day 5: Just inspect
cli4 = CLI()
cli4.draw_graphs()    # No compile needed
cli4.check_version()  # No compile needed
```

---

## Configuration Options (Future)

CLI can accept configuration:

```python
cli = CLI(
    run_cache_dir="./generated",     # Custom path
    auto_compile=True,               # Auto-compile before operations
    strict_mode=False,               # Warnings vs errors
    prefect_server="http://localhost:4200"  # Prefect config
)
```

---

## Summary

- **Dynamic discovery**: Fresh on each instantiation
- **Smart compilation**: Auto-creates run_cache only when needed
- **Flexible**: Works with just decorators (no compilation) or full stack
- **User-friendly**: No manual "compile before use" steps
- **Extensible**: Users can integrate operations directly or use full CLI

The CLI is the single entry point to all framework functionality.
