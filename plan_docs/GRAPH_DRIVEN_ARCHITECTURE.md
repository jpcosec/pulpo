# Graph-Driven Architecture: The Three Fundamental Graphs

**Status:** 📋 Design Documentation (For Library Refactoring)

The entire Pulpo Core framework is built upon three interconnected graphs. These graphs are the **single source of truth** for all code generation, analysis, and orchestration.

---

## Overview: The Three Graphs

### Graph 1: Model Composition Graph (MCG)
**Focus:** Data structure relationships
**Nodes:** `@datamodel` classes
**Edges:** Relationships, references, hierarchies
**Drives:** API CRUD endpoints, database schema, UI data models

### Graph 2: Operation Hierarchy Graph (OHG)
**Focus:** Workflow and task organization
**Nodes:** `@operation` functions
**Edges:** Hierarchical dependencies (parent-child via naming convention)
**Drives:** Prefect orchestration flows, CLI command hierarchy, task scheduling

### Graph 3: Data Flow Graph (DFG)
**Focus:** Data transformation pipeline
**Nodes:** Data models
**Edges:** Operations (directed: input models → operation → output models)
**Drives:** Data lineage analysis, impact analysis, dependency resolution

---

## Graph 1: Model Composition Graph (MCG)

### Definition

The MCG represents all `@datamodel` definitions and their relationships.

```
Node = @datamodel class
Edge = relationship/reference (FK, hierarchy, composition)
```

### Example

```python
@datamodel(name="Organization")
class Organization(Document):
    name: str

@datamodel(name="User", relations=[
    {"field": "org_id", "model": "Organization"}
])
class User(Document):
    name: str
    org_id: ObjectId

@datamodel(name="Project", relations=[
    {"field": "owner_id", "model": "User"},
    {"field": "org_id", "model": "Organization"}
])
class Project(Document):
    name: str
    owner_id: ObjectId
    org_id: ObjectId
```

### Visual Representation

```
┌──────────────────┐
│  Organization    │
│  - name: str     │
└────────┬─────────┘
         │ (org_id)
         │
    ┌────┴────┐
    │          │
┌───▼──────┐  ┌──▼─────────┐
│   User   │  │   Project   │
│ - name   │  │ - name      │
└────┬─────┘  │ - owner_id ─┼──→ User
     │        └─────────────┘
     │ (owner_id)
     └────────────────┘
```

### What MCG Drives

**1. API Generation (FastAPI Routes)**
```python
# Automatically generated from MCG
GET    /organizations              # List
POST   /organizations              # Create
GET    /organizations/{id}         # Read
PUT    /organizations/{id}         # Update
DELETE /organizations/{id}         # Delete

GET    /organizations/{org_id}/users      # Nested route
GET    /users/{user_id}/projects         # Reverse relation
```

**2. UI Data Models (React/Refine.dev)**
```typescript
// Automatically generated from MCG
interface Organization {
  _id: string;
  name: string;
  users?: User[];      // Inferred from relationship
  projects?: Project[];
}

interface User {
  _id: string;
  name: string;
  org?: Organization;  // Populated from FK
  projects?: Project[];
}
```

**3. Database Schema & Indexes**
```python
# Automatically created from MCG
# Collections: organizations, users, projects
# Indexes: user.org_id, project.owner_id, project.org_id
# Relationships validated, circular dependencies detected
```

**4. Admin UI Pages**
- List pages (with foreign key resolution)
- Create/Edit forms (with FK dropdowns)
- Show pages (with related data panels)
- Automatic relationship browsing

### MCG Analysis Algorithms

```python
# Detect circular dependencies
find_cycles(mcg) → List[List[Model]]

# Find all relationships for a model
get_relations(model, mcg) → Dict[field, target_model]

# Calculate model importance (based on inbound references)
importance_score(model, mcg) → int

# Find orphaned models (no references)
find_orphans(mcg) → List[Model]

# Validate schema consistency
validate_mcg(mcg) → List[ValidationError]
```

---

## Graph 2: Operation Hierarchy Graph (OHG)

### Definition

The OHG represents all `@operation` functions and their hierarchical relationships using dot-separated naming conventions.

```
Node = @operation function
Container = Big operation CONTAINS little operations (based on naming hierarchy)
Edge = Execution flow (what runs first → what runs second / sequential dependency)
```

**How it works:**
- Naming hierarchy defines containment: `data_ingestion` CONTAINS `data_ingestion.source_a.fetch`
- Edges define execution order: Based on dependencies and operation naming levels
- Operations at the same level (no arrows between them) can run in parallel
- Operations with arrows run sequentially (edges define "next step")

### Example

