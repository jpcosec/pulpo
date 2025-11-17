# 2. Core Concepts

## What is Pulpo Core

Pulpo Core is a **metadata-driven code generation framework** for Python that automates the creation of full-stack applications. Instead of manually writing REST APIs, CLI interfaces, and admin UIs for each new feature, you define your data models and operations once using decorators, and Pulpo Core automatically generates everything else.

### The Core Idea

```
Your Code (Models + Operations)
           ↓
      Decorators (Metadata)
           ↓
      Registries (Storage)
           ↓
   Code Generators (Synthesis)
           ↓
Multiple Surfaces (API + CLI + UI + Workflows)
```

### Why Use Pulpo Core?

- **Eliminate Boilerplate:** Stop writing repetitive CRUD endpoints, CLI commands, and UI pages
- **Maintain Type Safety:** Full Pydantic validation throughout
- **Scale Quickly:** Add new features in minutes instead of hours
- **Domain Agnostic:** Same framework works for any business domain
- **Production Ready:** Generated code is clean, type-safe, and deployable
- **Built-in Orchestration:** Prefect integration for workflow management
- **Single Source of Truth:** Changes to models/operations propagate everywhere automatically

### Who Should Use Pulpo Core?

✅ **Good fit:**
- Building admin dashboards and CRUD applications
- Creating internal tools and data management systems
- Developing microservices with standard operations
- Building prototypes that need to scale
- Building APIs with consistent patterns

❌ **Not ideal for:**
- Simple scripts (use libraries directly)
- Applications with highly custom UIs
- Projects that don't need API + CLI + UI+Orchestration
- Real-time applications (focus is on CRUD and batch operations)

---

## Define Once, Generate Everywhere Pattern

This is the fundamental pattern that Pulpo Core implements. Instead of defining the same feature multiple times for different interfaces, you define it once and Pulpo generates it everywhere.

### Traditional Approach (Without Pulpo)

When you want to add a new feature (e.g., "create a user"), you must write:

1. **Database Model** - Define the schema
2. **FastAPI Endpoint** - Handle HTTP requests
3. **CLI Command** - Handle command-line calls
4. **React Component** - Build the UI form
5. **Type Definitions** - Keep types in sync
6. **Validation Logic** - Repeat validators everywhere
7. **Prefect Workflow** - Define workflow, tasks and dependencies

Each change requires updating all 7+ places. And if operations need to run in sequence or parallel, you manually coordinate that logic.

### Pulpo Approach (With Decorators)

```python
# Step 1: Define the model ONCE
@datamodel(name="User", tags=["users"])
class User(Document):
    email: str
    name: str
    age: int

# Step 2: Define the operation ONCE (with hierarchical naming)
@operation(
    name="user_creation.validate",  # Hierarchical: namespace.verb
    inputs=User,
    outputs=Validated_User,
)
async def create_user(input: CreateUserInput) -> User:
    return CreateUserOutput(user_id="...", message="...")
```

**Then Pulpo automatically generates:**

✅ REST API endpoint: `POST /operations/user.create`
✅ CLI command: `./main ops run user.create --input '{"email":"...","name":"...","age":30}'`
✅ React UI form: Auto-generated create page
✅ Type validation: Pydantic validates inputs and outputs
✅ **Prefect workflow task:** Automatically integrated into Prefect flows based on hierarchy
✅ **Flow orchestration:** Dot-separated naming (`user_creation.write`) becomes a Prefect task which place in the flow can be infered based on the data it receives and generates.

All automatically from one definition.

### Benefits

- **Single Source of Truth:** Change once, update everywhere
- **Less Code:** 70-80% less boilerplate
- **Fewer Bugs:** Validation happens consistently
- **Easier Maintenance:** One place to fix, not five
- **Type Safe:** Full type hints propagated everywhere

---

## Decorators Overview

Decorators are the entry point to Pulpo Core. They register metadata about your code without changing how it executes.

### What Are Decorators?

