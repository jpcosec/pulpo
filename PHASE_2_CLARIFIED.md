# Phase 2: Prefect Integration - Clarified Design

**Date:** 2025-10-29
**Status:** Clarified requirements based on user feedback

---

## Key Clarifications

### 1. Dependency Detection: Data Model Based ✅

**Principle:** Operation flow is implicit in the data flow.

**How it works:**
```python
@datamodel(name="RawJobs")
class RawJobs: ...

@datamodel(name="CleanedJobs")
class CleanedJobs: ...

@operation(name="scraping.fetch", outputs=RawJobs)
async def fetch_jobs() -> RawJobs: ...

@operation(name="parsing.clean", inputs=RawJobs, outputs=CleanedJobs)
async def clean_jobs(raw: RawJobs) -> CleanedJobs: ...

# Framework automatically knows:
# - fetch_jobs must run first (produces RawJobs)
# - clean_jobs must run second (consumes RawJobs)

@operation(name="scraping.linkedin", outputs=RawJobs)
async def fetch_linkedin() -> RawJobs: ...

@operation(name="scraping.stepstone", outputs=RawJobs)
async def fetch_stepstone() -> RawJobs: ...

# Framework automatically knows:
# - linkedin and stepstone can run in parallel (same output, no dependencies)
# - Both must complete before clean_jobs runs
```

**Implementation:**
1. Parse all operations and their input/output DataModels
2. Build dependency graph: `Operation A -> DataModel X -> Operation B`
3. Operations with same inputs and outputs = parallelizable
4. This determines execution order implicitly

---

### 2. Generated Code Location ✅

**Clarification:** Generated flows and user operations share paths in `run_cache/`.

```
run_cache/
├── orchestration/           # Generated Prefect flows
│   ├── scraping_flow.py    # @flow for scraping.* ops
│   ├── parsing_flow.py     # @flow for parsing.* ops
│   └── standalones.py      # @flow for orphan operations
├── operations.py            # User operations (if generated)
└── ...other generated code...
```

Both live in same directory, so imports work seamlessly:
```python
# In run_cache/orchestration/scraping_flow.py
from run_cache.operations import fetch_jobs, clean_jobs
# or from registries at runtime
```

---

### 3. Flow Structure: Per Hierarchical Node ✅

**Principle:** Each hierarchical parent gets its own `@flow`.

**Structure:**
```
Operations:
- scraping.stepstone.fetch     → scraping_stepstone_flow (or scraping_flow?)
- scraping.linkedin.fetch      → scraping_linkedin_flow (or scraping_flow?)
- scraping.merge               → scraping_flow
- parsing.clean_text           → parsing_flow
- parsing.validate             → parsing_flow
- validate                      → standal ones.py

Question: How deep do we nest flows?
```

**User clarification suggests:**

**Option A: Per direct parent**
```
scraping/
  └── scraping_flow.py
      @flow: scraping_flow(...)
        ├── fetch_stepstone_task()
        ├── fetch_linkedin_task()
        └── merge_task()

parsing/
  └── parsing_flow.py
      @flow: parsing_flow(...)
        ├── clean_text_task()
        └── validate_task()

standalones/
  └── standalones.py
      @flow: validate_flow(...)
```

**Option B: Per each level**
```
scraping_stepstone_flow.py  (for scraping.stepstone.*)
scraping_linkedin_flow.py   (for scraping.linkedin.*)
scraping_flow.py            (for scraping.* top level)
parsing_flow.py             (for parsing.*)
standalones_flow.py         (for operations with no parent)
```

**Standalone Operations:**
Operations without hierarchy (e.g., `@operation(name="validate")`) either:
1. Get wrapped in auto-generated `validate_flow.py`
2. Get grouped in `standalones.py`

Plus, each flow must be executable as standalone via Prefect:
```bash
prefect flow run scraping_flow --param keywords="python"
```

---

### 4. CLI as Makefile ✅

**Principle:** CLI works like a Makefile. Each service can be independently managed.

