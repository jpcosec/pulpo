# CLI Architecture - Separation of Concerns

## Overview

Pulpo has **two distinct CLIs** with different responsibilities:

1. **Framework CLI** (`core/cli/`) - Analysis and code generation
2. **Project CLI** (`run_cache/cli/<project>`) - Operation and services management

---

## Framework CLI (`pulpo` command)

**Location**: `core/cli/interface.py`

**Purpose**: Provide analysis and generation capabilities that don't require generated code.

**Installation**:
```bash
pip install pulpo
# or
pip install -e .  # for development
```

**Usage**:
```bash
pulpo <command>
```

---

### Commands

#### ANALYSIS (Phase 1 - Standalone)

These commands work **without** generating any code. They inspect user's Python files.

```bash
# Discovery
pulpo list-models              # List all @datamodel classes discovered
pulpo list-operations          # List all @operation functions discovered

# Inspection
pulpo inspect model <name>     # Show model details (fields, types, metadata)
pulpo inspect operation <name> # Show operation details (inputs, outputs, dependencies)

# Validation
pulpo validate                 # Run linter on models and operations
pulpo validate --strict        # Strict mode with all checks

# Visualization
pulpo draw-graphs              # Generate Mermaid diagrams (docs/*.mmd)
pulpo show-flow <operation>    # Show data flow for specific operation
pulpo show-hierarchy           # Show operation hierarchy tree
```

**How it works**:
- Uses **AST scanning** (no imports needed) or **import-based discovery**
- Reads from `models/` and `operations/` directories
- Populates `ModelRegistry` and `OperationRegistry`
- Analyzes dependencies and builds DAG
- No code generation, pure analysis

---

#### GENERATION (Phase 2)

These commands **generate code** but don't execute it.

```bash
# Init - First time setup
pulpo init                     # Generate:
                               #   - CLI executable (./main)
                               #   - Config (.pulpo.yml)
                               #   - Initial graphs (docs/)

# Compile - Full code generation
pulpo compile                  # Generate:
                               #   - API (run_cache/generated_api.py)
                               #   - UI (run_cache/generated_frontend/)
                               #   - Workflows (run_cache/prefect_flows.py)
                               #   - CLI (run_cache/cli/<project>)
                               #   - Graphs (docs/)

# Compile specific targets
pulpo compile --api-only       # Generate only API
pulpo compile --ui-only        # Generate only UI
pulpo compile --workflows-only # Generate only Prefect workflows
```

**Output**: All generated code goes to `run_cache/` in the **project directory**.

---

#### HELP & INFO

```bash
pulpo --version                # Show Pulpo version
pulpo --help                   # Show help
pulpo help <command>           # Help for specific command
pulpo config show              # Show current configuration
pulpo config validate          # Validate .pulpo.yml
```

---

### Framework CLI Responsibilities

✅ **Should Do**:
- Discover models and operations
- Inspect metadata
- Validate code (linting)
- Generate graphs
- Generate CLI executable
- Generate code artifacts (API, UI, workflows)

❌ **Should NOT Do**:
- Start services (Docker containers)
- Execute operations
- Manage database
- Handle Prefect workflows
- Serve API/UI locally

---

## Project CLI (`./main` command)

**Location**: `run_cache/cli/<project_name>` (generated)

**Purpose**: Provide operational commands for the specific project.

**Generation**:
```bash
pulpo init              # Creates ./main
# or
pulpo compile           # Regenerates ./main
```

**Usage**:
```bash
./main <command>
```

---

### Commands

#### SERVICES MANAGEMENT

Manage the 5 Docker services (MongoDB, API, UI, Prefect Server, Prefect Worker).

```bash
# Lifecycle
./main up                      # Start all services (docker-compose up)
./main down                    # Stop all services (docker-compose down)
./main restart                 # Restart all services
./main stop                    # Stop without removing containers

# Monitoring
./main status                  # Show status of all 5 services
./main health                  # Health check for all services
./main logs                    # Show logs (all services)
./main logs --service api      # Logs for specific service
./main logs --follow           # Follow logs in real-time

# Individual services
./main api up                  # Start only API
./main ui up                   # Start only UI
./main db up                   # Start only MongoDB
```

---

#### OPERATIONS EXECUTION

Execute user-defined `@operation` functions.

```bash
# List operations
./main ops list                # List all available operations
./main ops list --category <cat> # Filter by category

# Execute operation
./main ops run <operation_name> \
  --input '{"key": "value"}'   # Execute with JSON input

./main ops run <operation_name> \
  --input-file data.json       # Execute with file input

# Show operation details
./main ops show <operation_name> # Show inputs, outputs, description
```

---

#### DATABASE MANAGEMENT

Manage MongoDB database for the project.

```bash
# Initialization
./main db init                 # Initialize schema and indexes
./main db seed                 # Seed test data
./main db drop                 # Drop all collections (dangerous!)

# Backup & Restore
./main db backup               # Backup to backups/
./main db backup --file mybackup.gz
./main db restore <backup>     # Restore from backup

# Utilities
./main db shell                # Open MongoDB shell
./main db status               # Show DB status (size, collections)
```

---

#### PREFECT WORKFLOWS

Manage Prefect orchestration.

```bash
# Server management
./main prefect start           # Start Prefect server
./main prefect stop            # Stop Prefect server
./main prefect restart         # Restart Prefect server
./main prefect ui              # Open Prefect UI in browser

# Workflow execution
./main prefect run <flow_name> # Execute a workflow
./main prefect schedule <flow> # Schedule a workflow

# Monitoring
./main prefect logs            # View Prefect logs
./main prefect status          # Show worker/server status
```

---

#### DEVELOPMENT

Local development commands (without Docker).

