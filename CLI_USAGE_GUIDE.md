# Pulpo CLI Usage Guide

The Pulpo framework provides a command-line interface for managing your project. Use these commands from your terminal:

## Getting Started

```bash
# Show help
pulpo --help

# Show version
pulpo version

# Check project status
pulpo status
```

## Compilation

```bash
# Compile all artifacts (APIs, UIs, Prefect flows, etc.)
pulpo compile

# Clean generated artifacts
pulpo clean
```

## Service Management

### Start and Stop Services

```bash
# Start all services (database, API, Prefect, UI)
pulpo up

# Stop all services
pulpo down
```

### Individual Service Control

#### Prefect Orchestration
```bash
# Start Prefect server
pulpo prefect start

# Stop Prefect server
pulpo prefect stop

# Restart Prefect server
pulpo prefect restart

# View Prefect logs
pulpo prefect logs

# Check Prefect status
pulpo prefect status
```

#### Database
```bash
# Start database
pulpo db start

# Stop database
pulpo db stop

# Initialize database (creates schema, indexes, etc.)
pulpo db init

# Check database status
pulpo db status

# View database logs
pulpo db logs

# Backup database
pulpo db backup

# Restore database
pulpo db restore
```

#### API Server
```bash
# Start API server (on default 0.0.0.0:8000)
pulpo api --host 0.0.0.0 --port 8000

# Restart API server
pulpo api restart

# View API logs
pulpo api logs
```

#### Web UI
```bash
# Launch web UI (on default port 3000)
pulpo ui --port 3000
```

## Discovery and Documentation

```bash
# List registered data models
pulpo models

# List registered operations
pulpo ops list

# Generate relationship graphs (Mermaid diagrams)
pulpo graph

# Generate operation flow diagrams
pulpo flows

# Generate markdown documentation
pulpo docs
```

## Linting and Quality

```bash
# Check datamodels and operations
pulpo lint check

# Show linting details
pulpo lint
```

## Complete Workflow Example

```bash
# 1. Compile your project
pulpo compile

# 2. Check project status
pulpo status

# 3. Start all services
pulpo up

# 4. Start Prefect server specifically
pulpo prefect start

# 5. Initialize database
pulpo db init

# 6. View service status
pulpo status

# 7. Run API server
pulpo api

# 8. When done, stop all services
pulpo down

# 9. Clean up
pulpo clean
```

## Environment Variables

You can control CLI behavior with environment variables:

```bash
# Enable verbose output
PULPO_VERBOSE=1 pulpo compile

# Specify run_cache directory (default: run_cache/)
PULPO_CACHE_DIR=/tmp/mycache pulpo compile

# Disable auto-compilation
PULPO_AUTO_COMPILE=0 pulpo status
```

## Integration with Makefile

Pulpo CLI commands automatically delegate to Makefile targets when available. This ensures consistency with your project's existing build system:

```bash
# These commands work via Makefile:
pulpo up          # → make up
pulpo down        # → make down
pulpo db init     # → make db-init
pulpo prefect start  # → make prefect-start
```

If you don't have a Makefile, the CLI will show a helpful message.

## Programmatic Usage (for Python code)

While the primary interface is the command line, you can also use the CLI programmatically in Python:

```python
from core.cli_interface import CLI

# Create CLI instance (discovers models/operations dynamically)
cli = CLI(verbose=True)

# Programmatic access
operations = cli.list_operations()
models = cli.list_models()
cache_dir = cli.compile()

# Service management via Python
cli.up()
cli.prefect("start")
cli.db("init")
```

However, for normal usage, prefer the command-line interface:

```bash
# Better: Use as CLI
pulpo compile
pulpo up
```

## Tips and Tricks

### Verbose Output
```bash
# See detailed output
PULPO_VERBOSE=1 pulpo compile
```

### Dry Run for Services
```bash
# Check if services would start without actually starting them
pulpo status  # Shows current state
```

### Monitor Service Logs
```bash
# Watch service logs in real-time
pulpo logs prefect
pulpo logs api
pulpo logs db
```

### Reset Everything
```bash
# Stop services and clean up
pulpo down
pulpo clean

# Then restart fresh
pulpo compile
pulpo up
```

## Troubleshooting

### "Command not found: pulpo"
Install the package properly:
```bash
pip install -e .  # Or: poetry install
```

### Services won't start
```bash
# Check system status
pulpo status

# View logs for more info
pulpo logs <service>

# Verify Makefile exists and has targets
make help
```

### Clean slate
```bash
# Remove everything and start over
pulpo clean
pulpo compile
pulpo up
```