```python
# Level 1: Root operations
@operation(name="data_ingestion", ...)
async def data_ingestion(input: Input) -> Output: ...

# Level 2: Sub-operations
@operation(name="data_ingestion.source_a.fetch", ...)
async def fetch_source_a(input: Input) -> Output: ...

@operation(name="data_ingestion.source_b.fetch", ...)
async def fetch_source_b(input: Input) -> Output: ...

# Level 2: Aggregation
@operation(name="data_ingestion.merge", ...)
async def merge(source_a_output, source_b_output) -> Output: ...

# Level 2: Validation
@operation(name="data_ingestion.validate", ...)
async def validate(merged_data) -> Output: ...

# Level 1: Transformation
@operation(name="data_transformation", ...)
async def data_transformation(input: Input) -> Output: ...
```

### Visual Representation

The OHG shows **containment** (big contains little) and **execution flow** (edges show what runs first, then second):

```
┌──────── data_ingestion ────────────────────────────┐
│                                                    │
│   source_a/fetch ─┐                               │
│                   ├──→ merge ──→ validate         │
│   source_b/fetch ─┘                               │
│   (parallel)                                       │
└────────────────────────────────────────────────────┘

┌──────── data_transformation ────────────────────────┐
│                                                    │
│   input ──→ clean ──→ validate ──→ output         │
└────────────────────────────────────────────────────┘
```

**Key Points:**
- **Containment**: Big operations (data_ingestion) CONTAIN smaller operations (source_a/fetch, source_b/fetch, etc.)
- **Edges show sequence**:
  - source_a/fetch and source_b/fetch run in parallel (same level, both start first)
  - Both must complete before merge can run
  - merge must complete before validate can run
  - Arrows show "what comes next"
- **Different roots**: data_ingestion and data_transformation are separate trees (can run independently)

### What OHG Drives

**1. Prefect Flow Generation**

The edges in the OHG define execution order:
- Operations in parallel (source_a/fetch ──┐, source_b/fetch ──┐) run simultaneously
- Operations chained by edges run sequentially (merge ──→ validate)

```python
# Automatically generated from OHG hierarchy and edges
@flow(name="data_ingestion")
async def data_ingestion_flow():
    # Step 1: Run parallel operations (no arrows between them, both start first)
    results = await asyncio.gather(
        fetch_source_a_task(),
        fetch_source_b_task()
    )

    # Step 2: Run dependent operation (merge ← arrow from parallel ops)
    merged = await merge_task(results)

    # Step 3: Run next in sequence (validate ← arrow from merge)
    validated = await validate_task(merged)

    return validated

# Subtasks automatically created from operation functions
@task(name="fetch_source_a")
async def fetch_source_a_task():
    return await fetch_source_a(input)
```

**The edges directly map to code:**
- No edge between A and B → `await asyncio.gather(A, B)` (parallel)
- A ──→ B edge → `result_B = await B(result_A)` (sequential)

**2. CLI Command Organization**
```bash
# Automatically generated from OHG
pulpo ops data_ingestion              # Root operation
pulpo ops data_ingestion.source_a.fetch   # Sub-operation
pulpo ops data_ingestion.source_b.fetch   # Sub-operation
pulpo ops data_ingestion.merge            # Sub-operation
pulpo ops data_ingestion.validate         # Sub-operation

pulpo ops data_transformation         # Different root

# Tree view
pulpo ops --tree
  data_ingestion
  ├── source_a/fetch
  ├── source_b/fetch
  ├── merge
  └── validate
  data_transformation
```

**3. Task Scheduling & Parallelization**

The edges define the execution plan:
- **No edge between operations** → Can run in parallel (`source_a/fetch` and `source_b/fetch`)
- **Edge pointing to operation** → Must wait for predecessor (`merge` waits for both fetches)
- **Chain of edges** → Sequential pipeline (`source → merge → validate`)

Prefect automatically:
- Parallelizes operations with no edge between them
- Serializes operations with edges (dependencies)
- Manages retry logic and state management
- Creates dependency graph from edge structure

**4. Operation API Endpoints**
```python
# Automatically generated from OHG
POST /operations/data_ingestion               # Root
POST /operations/data_ingestion/source_a/fetch # Sub-operation
POST /operations/data_ingestion/merge         # Sub-operation
# etc.
```

### OHG Analysis Algorithms

```python
# Get all operations at a level
get_level_operations(level, ohg) → List[Operation]

# Find all children of an operation
get_children(op, ohg) → List[Operation]

# Calculate operation depth
get_depth(op, ohg) → int

# Find parallel operations (same parent, same level)
find_parallelizable(ohg) → List[List[Operation]]

# Detect circular dependencies in hierarchy
find_cycles(ohg) → List[List[Operation]]

# Get dependency chain for operation
get_dependency_chain(op, ohg) → List[Operation]
```

---