Python decorators are functions that wrap other functions or classes. Pulpo uses decorators to collect metadata:

```python
@datamodel(name="Item", description="An item in inventory")
class Item(Document):
    # This decorator registers Item with the framework
    name: str
    price: float
```

The decorator doesn't change how `Item` works—it just tells Pulpo Core: "Remember this class, it's important."

### Two Main Decorators

#### 1. `@datamodel` - Register Data Models

Used to register Beanie Documents for code generation:

```python
@datamodel(
    name="Product",              # How it appears in APIs
    description="A product",     # Documentation
    tags=["products", "store"],  # For organization
    ui_order=1                   # UI field ordering hint
)
class Product(Document):
    name: str
    price: float
    description: str

    class Settings:
        name = "products"  # MongoDB collection name
```

**What it enables:**
- CRUD API endpoints (GET, POST, PUT, DELETE)
- Auto-generated React pages (list, create, edit, show)
- Type validation via Pydantic
- Discovery in the API (`/models`)

#### 2. `@operation` - Register Operations for API, CLI, and Workflow Orchestration

Used to register async functions as reusable operations that become API endpoints, CLI commands, and **Prefect workflow tasks**:

```python
@operation(
    name="stepstone_scraping.validation",     # Hierarchical: {flow}.{subflow}.{task} or {flow}.{task}
    description="Validate scrapped data",  # Documentation
    category="scrapping",                   # For organization
    models_in=["Order"],                  # Data model inputs (defines graph NODES the operation reads)
    models_out=["ValidationResult"],      # Data model outputs (defines graph NODES the operation writes)
)
async def validate_payment(
    input: PaymentInput
) -> ValidationResult:
    # Your logic here
    return ValidationResult(valid=True)
```

**Critical: Operation Naming Convention**

Operation names MUST be **verbal actions** with **hierarchical structure** for flow organization:
- ✅ Good: `user_creation.write`, `payment_processing.checkout.validation`,
- ❌ Wrong: `user_creation`, `checkout_processing`, `write_to_db`

Naming format: `{main_flow}.{optional_subflow}.{task_name}`
- Single level: `write` → Creates task standalone task without orchestration
- Two levels: `payment.charge` → Creates task in "payment" flow
- Three levels: `payment.checkout.validate` → Creates task in "checkout" subflow within "payment" flow

**Important: Hierarchy is organizational, NOT execution order!**
The dot-separated hierarchy organizes operations into flows and nested flows, but **execution order is determined by the dataflow graph** (see Registries section below).

**What it enables:**
- **REST API endpoint:** `POST /operations/payment.checkout.validate`
- **CLI command:** `./main ops run payment.checkout.validate --input '...'`
- **Prefect workflow task:** Registered in the dataflow graph based on its inputs/outputs
- **Dataflow graph node:** The operation becomes an edge in the data dependency graph
- **Automatic orchestration:** Framework analyzes `models_in` and `models_out` to determine execution order
- **Operation tracking and logging:** All executions tracked
- **Discovery in the API:** `GET /operations`

### Decorator Parameters

#### Common Parameters for Both Decorators

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `name` | str | Yes | Unique identifier (used in APIs and discovery) |
| `description` | str | No | Human-readable description for documentation |
| `tags` | list[str] | No | Tags for organization and filtering |

#### @datamodel Specific

| Parameter | Type | Purpose |
|-----------|------|---------|
| `ui_order` | int | Controls field ordering in generated UI |

#### @operation Specific (Includes Prefect Orchestration)

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `name` | str | **Yes** | **Hierarchical operation name** `{flow}.{optional_subflow}.{task}` for flow organization. Examples: `order.checkout`, `payment.validate`, `payment.checkout.charge`. Does NOT determine execution order - only organizes into flows. |
| `inputs` | BaseModel | Yes | Pydantic model defining input structure. |
| `outputs` | BaseModel | Yes | Pydantic model defining output structure. |
| `category` | str | No | Logical grouping for organization (e.g., "payment", "inventory", "reporting") |
| `models_in` | list[str] | **CRITICAL** | **Data model inputs that define the DataFlow Graph nodes this operation reads.** Example: `["Order", "Customer"]`. If another operation outputs these models, that operation runs first. |
| `models_out` | list[str] | **CRITICAL** | **Data model outputs that define the DataFlow Graph nodes this operation writes.** Example: `["PaymentRecord"]`. Any operation with this model in `models_in` will depend on this operation. |