**New Commands Needed:**
```bash
# Project-level commands
pulpo up              # Start all services
pulpo down            # Stop all services
pulpo build           # Build everything (Docker images, compile code, etc)
pulpo clean           # Clean generated artifacts

# Service-specific commands
pulpo prefect start   # Start Prefect server
pulpo prefect stop    # Stop Prefect server
pulpo prefect restart # Restart Prefect server
pulpo prefect logs    # Show Prefect logs

pulpo api start       # Start FastAPI server
pulpo api stop        # Stop FastAPI server
pulpo api restart     # Restart FastAPI server

pulpo db init         # Initialize database
pulpo db start        # Start database
pulpo db stop         # Stop database

pulpo ui start        # Start UI
pulpo ui stop         # Stop UI
pulpo ui restart      # Restart UI

pulpo status          # Show all services status
pulpo logs <service>  # Show service logs
```

**Under the hood:**
- Start/stop via Docker containers or subprocess management
- `up` = start prefect, api, db, ui in order
- `down` = stop all in reverse order
- `build` = docker build + compile + generate flows
- Each service managed independently with dependency awareness

---

## Implementation Plan (Revised)

### Components to Build:

#### 1. **Hierarchy Parser** (`core/hierarchy.py`)
```python
class HierarchyParser:
    def parse(name: str) -> ParsedName
    def get_parent(name: str) -> str | None
    def get_level(name: str) -> int
    def is_leaf(name: str) -> bool
    def is_standalone(name: str) -> bool
```

#### 2. **Data Flow Analyzer** (`core/orchestration/dataflow.py`) [NEW]
```python
class DataFlowAnalyzer:
    def build_dependency_graph(operations: List[Operation]) -> Dict:
        # Parse operation inputs/outputs
        # Build: Operation -> DataModel -> Operation chain
        # Return: {op_name: [depends_on: [op_names]]}

    def find_parallel_groups(operations: List[Operation]) -> List[List[str]]:
        # Find operations that can run in parallel
        # Criteria: same inputs, same outputs, no dependencies

    def topological_sort(operations: List[Operation]) -> List[str]:
        # Return operations in execution order
```

#### 3. **Orchestration Compiler** (`core/orchestration/compiler.py`)
```python
class OrchestrationCompiler:
    def compile(self) -> Orchestration:
        # Parse all operations
        # Analyze data flow
        # Build flow groups by hierarchical parent
        # Detect standalone operations
        # Return structure ready for code generation

class FlowDefinition:
    name: str                          # "scraping_flow"
    operations: List[OperationMetadata] # Operations in this flow
    dependencies: Dict[str, List[str]]  # Op -> depends_on
    standalone: bool                    # Is this a standalone flow
```

#### 4. **Sync/Async Detector** (`core/orchestration/sync_async.py`)
```python
class SyncAsyncDetector:
    def is_async(func: Callable) -> bool
    def wrap_if_sync(func: Callable) -> Callable
    def detect_and_wrap(func: Callable) -> Callable
```

#### 5. **Prefect Code Generator** (`core/orchestration/codegen.py`) [NEW]
```python
class PrefectCodeGenerator:
    def generate_flows(orchestration: Orchestration) -> Dict[str, str]:
        # For each FlowDefinition, generate @flow/@task code
        # Return: {flow_name: generated_code}

    def generate_task(operation: OperationMetadata) -> str:
        # Generate single @task wrapper for operation

    def generate_flow(flow_def: FlowDefinition) -> str:
        # Generate @flow with its @tasks
        # Handle parallelization
        # Handle dependencies
```

#### 6. **Service Manager** (`core/services/manager.py`) [NEW]
```python
class ServiceManager:
    def start(service: str) -> None
    def stop(service: str) -> None
    def restart(service: str) -> None
    def status(service: str) -> dict
    def up() -> None        # Start all
    def down() -> None      # Stop all
    def build() -> None     # Build all
    def logs(service: str) -> str
```

#### 7. **Updated CLI** (`core/cli_interface.py`)
```python
class CLI:
    # Existing methods...

    # New service management methods
    def prefect_start(self) -> None
    def prefect_stop(self) -> None
    def prefect_restart(self) -> None
    def api_start(self) -> None
    def api_stop(self) -> None
    def api_restart(self) -> None
    def db_init(self) -> None
    def db_start(self) -> None
    def db_stop(self) -> None
    def ui_start(self) -> None
    def ui_stop(self) -> None
    def ui_restart(self) -> None
    def up(self) -> None       # Start all services
    def down(self) -> None     # Stop all services
    def status(self) -> str    # Show all statuses
    def logs(self, service: str) -> str
```

