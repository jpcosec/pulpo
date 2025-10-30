# Phase 2: CLI Correction - Command-Line Interface

**Date:** 2025-10-30
**Issue:** CLI was presented as a programmatic Python interface instead of a proper command-line tool
**Status:** FIXED ✅

---

## What Was Wrong

The documentation showed using Pulpo via Python code:

```python
# ❌ WRONG: Not how users should interact
from pulpo import CLI

cli = CLI()
cli.compile()
cli.up()
cli.prefect("start")
```

This contradicts the principle that **a CLI (Command-Line Interface) is meant to be used from the command line**.

---

## What Was Fixed

### 1. Typer CLI Wired Properly

Added Phase 2 commands to `core/cli/main.py`:

```python
@app.command()
def up():
    """Start all services."""
    cli = get_cli()
    cli.up()

@app.command()
def down():
    """Stop all services."""
    cli = get_cli()
    cli.down()

@app.command()
def prefect(command: str = typer.Argument("start", ...)):
    """Manage Prefect orchestration server."""
    cli = get_cli()
    cli.prefect(command)

@app.command()
def db(command: str = typer.Argument("status", ...)):
    """Manage database service."""
    cli = get_cli()
    cli.db(command)

@app.command()
def clean():
    """Remove generated artifacts."""
    cli = get_cli()
    cli.clean()
```

### 2. Users Now Use Command-Line Interface

**Correct usage:**

```bash
# ✅ RIGHT: Use as CLI from terminal
pulpo compile
pulpo up
pulpo down
pulpo prefect start
pulpo prefect stop
pulpo db init
pulpo db status
pulpo api --port 8000
pulpo ui --port 3000
pulpo clean
```

### 3. Architecture Clarified

- **User-facing:** `pulpo` command-line interface (via Typer)
- **Internal:** `CLI` class (used by Typer, not for users)
- **Testing:** Tests use the CLI class directly

### 4. Documentation Created

**New files:**
- `CLI_USAGE_GUIDE.md` - Complete command reference for users
- `PHASE_2_CLI_CORRECTION.md` - This document

**Updated files:**
- `PHASE_2_IMPLEMENTATION.md` - Shows correct CLI usage

---

## Complete Command Reference

### Service Lifecycle
```bash
pulpo compile   # Generate all artifacts
pulpo up        # Start all services
pulpo down      # Stop all services
pulpo clean     # Remove generated files
```

### Orchestration
```bash
pulpo prefect start
pulpo prefect stop
pulpo prefect restart
pulpo prefect logs
pulpo prefect status
```

### Database
```bash
pulpo db start
pulpo db stop
pulpo db init
pulpo db status
pulpo db logs
```

### API
```bash
pulpo api --port 8000      # Default: 0.0.0.0:8000
```

### UI
```bash
pulpo ui --port 3000       # Default: port 3000
```

### Discovery
```bash
pulpo status               # Show project status
pulpo models               # List data models
pulpo graph                # Generate diagrams
pulpo flows                # Generate operation flows
pulpo docs                 # Generate documentation
```

---

## Architecture

### CLI Entry Point (pyproject.toml)

```toml
[tool.poetry.scripts]
pulpo = "core.cli.main:main"
```

When users run `pulpo`, it calls `core.cli.main:main()` which initializes the Typer app.

### Command Flow

```
User Terminal
    ↓
pulpo compile
    ↓
core/cli/main.py (@app.command)
    ↓
core/cli_interface.py (CLI class)
    ↓
core/orchestration/ (Phase 2 components)
    ↓
run_cache/ (generated artifacts)
```

### CLI Class (Internal Only)

The `CLI` class in `core/cli_interface.py`:
- Used by Typer commands
- Used in tests
- NOT for direct user consumption

Users interact with the Typer CLI, which internally uses the CLI class.

---

## Test Results

All Phase 2 integration tests pass with the corrected CLI:

```
✅ test_hierarchy_parser_with_operation_names
✅ test_data_flow_analyzer_detects_dependencies
✅ test_parallel_group_detection
✅ test_orchestration_compiler_creates_flows
✅ test_prefect_code_generation
✅ test_cli_compile_generates_flows
✅ test_hierarchy_parser_standalone_operations
✅ test_topological_sort_respects_dependencies

8/8 passing
```

---

## Example Workflow

```bash
# 1. Create your Pulpo project with @datamodel and @operation decorators
#    (already in your project)

# 2. Compile everything (generates Prefect flows, APIs, UI, docs)
pulpo compile

# 3. Start all services
pulpo up

# 4. Start Prefect server specifically
pulpo prefect start

# 5. Initialize database
pulpo db init

# 6. Run FastAPI server
pulpo api --host 0.0.0.0 --port 8000

# 7. Check status
pulpo status

# 8. When done
pulpo down

# 9. Clean up
pulpo clean
```

---

## Key Takeaway

**CLI = Command-Line Interface**

Users should interact with Pulpo via terminal commands:

```bash
pulpo <command> [arguments]
```

NOT via Python code:

```python
# ❌ Don't do this
from core.cli_interface import CLI
cli = CLI()
cli.up()
```

The CLI class is an internal implementation detail. The user-facing interface is the `pulpo` command.

---

## Documentation References

- **User Guide:** `CLI_USAGE_GUIDE.md`
- **Implementation Details:** `PHASE_2_IMPLEMENTATION.md`
- **Phase 2 Architecture:** `PHASE_2_CLARIFIED.md`
- **Help:** `pulpo --help`