## Graph 3: Data Flow Graph (DFG)

### Definition

The DFG represents the transformation pipeline where operations move data between models.

```
Node = Data model
Edge = Operation (directed: input model → operation → output model)
```

### Example

```python
# Models (nodes in DFG)
@datamodel(name="RawData")
class RawData(Document):
    source: str
    content: str

@datamodel(name="ProcessedData")
class ProcessedData(Document):
    source: str
    cleaned: str
    metadata: dict

@datamodel(name="AnalyzedData")
class AnalyzedData(Document):
    source: str
    insights: list
    score: float

# Operations (edges in DFG)
@operation(
    name="process_raw",
    inputs=ProcessInput,
    outputs=ProcessOutput,
    models_in=["RawData"],      # Input node
    models_out=["ProcessedData"] # Output node
)
async def process_raw(...): ...

@operation(
    name="analyze_processed",
    inputs=AnalyzeInput,
    outputs=AnalyzeOutput,
    models_in=["ProcessedData"], # Input node
    models_out=["AnalyzedData"]  # Output node
)
async def analyze_processed(...): ...
```

### Visual Representation

```
RawData (node)
    │
    │ [process_raw operation]
    │ (input: RawData → output: ProcessedData)
    ▼
ProcessedData (node)
    │
    │ [analyze_processed operation]
    │ (input: ProcessedData → output: AnalyzedData)
    ▼
AnalyzedData (node)
```

### What DFG Drives

**1. Data Lineage Tracking**
```
AnalyzedData ← process_raw ← RawData
AnalyzedData ← analyze_processed ← ProcessedData ← process_raw ← RawData
```

Query: "Where does AnalyzedData come from?"
Answer: "RawData → (process_raw) → ProcessedData → (analyze_processed) → AnalyzedData"

**2. Impact Analysis**
```
Question: "If RawData schema changes, what's affected?"
Answer:
  - RawData (direct)
  - process_raw operation (uses RawData as input)
  - ProcessedData (output of process_raw)
  - analyze_processed operation (uses ProcessedData as input)
  - AnalyzedData (output of analyze_processed)
```

**3. Data Quality & Validation**
```python
# Can validate data transformation at each step
# Automatically trace which operation corrupted/transformed data
# Implement checkpoints for data validation
```

**4. Optimization Opportunities**
```
Can we:
- Cache ProcessedData to avoid re-running process_raw?
- Parallelize analyze_processed with other operations?
- Move ProcessedData to a faster storage tier?
- Add incremental updates for analyze_processed?
```

**5. Documentation Generation**
```
Auto-generate data pipeline documentation:
  1. Raw Data Ingestion
     Input: RawData
     Operation: process_raw
     Output: ProcessedData

  2. Analysis
     Input: ProcessedData
     Operation: analyze_processed
     Output: AnalyzedData
```

### DFG Analysis Algorithms

```python
# Find data lineage (ancestors of a model)
get_data_lineage(model, dfg) → List[Model]

# Find impact (descendants of a model)
get_impact(model, dfg) → List[Model]

# Find all paths from source to sink
find_paths(source: Model, sink: Model, dfg) → List[Path]

# Detect unreachable models
find_orphans(dfg) → List[Model]

# Find data transformation bottlenecks
find_bottlenecks(dfg) → List[Operation]

# Calculate data movement (model → operation → model)
get_data_movement(dfg) -> Dict[Operation, int]
```

---

## How the Three Graphs Work Together

### Integration Points

**1. Operation Input/Output Models**
```
Operation (in OHG) → models_in, models_out (in MCG)
                 → input/output types (in DFG)

Example:
@operation(
    name="data_ingestion.merge",
    models_in=["User", "Project"],    # MCG nodes
    models_out=["MergedData"]         # MCG node
)
# Creates edge in DFG: User → merge_op → MergedData
#                      Project → merge_op → MergedData
```

**2. Relationship Resolution in API**
```
User.projects (MCG relationship)
  + GET /users/{id}/projects (API endpoint)
  + Automatically populated in API responses
  + UI shows related projects in User detail page
```

**3. Prefect Flow Data Dependencies**
```
OHG hierarchy: data_ingestion.source_a.fetch → data_ingestion.merge
DFG path: RawData_A → source_a_fetch → ProcessedData_A → merge → MergedData

Prefect automatically:
- Runs source_a_fetch with RawData_A as input
- Waits for output (ProcessedData_A)
- Passes ProcessedData_A to merge
```

### Code Generation Pipeline