**How Execution Order is Determined:**

The `models_in` and `models_out` parameters define the **DataFlow Graph**, which determines execution order:

```
DataFlow Graph Principle:
- Nodes = Data models
- Edges = Operations
- If Operation A outputs model X, and Operation B inputs model X, then B depends on A
```

**Example:**
```python
@operation(name="payment.validate", models_in=["Order"], models_out=["ValidationResult"])
@operation(name="payment.charge", models_in=["ValidationResult"], models_out=["ChargeRecord"])
@operation(name="payment.confirm", models_in=["ChargeRecord"], models_out=["Confirmation"])
```

**DataFlow Graph:**
```
Order --[validate]--> ValidationResult --[charge]--> ChargeRecord --[confirm]--> Confirmation
```

**Execution:** validate → charge → confirm (sequential, determined by data dependencies)

**Parallel Example:**
```python
@operation(name="payment.validate", models_in=["Order"], models_out=["ValidationResult"])
@operation(name="payment.fraud_check", models_in=["ValidationResult"], models_out=["FraudCheckResult"])
@operation(name="payment.charge", models_in=["ValidationResult"], models_out=["ChargeRecord"])
@operation(name="payment.confirm", models_in=["ChargeRecord", "FraudCheckResult"], models_out=["Confirmation"])
```

**DataFlow Graph:**
```
Order --[validate]--> ValidationResult
                          ├--[fraud_check]--> FraudCheckResult
                          └--[charge]--> ChargeRecord
                                    └--[confirm]--> Confirmation
```

**Execution:** validate → (fraud_check + charge in parallel) → confirm (sequential, based on data dependencies)

**Key Point:** The hierarchy name (`payment.validate` vs `payment.charge`) is purely for organizing which flow they belong to. The execution order is **entirely determined by the models_in/models_out dataflow graph**, not the naming hierarchy.

---

## Registries & Metadata

After decorators collect metadata, the framework stores it in registries. These are the single source of truth for what models and operations exist.

**The OperationRegistry IS the DataFlow Graph itself** - each operation's `models_in` and `models_out` define nodes and edges in the execution graph.

### What Are Registries?

Registries are in-memory dictionaries that store metadata. When your decorators run, they register information with the framework:

```python
# Simplified view of how registries work
class ModelRegistry:
    _models = {}  # {name: ModelInfo}

class OperationRegistry:
    _ops = {}     # {name: OperationMetadata}
```

### ModelRegistry

Stores information about all `@datamodel` decorated classes:

```python
from core.registries import ModelRegistry

# Get all registered models
all_models = ModelRegistry.list_all()  # Returns list of all ModelInfo

# Get a specific model
user_model = ModelRegistry.get("User")  # Returns ModelInfo or None
```

Each ModelInfo contains:
- `name`: "User"
- `description`: "A user account"
- `fields`: Dictionary of field information
- `tags`: Tags for organization
- `schema`: JSON schema for validation

### OperationRegistry - The DataFlow Graph

Stores information about all `@operation` decorated functions. **This registry IS the DataFlow Graph.**

```python
from core.registries import OperationRegistry

# Get all registered operations
all_ops = OperationRegistry.list_all()  # Returns list of all OperationMetadata

# Get a specific operation
validate_op = OperationRegistry.get("payment.validate")
# Returns: OperationMetadata with:
#   name: "payment.validate"
#   models_in: ["Order"]      ← Input node in graph
#   models_out: ["ValidationResult"]  ← Output node in graph
```