```bash
# Run services locally
./main api --port 8000         # Run API locally (uvicorn)
./main ui --port 3000          # Run UI dev server locally

# Development utilities
./main shell                   # Open Python shell with project context
./main notebook                # Start Jupyter notebook
```

---

#### REGENERATION

Trigger code regeneration (delegates to framework CLI).

```bash
./main compile                 # Calls: pulpo compile
./main compile --api-only      # Regenerate only API
```

---

### Project CLI Responsibilities

✅ **Should Do**:
- Start/stop Docker services
- Execute operations
- Manage database (init, seed, backup)
- Handle Prefect workflows
- Serve API/UI locally (dev mode)
- Show logs and status

❌ **Should NOT Do**:
- Analyze models/operations (use framework CLI)
- Generate code artifacts (delegates to framework CLI)
- Validate code (use framework CLI)

---

## Interaction Flow

### First Time Setup

```bash
# User creates project structure
mkdir my-project && cd my-project
mkdir models operations

# User writes code
vim models/user.py              # @datamodel

# User analyzes with framework CLI
pulpo list-models               # ✓ Found: User
pulpo validate                  # ✓ All checks pass
pulpo draw-graphs               # Generates docs/

# User generates project CLI
pulpo init                      # Creates:
                                #   - ./main (executable)
                                #   - .pulpo.yml

# User generates full code
pulpo compile                   # Generates run_cache/
```

---

### Daily Development

```bash
# User starts services with PROJECT CLI
./main up                       # 5 Docker containers start

# User executes operations
./main ops run create_user --input '{"email":"test@test.com"}'

# User checks logs
./main logs --follow

# User modifies code
vim models/user.py              # Add new field

# User validates with FRAMEWORK CLI
pulpo validate                  # Check for errors

# User regenerates with PROJECT CLI
./main compile                  # Internally calls: pulpo compile

# User restarts services
./main restart
```

---

### Debugging & Analysis

```bash
# User encounters issue with operation
pulpo inspect operation create_user  # Framework CLI: Show details
pulpo show-flow create_user          # Framework CLI: Show data flow
pulpo draw-graphs                    # Framework CLI: Regenerate graphs

# User checks service status
./main status                        # Project CLI: Service status
./main logs --service api            # Project CLI: API logs
./main health                        # Project CLI: Health check
```

---

## Implementation Plan

### Phase 1: Documentation ✅
- Create this document
- Define clear boundaries
- Document all commands

### Phase 2: Refactor Framework CLI
**File**: `core/cli/interface.py`

**Keep**:
- `list_models()`
- `list_operations()`
- `inspect_model()`
- `inspect_operation()`
- `validate()`
- `draw_graphs()`
- `show_flow()`
- `init()`
- `compile()`

**Remove** (move to generated CLI):
- `api()`
- `up()`, `down()`, `restart()`
- `logs()`
- `status()`
- `health()`
- `db()`
- `prefect()`

---

### Phase 3: Enhance CLI Generator
**File**: `core/generation/init/cli_generator.py`

**Add commands**:
- Services: `up`, `down`, `restart`, `logs`, `status`, `health`
- Operations: `ops list`, `ops run`, `ops show`
- Database: `db init`, `db seed`, `db backup`, `db restore`, `db shell`
- Prefect: `prefect start`, `prefect stop`, `prefect run`, `prefect logs`
- Development: `api`, `ui`, `shell`, `notebook`
- Regeneration: `compile` (calls `pulpo compile`)

---

## Command Reference Tables

### Framework CLI (`pulpo`)

| Command | Category | Output | Runs Without Generated Code |
|---------|----------|--------|------------------------------|
| `list-models` | Analysis | Terminal | ✅ Yes |
| `list-operations` | Analysis | Terminal | ✅ Yes |
| `inspect <item>` | Analysis | Terminal | ✅ Yes |
| `validate` | Analysis | Terminal | ✅ Yes |
| `draw-graphs` | Analysis | `docs/*.mmd` | ✅ Yes |
| `show-flow` | Analysis | Terminal | ✅ Yes |
| `init` | Generation | `./main`, `.pulpo.yml` | ⚠️ Needs models/ops |
| `compile` | Generation | `run_cache/` | ⚠️ Needs models/ops |

---

### Project CLI (`./main`)

| Command | Category | Requires |
|---------|----------|----------|
| `up/down/restart` | Services | Docker |
| `status/health/logs` | Monitoring | Running services |
| `ops run` | Execution | Generated API + DB |
| `ops list` | Info | Metadata |
| `db init/seed` | Database | MongoDB |
| `db backup/restore` | Database | MongoDB |
| `prefect start/stop` | Workflows | Prefect |
| `api/ui` | Development | Generated code |
| `compile` | Generation | Framework CLI |

---

## Benefits of This Separation

1. **Clear Responsibilities**: Framework analyzes, project operates
2. **Standalone Analysis**: Can validate without generating code
3. **Project-Specific Operations**: Each project has its own CLI with its operations
4. **No Framework Dependency in Production**: Project CLI is self-contained
5. **Better UX**: Two focused CLIs instead of one confusing CLI
6. **Easier Testing**: Can test analysis without Docker/services
7. **Faster Iteration**: Analysis is instant, generation on demand

---

## Migration Path

For existing users using `core.cli_interface.CLI`:

**Before**:
```python
from core import CLI
cli = CLI()
cli.api()  # This will be removed
```

**After**:
```python
# Use generated CLI instead:
# ./main api

# Or for analysis:
# pulpo list-models
```

---

## Next Steps

1. ✅ Document separation (this file)
2. ⬜ Implement framework CLI refactoring
3. ⬜ Implement enhanced CLI generator
4. ⬜ Update tests
5. ⬜ Update examples
6. ⬜ Update main documentation
