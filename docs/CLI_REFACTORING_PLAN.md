# Pulpo CLI Architecture Refactoring Plan

## Overview
Transform Pulpo from file-scanning discovery to main entrypoint-based discovery, with proper CLI separation between framework-level and project-level commands.

## Correction Plan

### Phase 1: Discovery Mechanism
1. **Rename** `scripts/discover.py` → `scripts/discovery_file_scan.py`
   - Purpose: Scan entire codebase to help debug/bootstrap projects
   - NOT used for regular code generation
   - Only used: `pulpo discover` (framework command) or generating initial main.py

2. **Create** `scripts/discovery_main.py`
   - Purpose: Import and scan from main.py entrypoint
   - Reads imports from specified main.py file
   - Populates registries via imports (the ONLY way to generate)

3. **Update** `core/codegen.py`
   - Change: Only accepts models/operations from main.py imports
   - Remove: File scanning logic from codegen
   - Add: Main.py path as parameter
   - Add: Generate `registry.json` in `.run_cache/` for debugging

### Phase 2: Project Entrypoint
1. **Create** `core/cli_template.py`
   - Reusable Typer CLI factory for projects
   - Projects inherit reduced command set
   - All commands operate on current project only

2. **Create** main.py templates for each example
   - `examples/pokemon-app/main.py`
   - `examples/todo-app/main.py`
   - `examples/ecommerce-app/main.py`
   - Structure: imports models + operations, creates Typer app

### Phase 3: Cleanup
1. **Remove** `examples/todo-app/operations/crud.py`
   - Beanie + FastAPI handle CRUD automatically
   - No need for explicit operations

2. **Update** example READMEs
   - Document how to use main.py
   - Show: `python main.py compile`, `python main.py up`, etc.

### Phase 4: Framework CLI & Debugging
1. **Update** `core/cli/main.py`
   - Keep framework-level commands only
   - All project-related commands removed
   - Focus: `discover` (debug), `version` (info)

2. **Add file-scan variants for visualization**
   - `graph --from-scan`: Generate graphs from codebase-wide discovery
   - `flows --from-scan`: Generate flows from codebase-wide discovery
   - Purpose: Debug/understand entire codebase structure

---

# CLI Command Organization & Deployment

## Complete CLI Command Matrix

| Category                               | Command    | Purpose                             | Framework CLI `pulpo` | Project CLI `main.py` | Scope   | Notes                                                |
| -------------------------------------- | ---------- | ----------------------------------- | :-------------------: | :-------------------: | ------- | ---------------------------------------------------- |
| **DISCOVERY & INSPECTION**             |            |                                     |                       |                       |         |                                                      |
|                                        | `version`  | Show framework version              |           ✅           |           ❌           | Global  | Framework-only, not project-specific                 |
|                                        | `discover` | Scan codebase to find models/ops    |           ✅           |           ❌           | Global  | Debug/bootstrap tool, scans entire codebase          |
|                                        | `status`   | Show project status summary         |           ❌           |           ✅           | Project | List models, operations, paths, version              |
|                                        | `models`   | List all models in project          |           ❌           |           ✅           | Project | Shows registered @datamodel decorators               |
|                                        | `lint`     | Lint models and operations          |           ❌           |           ✅           | Project | Validates decorator usage & structure                |
| **CODE GENERATION**                    |            |                                     |                       |                       |         |                                                      |
|                                        | `compile`  | Generate all artifacts to run_cache |           ❌           |           ✅           | Project | Reads from main.py imports, generates API/UI/Prefect |
|                                        | `docs`     | Generate markdown documentation     |           ❌           |           ✅           | Project | Auto-generates API docs from models/operations       |
|                                        | `graph`    | Generate relationship diagrams      |    ✅ (--from-scan)    |           ✅           | Mixed   | Framework: codebase-wide; Project: from main.py imports|
|                                        | `flows`    | Generate operation flow diagrams    |    ✅ (--from-scan)    |           ✅           | Mixed   | Framework: codebase-wide; Project: from main.py imports|
| **OPERATION EXECUTION**                |            |                                     |                       |                       |         |                                                      |
|                                        | `ops`      | Execute registered operations       |           ❌           |           ✅           | Project | CLI interface to run @operation functions            |
| **SERVICE MANAGEMENT - DATABASE**      |            |                                     |                       |                       |         |                                                      |
|                                        | `db`       | Manage database service             |           ❌           |           ✅           | Project | start/stop/init/status/logs for MongoDB              |
|                                        | `init`     | Initialize project services         |           ❌           |           ✅           | Project | Set up database, Prefect, environment                |
| **SERVICE MANAGEMENT - API & UI**      |            |                                     |                       |                       |         |                                                      |
|                                        | `api`      | Start FastAPI server                |           ❌           |           ✅           | Project | Serve generated API (default: 0.0.0.0:8000)          |
|                                        | `ui`       | Launch web UI                       |           ❌           |           ✅           | Project | Serve generated React UI (default: localhost:3000)   |
| **SERVICE MANAGEMENT - ORCHESTRATION** |            |                                     |                       |                       |         |                                                      |
|                                        | `prefect`  | Manage Prefect orchestration        |           ❌           |           ✅           | Project | start/stop/restart/logs/status for Prefect           |
| **SERVICE MANAGEMENT - LIFECYCLE**     |            |                                     |                       |                       |         |                                                      |
|                                        | `up`       | Start all services                  |           ❌           |           ✅           | Project | Start API + UI + DB + Prefect (orchestrated)         |
|                                        | `down`     | Stop all services                   |           ❌           |           ✅           | Project | Stop all running services                            |
|                                        | `clean`    | Remove generated artifacts          |           ❌           |           ✅           | Project | Delete run_cache/ directory                          |