Each OperationMetadata contains:
- `name`: "payment.validate" (hierarchical name)
- `models_in`: ["Order"] - **These are the graph INPUT NODES**
- `models_out`: ["ValidationResult"] - **These are the graph OUTPUT NODES**
- `inputs`: Pydantic model for input validation
- `outputs`: Pydantic model for output validation
- `category`: For organization
- `function`: The actual async function to execute

### How the DataFlow Graph is Built

The DataFlowAnalyzer builds the graph from the OperationRegistry:

```
OperationRegistry Entries:
  validate: models_in=["Order"], models_out=["ValidationResult"]
  charge:   models_in=["ValidationResult"], models_out=["ChargeRecord"]
  confirm:  models_in=["ChargeRecord"], models_out=["Confirmation"]

↓ (Analyzed by DataFlowAnalyzer)

DataFlow Graph:
  Nodes: Order, ValidationResult, ChargeRecord, Confirmation
  Edges:
    Order --[validate]--> ValidationResult
    ValidationResult --[charge]--> ChargeRecord
    ChargeRecord --[confirm]--> Confirmation

↓ (Determines execution)

Execution Order: validate → charge → confirm (sequential)
```

**Key Insight:** The OperationRegistry doesn't explicitly store the graph structure. Instead, the graph is **computed on-demand** by analyzing `models_in` and `models_out` of all operations.

### How Registration Works

1. **Import Time:** When your `main` file imports decorated classes/functions, decorators run
2. **Metadata Collection:** Decorator collects metadata
3. **Registry Storage:** Metadata stored in global registries
4. **Graph Building:** When generating code, DataFlowAnalyzer builds the graph from OperationRegistry entries

Example flow:

```python
# main.py
from models.user import User  # Decorator runs, User registered in ModelRegistry
from operations.validate import validate_payment  # Decorator runs, operation registered in OperationRegistry

# After imports:
# ModelRegistry: {"User": ModelInfo(...), "Order": ModelInfo(...), ...}
# OperationRegistry: {"payment.validate": OperationMetadata(...), ...}
#
# When code generation happens:
# DataFlowAnalyzer analyzes all OperationRegistry entries
# Builds implicit DataFlow Graph from models_in/models_out
# Generates Prefect flows based on graph structure
```

### Graphs for Visualization

The framework generates visualization graphs using the registry data:

- **Operation Flow Graph**: Models as nodes, operations as edges
  - Nodes = Data models from ModelRegistry
  - Edges = Operations from OperationRegistry showing data transformation

- **Model Relationship Graph**: Shows how models reference each other
  - Nodes = Data models
  - Edges = Field relationships between models

These graphs are generated in markdown/mermaid format for documentation.

---

## Code Generation Pipeline

After metadata is collected in registries, the framework generates code from it. This is a multi-step process.

### The Generation Process

#### Step 1: Discovery
The framework reads registries to find all models and operations:

```
ModelRegistry → ["User", "Product", "Order"]
OperationRegistry → [
  "payment.validate" (models_in=["Order"], models_out=["ValidationResult"]),
  "payment.charge" (models_in=["ValidationResult"], models_out=["ChargeRecord"]),
  ...
]
```

#### Step 2: DataFlow Graph Analysis
**Critical Step:** The DataFlowAnalyzer builds the execution graph from the OperationRegistry:

```
For each operation in OperationRegistry:
  - Extract models_in (input nodes)
  - Extract models_out (output nodes)
  - Find dependencies: if another operation outputs what this one inputs, add dependency edge

Result: DataFlow Graph showing:
  - Which operations run first (no dependencies)
  - Which operations can run in parallel (same inputs)
  - Sequential dependencies (output of one is input to another)
  - Execution order (topological sort)
```

Example:
```
payment.validate (inputs: Order, outputs: ValidationResult)
payment.charge (inputs: ValidationResult, outputs: ChargeRecord)
→ payment.charge depends on payment.validate

payment.charge (inputs: ValidationResult, outputs: ChargeRecord)
payment.fraud_check (inputs: ValidationResult, outputs: FraudCheckResult)
→ payment.charge and payment.fraud_check can run in parallel (both take ValidationResult)
```