```
┌─────────────────────────────────────────────┐
│          Metadata Collection (Decorators)    │
│  @datamodel, @operation register in registry│
└────────┬───────────────┬───────────────┬────┘
         │               │               │
         ▼               ▼               ▼
    ┌────────────┐  ┌──────────┐  ┌───────────┐
    │    MCG     │  │   OHG    │  │    DFG    │
    │ (Models &  │  │(Operation│  │ (Data     │
    │ Relations) │  │Hierarchy)│  │ Flow)     │
    └────────────┘  └──────────┘  └───────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                    ┌────▼─────┐
                    │Analyzers │
                    └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    FastAPI          CLI Org          Prefect
    Routes           Structure         Flows
         │               │               │
    ┌────┴───────────────┴───────────────┴────┐
    │       Code Generation Templates          │
    │  (Jinja2 templates for API/CLI/UI)      │
    └────┬───────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │   Generated Code Output   │
    │  (FastAPI, React, CLI)    │
    └──────────────────────────┘
```

---

## Graph Construction & Maintenance

### How Graphs Are Built

**1. Registry Population (Import Time)**
```python
# When decorators are applied:
@datamodel(name="User", relations=[...])
class User(Document): ...
    ↓
ModelRegistry.register(...)
    ↓
MCG is updated with new node and edges
```

**2. Graph Analysis (Code Generation Time)**
```python
# Before generating code:
mcg = ModelRegistry.as_graph()
ohg = OperationRegistry.as_graph()
dfg = build_dataflow_graph(mcg, ohg)

# Validate graphs
validate_mcg(mcg)
validate_ohg(ohg)
validate_dfg(dfg)

# Generate code
for model in mcg.nodes():
    generate_api_routes(model, mcg)

for op in ohg.nodes():
    generate_cli_command(op, ohg)

generate_prefect_flows(ohg, dfg)
```

### Graph Validation

**MCG Validation**
```python
- No circular references (User → Project → User ✗)
- All FK targets exist
- No orphaned models (optional)
- Type consistency in relationships
```

**OHG Validation**
```python
- No circular hierarchies
- All operation dependencies resolvable
- No missing parent operations
- Input/output types match across hierarchy
```

**DFG Validation**
```python
- No unreachable models (orphans)
- Operation input/output types match model definitions
- Data can flow through pipeline without type errors
- No infinite loops
```

---

## Benefits of Graph-Driven Architecture

### 1. **Consistency**
All generated code derives from the same source of truth (the graphs).
Changes propagate automatically.

### 2. **Analysis Capabilities**
- Find circular dependencies
- Trace data lineage
- Calculate impact of schema changes
- Optimize parallelization
- Detect bottlenecks

### 3. **Extensibility**
New code generators can be plugged in without modifying core logic.
Just read the graphs and generate code.

### 4. **Documentation**
Graphs can be visualized to auto-generate architecture documentation.

### 5. **Validation**
Before generating code, validate entire architecture.
Catch errors early.

### 6. **Performance**
Analyze graphs to find optimization opportunities:
- Parallelize independent operations
- Cache expensive transformations
- Reorder operations for efficiency

---

## Current Implementation Status

### ✅ Implemented
- Model Composition Graph (MCG) in registries
- Operation Hierarchy Graph (OHG) in registries
- Basic code generation from graphs

### 🔄 In Progress
- Comprehensive graph analysis algorithms
- Data Flow Graph (DFG) explicit construction
- Visual graph representations

### 📋 Planned
- Advanced graph algorithms (cycle detection, path finding)
- Graph optimization algorithms
- Real-time graph updates
- Graph visualization UI

---

## Visual Diagram Reference

Create three separate Mermaid diagrams in documentation:

```
[MCG Diagram]
Organization
  ├── users (1:many)
  └── projects (1:many)
User
  ├── org_id (many:1)
  └── projects (many:many)
Project
  ├── owner_id (many:1)
  └── org_id (many:1)
```

```
[OHG Diagram - Containment & Flow]

┌── data_ingestion ─────────────┐
│                               │
│  source_a/fetch ──┐           │
│                   ├→ merge ──→ validate
│  source_b/fetch ──┘           │
│  (parallel)                   │
└───────────────────────────────┘

Containment: Big (data_ingestion) contains little (source_a/fetch, source_b/fetch, merge, validate)
Edges: Show execution flow - what runs first, what runs second
Parallel: source_a/fetch and source_b/fetch run simultaneously
Sequential: merge waits for both fetches, validate waits for merge
```

```
[DFG Diagram]
RawData_A → [source_a/fetch] → ProcessedData_A ┐
RawData_B → [source_b/fetch] → ProcessedData_B ├→ [merge] → MergedData
                                                  ┘
```

---

## References & Further Reading

- `docs/ARCHITECTURE_OVERVIEW.md` - System architecture
- `docs/HOW_CORE_WORKS.md` - Implementation details
- `core/registries.py` - Graph storage implementation
- `core/codegen.py` - Code generators (graph consumers)