---

## Usage Examples

### Framework Level (Global Pulpo)
```bash
pulpo version                    # Check framework version
pulpo discover                   # Debug: scan codebase for models/operations
pulpo graph --from-scan          # Debug: generate graphs from file scan (codebase-wide)
pulpo flows --from-scan          # Debug: generate flows from file scan (codebase-wide)
```

### Project Level (Project Entrypoint)
```bash
# In /path/to/project/
python main.py status            # Show project status
python main.py models            # List my models
python main.py compile           # Generate artifacts (from main.py imports)
python main.py graph             # Generate my relationship diagrams (from main.py)
python main.py flows             # Generate my operation flows (from main.py)
python main.py api               # Start my API server
python main.py up                # Start all my services
python main.py down              # Stop all my services
python main.py ops list          # List my operations
python main.py lint              # Validate my decorators
```

---

## Registry File (Physical Debug Output)

A `registry.json` file is generated in `.run_cache/` during compilation for debugging purposes:

```json
{
  "timestamp": "2025-11-02T10:30:00Z",
  "method": "main_entrypoint",
  "entry_point": "main.py",
  "models": [
    {
      "name": "Pokemon",
      "description": "A Pokemon creature",
      "fields": ["name", "hp", "attack", "defense"],
      "tags": ["pokemon", "creature"]
    },
    {
      "name": "Trainer",
      "description": "A Pokemon trainer",
      "fields": ["name", "region", "team"]
    }
  ],
  "operations": [
    {
      "name": "pokemon.battles.execute",
      "description": "Execute a battle between two Pokemon",
      "inputs": "BattleInput",
      "outputs": "BattleResult",
      "category": "battles"
    }
  ]
}
```

**Purpose:**
- Debugging: See exactly what was discovered
- Auditing: Know which models/operations are included
- CI/CD: Check registry changes in version control
- IDE tooltips: Can be used by tools for autocompletion

**Location:** `.run_cache/registry.json`
**Updated:** During every `compile` command
**Format:** JSON (human-readable, machine-parseable)

---

## Key Architectural Decisions

### 1. Framework CLI (`pulpo`)
- **Minimal**: Only `version` and `discover`
- **Purpose**: Framework information and debugging
- **Scope**: Global/system-wide
- **Debug Features**: `graph --from-scan`, `flows --from-scan` for codebase-wide visualization

### 2. Project CLI (`python main.py`)
- **Complete**: All project management commands
- **Purpose**: Develop, build, deploy a single project
- **Scope**: Current project directory only
- **Inheritance**: Extends Pulpo's CLI class with project-specific behavior

### 3. Code Generation
- **Input**: Only from main.py imports
- **No file scanning**: Codegen doesn't scan directories
- **Discovery**: Via explicit imports in main.py (shows intent)
- **File scan purpose**: Debug tool only (e.g., `pulpo discover` to bootstrap)

### 4. Service Management
- **Per-project**: Each project manages its own services
- **Isolated**: `python main.py up` affects only that project
- **Docker-friendly**: Services scoped to project directory

---

## Migration Path

### For Existing Projects (with file-scan structure)
```bash
# 1. Generate initial main.py from file scan
pulpo discover > initial_main.py

# 2. Edit main.py to import your actual models/operations
# 3. Run project CLI
python main.py compile
python main.py up
```

### For New Projects
```bash
# 1. Create main.py with imports
# 2. Run project CLI immediately
python main.py compile
python main.py api
```

---

## Implementation Timeline

| Phase | Tasks | Estimated Impact |
|-------|-------|------------------|
| Phase 1 | Rename discover.py, create discovery_main.py, update codegen | Core refactor |
| Phase 2 | Create cli_template.py, add main.py to examples | Project setup |
| Phase 3 | Remove crud.py from todo-app, update READMEs | Cleanup |
| Phase 4 | Simplify core/cli/main.py to framework-only | CLI polish |