#### Step 3: Model Relationship Analysis
The framework analyzes model fields to detect relationships:

```
- Order has list[Item] → Order one-to-many with Item
- Invoice references Customer → Invoice references Customer
- Can these be visualized in diagrams?
```

#### Step 4: Synthesis
Code generators create production code from templates using:
- ModelRegistry data
- OperationRegistry data
- DataFlow Graph structure

```
For each model:
  Generate CRUD API endpoints
  Generate UI pages

For each operation:
  Generate API endpoint
  Generate CLI command
  Generate Prefect @task (placed in appropriate @flow based on hierarchy)

For the DataFlow Graph:
  Generate Prefect @flow that orchestrates operations according to graph structure
  Generate operation-flow diagram (markdown/mermaid)
  Generate model-relationship diagram (markdown/mermaid)
```

#### Step 5: Writing
Generated code is written to `run_cache/` directory:

```
run_cache/
├── generated_api.py              # FastAPI routes (CRUD + operations)
├── generated_flows.py            # Prefect flows based on DataFlow Graph
├── generated_ui_config.ts        # React/Refine configuration
├── generated_frontend/           # Full React application
├── operation-flow.md             # DataFlow Graph visualization
├── model-relationships.md        # Model relationship diagram
├── registry.json                 # Discovery log
└── .gitkeep
```

#### Step 6: Validation
Generated code is validated to ensure it's correct:

```
- Python syntax check (generated_api.py, generated_flows.py)
- Import verification
- Type checking (models_in/out match Pydantic schemas)
- Prefect flow validation
- FastAPI app validation
```

### Trigger Points

Generation happens when you run:

```bash
./main compile              # Explicit generation
./main up                   # Automatic generation before starting
./main api                  # Automatic generation before starting API
```

### Incremental Generation

The framework uses hashing to avoid regenerating unchanged code:

```
- Each generated file has a .hash file
- If model/operation metadata hasn't changed, hash matches
- Generation skips unchanged artifacts
- Saves time for large projects
```

### Generated Artifacts

| Artifact | Purpose | Example |
|----------|---------|---------|
| `generated_api.py` | FastAPI application with all routes | ~500-2000 lines per project |
| `generated_ui_config.ts` | React/Refine config for admin UI | Resource definitions, navigation |
| `generated_frontend/` | Complete React application | Can run standalone |
| `generated_flows.py` | Prefect workflows | One flow per hierarchical operation |
| `registry.json` | Discovery log for debugging | Lists all models/operations found |

---

## Key Takeaways

1. **Decorators register metadata** - `@datamodel` and `@operation` collect metadata without changing code execution

2. **Two separate concerns:**
   - **Hierarchy (from operation name):** Structural organization of operations into flows (`{flow}.{subflow}.{task}`)
   - **DataFlow Graph (from models_in/out):** Determines execution order - which operations run first, in parallel, sequentially

3. **OperationRegistry IS the DataFlow Graph** - Each operation's `models_in` and `models_out` define nodes and edges in the execution graph

4. **DataFlowAnalyzer builds execution order** - From OperationRegistry entries, it computes which operations depend on which, enabling parallel execution when possible

5. **Single definition, multiple surfaces** - Same `@operation` creates:
   - API endpoint (`POST /operations/{name}`)
   - CLI command (`./main ops run {name}`)
   - Prefect task (placed in flow according to hierarchy)
   - Operation tracking and logging

6. **Type-safe throughout** - Pydantic validates inputs and outputs for each operation

7. **Main entrypoint controls discovery** - Only models and operations imported in `main` are discovered and registered

8. **Code generation uses both hierarchy and dataflow:**
   - **Hierarchy** determines Prefect flow structure (which tasks go in which flows)
   - **DataFlow graph** determines execution order within and across flows

---

**Next:** Understand the system architecture in [Architecture](03_Architecture.md)
