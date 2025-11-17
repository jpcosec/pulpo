# Framework Utility Scripts

Helper scripts for running and managing the framework.
These scripts are **framework-level** and generic for any application using the core framework.

## Documentation & Analysis Scripts

### graph_generator.py

Generate Mermaid diagrams visualizing your application's architecture from `@datamodel` and `@operation` decorators.

**What it generates:**
- **Operation Flow Graph**: Shows how operations transform data between models
- **Model Relationships**: Shows field-level relationships between models (foreign keys, one-to-many, etc.)
- **Architecture Index**: Overview document with statistics

**Usage:**
```bash
# Generate diagrams from current project
python core/scripts/graph_generator.py

# Specify project directory
python core/scripts/graph_generator.py --project-dir test-project-demo

# Specify output directory
python core/scripts/graph_generator.py --output-dir docs/architecture

# Generate only operation flow
python core/scripts/graph_generator.py --flow-only

# Generate only model relationships
python core/scripts/graph_generator.py --relations-only

# Verbose mode (show discovered models/operations)
python core/scripts/graph_generator.py -v

# Use already registered models (skip discovery)
python core/scripts/graph_generator.py --no-discover
```

**Output files:**
- `operation-flow.md` - Mermaid flowchart showing data flow through operations
- `model-relationships.md` - Mermaid ER diagram showing model relationships
- `README.md` - Index with overview and statistics

**Viewing the diagrams:**
- GitHub/GitLab (native Mermaid support)
- VS Code (with Mermaid Preview extension)
- Any Markdown viewer with Mermaid support

### autodiscover.py

Scan project directories for `@datamodel` and `@operation` decorators using AST parsing (no imports).

**Usage:**
```bash
python core/scripts/autodiscover.py test-project-demo/
```

## API Scripts

All API scripts require:
- MongoDB running on localhost:27017
- Generated API code at `run_cache/generated_api/`
- Python dependencies installed

### Available Scripts

- **`run_api.py`** - Run the auto-generated API with hot reload (default)
  ```bash
  python -m core.scripts.run_api
  # API available at http://localhost:8000
  ```

- **`run_api_direct.py`** - Run API on alternative port 8001
  ```bash
  python -m core.scripts.run_api_direct
  # API available at http://localhost:8001
  ```

- **`run_api_test_port.py`** - Run API on port 8001 without hot reload (for testing)
  ```bash
  python -m core.scripts.run_api_test_port
  # Useful for stable testing without reload interference
  ```

## Application-Specific Scripts

Application-specific scripts have been moved to `core/examples/`:

- **`core/examples/clear_taskruns.py`** - Clear all TaskRun records (example-specific)
  ```bash
  python -m core.examples.clear_taskruns
  ```

## Usage via Makefile

```bash
make api             # Start API with hot reload
make clean-cache     # Remove generated files
```

## Notes

- All scripts work with the generated API code
- Generated code is ephemeral - regenerate with `make codegen`
- Scripts follow framework conventions, not application-specific patterns