---

## Execution Flow Example

**User code:**
```python
# models.py
@datamodel(name="RawJobs")
class RawJobs(Document):
    title: str

@datamodel(name="CleanedJobs")
class CleanedJobs(Document):
    title: str

# operations.py
@operation(
    name="scraping.stepstone.fetch",
    inputs=BaseModel,
    outputs=RawJobs,
)
async def fetch_stepstone() -> RawJobs: ...

@operation(
    name="scraping.linkedin.fetch",
    inputs=BaseModel,
    outputs=RawJobs,
)
async def fetch_linkedin() -> RawJobs: ...

@operation(
    name="scraping.merge",
    inputs=RawJobs,  # Takes multiple RawJobs
    outputs=CleanedJobs,
)
async def merge(stepstone: RawJobs, linkedin: RawJobs) -> CleanedJobs: ...

# main.py
from pulpo import CLI
cli = CLI()

if __name__ == "__main__":
    cli.run()  # or specific commands below
```

**User runs:**
```bash
# Build everything
pulpo build
# Generates:
#   - run_cache/orchestration/scraping_flow.py
#   - run_cache/orchestration/parsing_flow.py (if other ops exist)
#   - Docker images
#   - etc

# Start all services
pulpo up
# Starts: DB, API, UI, Prefect server

# Deploy and run a flow
pulpo prefect deploy scraping_flow

# Or run directly
pulpo prefect run scraping_flow
```

**Generated `run_cache/orchestration/scraping_flow.py`:**
```python
from prefect import flow, task
import asyncio
from user_project import fetch_stepstone, fetch_linkedin, merge

@task
async def fetch_stepstone_task() -> dict:
    return await fetch_stepstone()

@task
async def fetch_linkedin_task() -> dict:
    return await fetch_linkedin()

@task
async def merge_task(stepstone: dict, linkedin: dict) -> dict:
    return await merge(stepstone, linkedin)

@flow
async def scraping_flow() -> dict:
    # Parallel execution detected from data model outputs
    stepstone, linkedin = await asyncio.gather(
        fetch_stepstone_task(),
        fetch_linkedin_task(),
    )
    # Data model input matching detected
    return await merge_task(stepstone, linkedin)

if __name__ == "__main__":
    scraping_flow()
```

---

## Implementation Sequence

1. **Hierarchy Parser** - Parse operation names ✅
2. **Data Flow Analyzer** - Build dependency graph from data models
3. **Orchestration Compiler** - Group operations by hierarchy and dependencies
4. **Sync/Async Detector** - Wrap sync functions
5. **Prefect Code Generator** - Generate @flow/@task code
6. **Service Manager** - Manage start/stop/restart
7. **Update CLI** - Add service management methods
8. **Update main.py** - Wire Typer commands to CLI methods

---

## Success Criteria for Phase 2

✅ When Phase 2 is complete:
- [ ] Hierarchy parser works correctly
- [ ] Data flow analyzer builds correct dependency graphs
- [ ] Orchestration compiler groups operations by hierarchy
- [ ] Standalone operations detected and handled
- [ ] Prefect code generated is valid Python
- [ ] `cli.compile()` generates flows to run_cache/orchestration/
- [ ] `cli.up()` starts all services in correct order
- [ ] `cli.down()` stops all services gracefully
- [ ] `cli.prefect start` starts Prefect server
- [ ] `cli.status()` shows all services
- [ ] Generated flows are executable via Prefect
- [ ] Example works end-to-end

---

## Ready to Implement?

This clarified design addresses:
1. ✅ Dependency detection via data models
2. ✅ Generated code location (run_cache, shared paths)
3. ✅ Flow structure (per hierarchical node + standalones)
4. ✅ CLI as Makefile with service management
5. ✅ Standalone operations handling

Shall we proceed with implementation?
