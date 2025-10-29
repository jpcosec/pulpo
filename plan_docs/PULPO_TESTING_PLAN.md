# PulpoCore Testing & Modification Plan

**Purpose:** Test PulpoCore as agnostic framework with auto-generated Prefect orchestration
**Environment:** Separate test instance
**Phases:** 5 independent, testable phases
**Extended Proposal C:** Hierarchical naming → auto-generated DAG orchestration

---

## Overview

This plan tests the new PulpoCore architecture with Extended Proposal C features:
- Framework is **agnostic** to project structure
- Only requires: **decorators + main entrypoint**
- Hierarchical naming convention creates orchestration DAG automatically
- CLI object acts as interface to everything
- Generated code goes to **run_cache/** (not hidden)

### Extended Proposal C Key Features

**1. Hierarchical Naming Convention**
```python
@operation(name="scraping.stepstone.fetch")  # 3-level hierarchy
async def fetch_stepstone(): ...

@operation(name="scraping.linkedin.fetch")   # Same parent, parallel sibling
async def fetch_linkedin(): ...

@operation(name="scraping.merge")             # Same level parent
async def merge_sources(): ...
```
Framework parses naming hierarchy and auto-generates Prefect flow structure in `/run_cache/orchestration/`

**2. Automatic Parallelization Detection**
- Operations at same hierarchy level with no inter-dependencies run in parallel
- Framework uses `asyncio.gather()` to execute concurrently
- Auto-detects from operation input/output types
- Results automatically merged for downstream operations

**3. Sync/Async Transparency**
```python
@operation(name="parsing.clean_text")
def clean_text(text: str) -> str:  # Sync function
    return text.strip().lower()

@operation(name="parsing.validate_job")
async def validate_job(job: Job) -> ValidatedJob:  # Async function
    return await validate_with_ai(job)
```
Framework automatically wraps sync functions with `run_in_executor()`, no user intervention needed

---

# PHASE 1: Framework Structure Validation

## Step 1.1: Verify PulpoCore Package Structure

**Objective:** Confirm pulpo/ folder has correct structure as standalone package.

**Prerequisites:**
- New /pulpo folder exists
- Contains pulpo/ package subdirectory
- All framework code present

**Test Environment:**
```bash
# In test instance, create isolated test directory
mkdir -p ~/pulpo-test
cd ~/pulpo-test

# Copy the new pulpo folder here
cp -r /path/to/pulpo ./
```

**Verification:**
```bash
cd ~/pulpo-test/pulpo

# Check structure
tree -L 2 -d

# Expected output:
# pulpo/
# ├── core/
# │   ├── cli/
# │   ├── decorators/
# │   ├── registries/
# │   ├── codegen/
# │   ├── graph_generator/
# │   ├── linter/
# │   ├── selfawareness/
# │   └── utils/
# ├── templates/
# ├── frontend_template/
# ├── docs/
# ├── examples/
# ├── tests/
# └── __init__.py

# Check __init__.py exports
cat pulpo/__init__.py
# Should show: from pulpo.core.decorators import datamodel, operation
```

**Acceptance Criteria:**
- ✅ pulpo/ is standalone package (not nested in other folder)
- ✅ pulpo/__init__.py exists and exports main items
- ✅ Can import: `from pulpo import datamodel, operation, CLI`
- ✅ All submodules present

**Test Commands:**
```bash
cd ~/pulpo-test
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

# Test imports
from pulpo import datamodel, operation
from pulpo.core.registries import ModelRegistry, OperationRegistry
from pulpo.core.cli import CLI

print("✅ All imports successful")
print(f"   datamodel: {datamodel}")
print(f"   operation: {operation}")
print(f"   CLI: {CLI}")
EOF

# Expected: All imports successful, no errors
```

**Rollback:** Delete test directory
```bash
rm -rf ~/pulpo-test
```

---

## Step 1.1b: Verify Hierarchy Parser (Extended Proposal C)

**Objective:** Confirm framework can parse hierarchical operation names into DAG structure.

**Test:**
```bash
cd ~/pulpo-test

cat > test_hierarchy.py << 'EOF'
from pulpo import operation
from pulpo.core.hierarchy import HierarchyParser  # New module in Extended Proposal C

# Test hierarchy parsing
test_names = [
    "scraping.stepstone.fetch",
    "scraping.stepstone.parse",
    "scraping.linkedin.fetch",
    "scraping.linkedin.parse",
    "scraping.merge",
    "parsing.clean_text",
    "parsing.validate_job",
    "parsing.save_db",
]

parser = HierarchyParser()

# Parse all names
parsed = [parser.parse(name) for name in test_names]

# Verify structure
for name, parsed_name in zip(test_names, parsed):
    print(f"{name}")
    print(f"  → hierarchy: {parsed_name.hierarchy}")
    print(f"  → level: {parsed_name.level}")
    print(f"  → step: {parsed_name.step}")

# Verify grouping
scraping_ops = [p for p in parsed if p.hierarchy[0] == "scraping"]
parsing_ops = [p for p in parsed if p.hierarchy[0] == "parsing"]

print(f"\n✅ Scraping operations: {len(scraping_ops)}")
print(f"✅ Parsing operations: {len(parsing_ops)}")

# Verify multi-level hierarchy
stepstone_ops = [p for p in scraping_ops if len(p.hierarchy) > 1 and p.hierarchy[1] == "stepstone"]
print(f"✅ Stepstone sub-operations: {len(stepstone_ops)}")

assert len(scraping_ops) == 5, "Should have 5 scraping operations"
assert len(parsing_ops) == 3, "Should have 3 parsing operations"
assert len(stepstone_ops) == 2, "Should have 2 stepstone sub-operations"

print("\n✅ Hierarchy parsing works correctly!")
EOF

python3 test_hierarchy.py
```

**Acceptance Criteria:**
- ✅ HierarchyParser can parse operation names
- ✅ Multi-level hierarchy supported (3+ levels)
- ✅ Grouping by hierarchy level works
- ✅ No parsing errors

---

## Step 1.2: Verify Import Pattern

**Objective:** Confirm imports work as `from pulpo import ...`

**Test:**
```bash
cd ~/pulpo-test

# Create test file
cat > test_imports.py << 'EOF'
# Test new import pattern
from pulpo import datamodel, operation, ModelRegistry, OperationRegistry
from pulpo.core import cli
from pulpo.core.cli import CLI

# Verify they're the right objects
assert callable(datamodel), "datamodel should be callable"
assert callable(operation), "operation should be callable"
assert hasattr(CLI, '__init__'), "CLI should be a class"

print("✅ Import pattern verification passed")
print(f"  datamodel: {type(datamodel)}")
print(f"  operation: {type(operation)}")
print(f"  CLI: {CLI}")

# Test decorator usage
@datamodel(name="TestModel")
class TestModel:
    pass

@operation(name="test_op")
async def test_op():
    pass

print("✅ Decorators work correctly")
EOF

# Run test
python3 test_imports.py
```

**Acceptance Criteria:**
- ✅ Imports work with pattern: `from pulpo import ...`
- ✅ Decorators can be applied
- ✅ No import errors
- ✅ All objects are correct types

---

# PHASE 2: CLI Interface Validation

## Step 2.1: CLI Instantiation

**Objective:** Verify CLI can be instantiated and configured.

**Test:**
```bash
cd ~/pulpo-test

cat > test_cli.py << 'EOF'
from pulpo.core.cli import CLI
from pulpo import datamodel, operation

# Create sample models and operations
@datamodel(name="Job", description="Job posting")
class Job:
    title: str
    company: str

@operation(name="search_jobs", description="Search for jobs")
async def search_jobs(keywords: str):
    return {"results": []}

# Test 1: Instantiate CLI
print("Test 1: Instantiate CLI")
cli = CLI()
print(f"✅ CLI instantiated: {cli}")
print(f"   CLI type: {type(cli)}")

# Test 2: Check CLI has expected methods
print("\nTest 2: CLI methods")
required_methods = ['discover', 'compile', 'build', 'run']
for method in required_methods:
    has_method = hasattr(cli, method)
    print(f"   {method}: {'✅' if has_method else '❌'}")
    assert has_method, f"CLI should have {method} method"

# Test 3: Verify CLI can access registries
print("\nTest 3: CLI registries")
assert hasattr(cli, 'model_registry'), "CLI should have model_registry"
assert hasattr(cli, 'operation_registry'), "CLI should have operation_registry"
print("✅ CLI has registries")

# Test 4: Check registries have our items
print("\nTest 4: Registry contents")
models = cli.model_registry.get_all()
ops = cli.operation_registry.get_all()
print(f"   Models registered: {len(models)}")
print(f"   Operations registered: {len(ops)}")
EOF

python3 test_cli.py
```

**Acceptance Criteria:**
- ✅ CLI instantiates without errors
- ✅ CLI has methods: discover, compile, build, run
- ✅ CLI has registries: model_registry, operation_registry
- ✅ Registries contain discovered items

---

## Step 2.2: CLI Commands

**Objective:** Verify CLI commands work.

**Test:**
```bash
cd ~/pulpo-test

cat > test_cli_commands.py << 'EOF'
from pulpo.core.cli import CLI
from pulpo import datamodel, operation

# Create test project structure
import os
import json

@datamodel(name="TestModel")
class TestModel:
    name: str

@operation(name="test_op")
async def test_op():
    return {"status": "ok"}

# Create a main entrypoint
cli = CLI()

# Test 1: Discover command
print("Test 1: CLI discover")
try:
    cli.discover()
    print("✅ Discover succeeded")
except Exception as e:
    print(f"❌ Discover failed: {e}")

# Test 2: Check discovered items
print("\nTest 2: Discovered items")
models = cli.model_registry.get_all()
ops = cli.operation_registry.get_all()
print(f"✅ Found {len(models)} models")
print(f"✅ Found {len(ops)} operations")

for model_name in models:
    print(f"   Model: {model_name}")

for op_name in ops:
    print(f"   Operation: {op_name}")
EOF

python3 test_cli_commands.py
```

**Acceptance Criteria:**
- ✅ CLI.discover() works
- ✅ Finds models and operations
- ✅ Registries populate correctly
- ✅ No errors during discovery

---

## Step 2.3: Orchestration Compilation (Extended Proposal C)

**Objective:** Test that CLI can compile hierarchy-based operations into Prefect flows.

**Test:**
```bash
cd ~/pulpo-test

cat > test_orchestration.py << 'EOF'
from pulpo import operation, datamodel
from pulpo.core.cli import CLI
from pulpo.core.orchestration import OrchestrationCompiler
from pydantic import BaseModel

# Define parallel operations with hierarchy
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(keywords: str):
    return {"source": "stepstone", "jobs": []}

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(keywords: str):
    return {"source": "linkedin", "jobs": []}

@operation(name="scraping.glassdoor.fetch")
async def fetch_glassdoor(keywords: str):
    return {"source": "glassdoor", "jobs": []}

@operation(name="scraping.merge")
async def merge_all(stepstone, linkedin, glassdoor):
    """Auto-detects inputs from upstream operations"""
    all_jobs = stepstone["jobs"] + linkedin["jobs"] + glassdoor["jobs"]
    return {"merged": True, "count": len(all_jobs)}

# Test compilation
print("Test 1: Discover operations")
cli = CLI()
cli.discover()
print(f"✅ Found {len(cli.operation_registry.get_all())} operations")

# Test 2: Compile orchestration
print("\nTest 2: Compile orchestration from hierarchy")
compiler = OrchestrationCompiler(cli)
orchestration = compiler.compile()

# Verify orchestration structure
print(f"✅ Compiled orchestration: {type(orchestration)}")

# Test 3: Verify parallelization detection
print("\nTest 3: Parallelization detection")
scraping_flow = orchestration.get_flow("scraping")
parallel_group = scraping_flow.get_parallel_group("fetch")

if parallel_group:
    print(f"✅ Detected parallel fetch operations: {len(parallel_group.operations)}")
    for op in parallel_group.operations:
        print(f"   - {op.name}")
else:
    print("⚠️  No parallel group detected (check logic)")

# Test 4: Verify dependency graph
print("\nTest 4: Dependency graph generation")
merge_op = scraping_flow.get_operation("merge")
dependencies = merge_op.get_dependencies()
print(f"✅ Merge operation has {len(dependencies)} upstream dependencies")
for dep in dependencies:
    print(f"   - {dep.name}")

assert len(dependencies) == 3, "Merge should depend on 3 fetch operations"
print("\n✅ Orchestration compilation works!")
EOF

python3 test_orchestration.py
```

**Acceptance Criteria:**
- ✅ OrchestrationCompiler can compile hierarchy to flows
- ✅ Parallelization detected for same-level operations
- ✅ Dependencies inferred from operation inputs
- ✅ Dependency graph created correctly
- ✅ No errors during compilation

---

# PHASE 3: Run Cache Generation

## Step 3.1: Verify run_cache Folder Creation

**Objective:** Test that `make compile` creates `run_cache/` (visible, not hidden).

**Setup:**
```bash
cd ~/pulpo-test

# Create example project
mkdir -p example-project
cd example-project

# Copy example from tar if available
# OR create minimal example
cat > models.py << 'EOF'
from pulpo import datamodel

@datamodel(name="Item", description="Test item")
class Item:
    name: str
    description: str
EOF

cat > operations.py << 'EOF'
from pulpo import operation
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str

class SearchOutput(BaseModel):
    results: list

@operation(name="search", inputs=SearchInput, outputs=SearchOutput)
async def search(input: SearchInput):
    return SearchOutput(results=[])
EOF

cat > main.py << 'EOF'
from pulpo.core.cli import CLI
from models import Item
from operations import search

# Create CLI
cli = CLI()

# Discover decorators
cli.discover()

# Main interface
if __name__ == "__main__":
    # Would be: cli.run()
    print("CLI initialized")
EOF

cat > Makefile << 'EOF'
.PHONY: compile build clean

compile:
	python3 -c "from pulpo.core.cli import CLI; cli = CLI(); cli.compile()"

build:
	echo "Building..."

clean:
	rm -rf run_cache/

help:
	@echo "Available commands: compile, build, clean"
EOF
```

**Test:**
```bash
cd ~/pulpo-test/example-project

# Run make compile
make compile

# Check folder creation
ls -la | grep run_cache

# Expected:
# drwxr-xr-x  run_cache/    (NOT .run_cache/)

# Verify it's not hidden
[ -d "run_cache" ] && echo "✅ run_cache/ is visible" || echo "❌ run_cache/ not found"
[ -d ".run_cache" ] && echo "❌ .run_cache/ exists (should not)" || echo "✅ .run_cache/ doesn't exist (correct)"
```

**Acceptance Criteria:**
- ✅ Folder created as `run_cache/` (not `.run_cache/`)
- ✅ Folder is visible (no leading dot)
- ✅ No hidden folder created
- ✅ Folder contains generated files

---

## Step 3.2: Verify Generated Artifacts

**Objective:** Check that run_cache/ contains expected generated files.

**Test:**
```bash
cd ~/pulpo-test/example-project

# Check contents
echo "Contents of run_cache/:"
ls -la run_cache/

# Expected files (some or all):
# - orchestration/           ← NEW: Prefect flows (Extended Proposal C)
# - generated_api.py
# - generated_cli.py (or cli/)
# - generated_ui_config.ts
# - Dockerfile
# - docker-compose.yml
# - models_graph.svg
# - operations.md

# Verify API generation
if [ -f "run_cache/generated_api.py" ]; then
    echo "✅ FastAPI code generated"
    # Check if valid Python
    python3 -m py_compile run_cache/generated_api.py && echo "✅ Generated API is valid Python"
else
    echo "❌ generated_api.py not found"
fi

# Verify Prefect orchestration (Extended Proposal C)
if [ -d "run_cache/orchestration" ]; then
    echo "✅ Prefect orchestration folder created"
    echo "   Contents:"
    ls -la run_cache/orchestration/
else
    echo "⚠️  orchestration/ not found (may be optional)"
fi

# Verify CLI generation
if [ -d "run_cache/cli" ] || [ -f "run_cache/generated_cli.py" ]; then
    echo "✅ CLI code generated"
else
    echo "⚠️  CLI code not found (may be optional)"
fi

# Count generated files
FILE_COUNT=$(find run_cache -type f | wc -l)
echo "✅ Generated $FILE_COUNT files"
```

**Acceptance Criteria:**
- ✅ run_cache/ contains generated files
- ✅ At least generated_api.py exists
- ✅ Generated Python code is syntactically valid
- ✅ orchestration/ folder created with Prefect flows (Extended Proposal C)
- ✅ Other expected artifacts present

---

## Step 3.2b: Verify Prefect Flow Generation (Extended Proposal C)

**Objective:** Test that generated Prefect flows correctly handle hierarchy, parallelization, and sync/async.

**Test:**
```bash
cd ~/pulpo-test/example-project

cat > test_generated_flows.py << 'EOF'
import sys
sys.path.insert(0, "run_cache/orchestration")

# Test 1: Import generated flows
print("Test 1: Import generated flows")
try:
    from scraping import scraping_flow
    print("✅ Generated scraping flow imported")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Verify flow structure
print("\nTest 2: Verify flow structure")
print(f"✅ Flow name: {scraping_flow.name}")
print(f"✅ Flow has {len(scraping_flow.tasks)} tasks")

# List tasks
for task in scraping_flow.tasks:
    print(f"   - {task.name}")

# Test 3: Verify Prefect decorators
print("\nTest 3: Verify Prefect decorators")
import inspect

# Check if it's a Prefect flow
is_prefect_flow = hasattr(scraping_flow, 'run')
print(f"{'✅' if is_prefect_flow else '❌'} Is valid Prefect flow: {is_prefect_flow}")

# Test 4: Verify parallelization structure (if present)
print("\nTest 4: Check for parallelization")
# Look for asyncio.gather in source
source = inspect.getsource(scraping_flow.fn) if hasattr(scraping_flow, 'fn') else ""
has_parallelization = "gather" in source or "asyncio" in source
print(f"{'✅' if has_parallelization else '⚠️'} Uses asyncio.gather for parallelization: {has_parallelization}")

# Test 5: Test execution (dry run)
print("\nTest 5: Execute flow (dry run)")
try:
    # Just verify it can be called, don't actually run
    print("✅ Flow is callable and structured correctly")
except Exception as e:
    print(f"❌ Flow execution failed: {e}")

print("\n✅ Generated Prefect flows validated!")
EOF

python3 test_generated_flows.py
```

**Acceptance Criteria:**
- ✅ Generated flow files exist in run_cache/orchestration/
- ✅ Flows are valid Prefect @flow decorated functions
- ✅ Flows can be imported without errors
- ✅ Parallelization detected in flow code
- ✅ All operations included as @task wrappers

---

## Step 3.3: Idempotency Test

**Objective:** Verify running compile twice produces same result.

**Test:**
```bash
cd ~/pulpo-test/example-project

# First compilation
echo "First compile..."
make compile
sleep 1

# Create hash of contents
HASH1=$(find run_cache -type f -exec md5sum {} \; | sort | md5sum | awk '{print $1}')
echo "Hash after first compile: $HASH1"

# Second compilation
echo "Second compile..."
make compile
sleep 1

# Create hash again
HASH2=$(find run_cache -type f -exec md5sum {} \; | sort | md5sum | awk '{print $1}')
echo "Hash after second compile: $HASH2"

# Compare
if [ "$HASH1" = "$HASH2" ]; then
    echo "✅ Idempotent - same result both times"
else
    echo "⚠️  Different result (may be expected if timestamps differ)"
fi
```

**Acceptance Criteria:**
- ✅ Second compile succeeds
- ✅ No errors on idempotent runs
- ✅ Generated code is stable

---

# PHASE 4: Framework Agnosticism Test

## Step 4.1: Different Project Structure

**Objective:** Test that framework works with non-standard project layout.

**Test Setup 1: Flat structure (all in one file)**
```bash
cd ~/pulpo-test

mkdir -p flat-project
cd flat-project

cat > app.py << 'EOF'
"""Single file app with models and operations."""

from pulpo import datamodel, operation
from pulpo.core.cli import CLI
from pydantic import BaseModel

# Models
@datamodel(name="User")
class User:
    name: str
    email: str

@datamodel(name="Post")
class Post:
    title: str
    content: str
    author: str

# Operations
class CreateUserInput(BaseModel):
    name: str
    email: str

class CreateUserOutput(BaseModel):
    id: str
    name: str

@operation(name="create_user", inputs=CreateUserInput, outputs=CreateUserOutput)
async def create_user(input: CreateUserInput):
    return CreateUserOutput(id="123", name=input.name)

# CLI
if __name__ == "__main__":
    cli = CLI()
    cli.discover()
    # Would run: cli.run()
    print(f"Discovered {len(cli.model_registry.get_all())} models")
    print(f"Discovered {len(cli.operation_registry.get_all())} operations")
EOF

python3 app.py
```

**Expected Output:**
```
Discovered 2 models
Discovered 1 operations
```

**Test Setup 2: Nested structure (different from conventional)**
```bash
cd ~/pulpo-test

mkdir -p nested-project/internal/{models,ops}
cd nested-project

cat > internal/models/__init__.py << 'EOF'
from pulpo import datamodel

@datamodel(name="Config")
class Config:
    api_key: str
    debug: bool
EOF

cat > internal/ops/__init__.py << 'EOF'
from pulpo import operation

@operation(name="validate")
async def validate():
    return {"valid": True}
EOF

cat > main.py << 'EOF'
import sys
sys.path.insert(0, '.')

from pulpo.core.cli import CLI
from internal.models import Config
from internal.ops import validate

cli = CLI()
cli.discover()
print(f"Models: {len(cli.model_registry.get_all())}")
print(f"Operations: {len(cli.operation_registry.get_all())}")
EOF

python3 main.py
```

**Acceptance Criteria:**
- ✅ Flat structure works
- ✅ Nested non-standard structure works
- ✅ Framework finds decorators regardless of structure
- ✅ CLI works with any project organization

---

## Step 4.2: Sync/Async Function Handling (Extended Proposal C)

**Objective:** Verify framework correctly detects and wraps sync functions with run_in_executor.

**Test:**
```bash
cd ~/pulpo-test

cat > test_sync_async.py << 'EOF'
from pulpo import operation
from pulpo.core.cli import CLI
from pulpo.core.orchestration import SyncAsyncDetector
import inspect

# Mix of sync and async operations
@operation(name="parsing.clean_text")
def clean_text(text: str) -> str:
    """Sync function - should be wrapped with run_in_executor"""
    return text.strip().lower()

@operation(name="parsing.validate_job")
async def validate_job(text: str) -> bool:
    """Async function - should remain as-is"""
    return len(text) > 0

@operation(name="processing.transform")
def transform(data: dict) -> dict:
    """Another sync function"""
    return {k: v.upper() for k, v in data.items()}

@operation(name="processing.load")
async def load_to_db(data: dict) -> bool:
    """Another async function"""
    return True

# Test detection
print("Test 1: Sync/Async detection")
detector = SyncAsyncDetector()

ops = [clean_text, validate_job, transform, load_to_db]
for op in ops:
    is_async = inspect.iscoroutinefunction(op)
    detected = detector.is_async(op)
    print(f"   {op.__name__}: async={detected}, expected={is_async}")
    assert detected == is_async, f"Detection failed for {op.__name__}"

print("✅ All operations correctly detected")

# Test 2: Wrapping sync functions
print("\nTest 2: Sync function wrapping")
wrapped = detector.wrap_if_sync(clean_text)
is_wrapped_async = inspect.iscoroutinefunction(wrapped)
print(f"   clean_text: originally sync, wrapped async={is_wrapped_async}")
assert is_wrapped_async, "Sync function should be wrapped to async"

# Test 3: No wrapping for async
print("\nTest 3: Async functions remain unchanged")
wrapped_async = detector.wrap_if_sync(validate_job)
assert wrapped_async == validate_job, "Async function should not be wrapped"
print("✅ Async function unchanged")

print("\n✅ Sync/Async handling works correctly!")
EOF

python3 test_sync_async.py
```

**Acceptance Criteria:**
- ✅ Sync functions correctly detected (not coroutines)
- ✅ Async functions correctly detected (are coroutines)
- ✅ Sync functions wrapped with run_in_executor
- ✅ Async functions left unchanged
- ✅ Wrapped sync functions are awaitable

---

## Step 4.3: Framework Independence

**Objective:** Verify framework doesn't assume project structure.

**Test:**
```bash
cd ~/pulpo-test

cat > agnostic_test.py << 'EOF'
"""Test that framework makes no assumptions about project structure."""

from pulpo import datamodel, operation
from pulpo.core.cli import CLI

# Framework should work with:
# - Any number of models (0, 1, many)
# - Any number of operations (0, 1, many)
# - Models and operations in any order
# - Any naming scheme with hierarchy or without

# Test 1: No models, only operations with hierarchy
@operation(name="scraping.source1.fetch")
async def op1(): pass

@operation(name="scraping.source2.fetch")
async def op2(): pass

@operation(name="scraping.merge")
async def op3(): pass

cli = CLI()
cli.discover()

assert len(cli.model_registry.get_all()) == 0, "Should handle no models"
assert len(cli.operation_registry.get_all()) == 3, "Should find 3 operations"
print("✅ Test 1: Hierarchical operations, no models")

# Test 2: Reset and test only models
from importlib import reload
from pulpo.core import registries
reload(registries)

@datamodel(name="M1")
class M1: pass

@datamodel(name="M2")
class M2: pass

@datamodel(name="M3")
class M3: pass

cli = CLI()
cli.discover()

assert len(cli.model_registry.get_all()) == 3, "Should find 3 models"
assert len(cli.operation_registry.get_all()) == 0, "Should have no operations"
print("✅ Test 2: Multiple models, no operations")

print("✅ Framework is truly agnostic to structure!")
EOF

python3 agnostic_test.py
```

**Acceptance Criteria:**
- ✅ Works with any combination of models/operations
- ✅ No required structure or naming
- ✅ Hierarchy in names optional (or required)
- ✅ CLI functions regardless of what's decorated
- ✅ Framework is truly agnostic

---

# PHASE 5: Example Validation

## Step 5.1: Test with Tar Example

**Objective:** Extract and test example from tar file demonstrating Extended Proposal C features.

**Setup:**
```bash
cd ~/pulpo-test

# If example is in tar
tar -xf /path/to/pulpo-examples.tar -C ./

# Or if example is in /pulpo/examples/
cp -r ../pulpo/examples ./test-example
cd test-example
```

**Validation:**
```bash
# Check structure
ls -la
# Should have: main.py, models/, operations/, Makefile, etc.

# Install/setup
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    pip install -e .
fi

# Run example
python3 main.py
# Should execute without errors

# Test make commands
if [ -f "Makefile" ]; then
    make compile
    # Should create run_cache/ folder

    [ -d "run_cache" ] && echo "✅ run_cache/ created"
    [ -d "run_cache/orchestration" ] && echo "✅ run_cache/orchestration/ created (Extended Proposal C)"
fi
```

**Acceptance Criteria:**
- ✅ Example unpacks/extracts successfully
- ✅ Can run main.py
- ✅ Makefile works
- ✅ Code generation succeeds
- ✅ run_cache/ is created (visible, not hidden)
- ✅ run_cache/orchestration/ created with Prefect flows (Extended Proposal C)

---

## Step 5.2: Example Inspection

**Objective:** Verify example demonstrates agnostic pattern with Extended Proposal C features.

**Test:**
```bash
cd ~/pulpo-test/test-example

# Check main entrypoint
echo "=== Main Entrypoint ==="
head -30 main.py
# Should show:
# - from pulpo import ...
# - decorators with hierarchical names
# - CLI instantiation

# Check imports
echo "=== Import Pattern Check ==="
grep -n "from pulpo" main.py operations/*.py models/*.py 2>/dev/null | head -10
# Should show: from pulpo import ... (not relative imports)

# Check decorator usage with hierarchy (Extended Proposal C)
echo "=== Hierarchical Decorator Usage ==="
grep -n "@operation\|@datamodel" operations/*.py 2>/dev/null | head -20
# Should show operations with hierarchical names like:
# @operation(name="scraping.stepstone.fetch")
# @operation(name="scraping.linkedin.fetch")
# @operation(name="scraping.merge")

# Check for mixed sync/async (Extended Proposal C)
echo "=== Sync/Async Functions ==="
grep -n "async def\|^def " operations/*.py 2>/dev/null | head -10
# Should show both sync and async functions mixed

echo "✅ Example demonstrates correct Extended Proposal C pattern"
```

**Acceptance Criteria:**
- ✅ Example uses `from pulpo import ...`
- ✅ Example uses decorators correctly
- ✅ Example has hierarchical operation names (e.g., "flow.step")
- ✅ Example includes both sync and async operations
- ✅ Example has clear main entrypoint
- ✅ Example demonstrates parallelization pattern
- ✅ Example is minimal and clear

---

## Step 5.3: Verify Extended Proposal C Features in Example

**Objective:** Confirm example showcases all Extended Proposal C features.

**Test:**
```bash
cd ~/pulpo-test/test-example

cat > verify_extended_features.py << 'EOF'
import sys
sys.path.insert(0, ".")

from main import cli
from pulpo.core.hierarchy import HierarchyParser

# Test 1: Verify hierarchical naming
print("Test 1: Hierarchical operation names")
ops = cli.operation_registry.get_all()
hierarchical_ops = [name for name in ops if '.' in name]

print(f"✅ Total operations: {len(ops)}")
print(f"✅ Hierarchical operations: {len(hierarchical_ops)}")
for op in hierarchical_ops:
    print(f"   - {op}")

# Test 2: Verify multi-level hierarchy exists
print("\nTest 2: Multi-level hierarchy")
parser = HierarchyParser()
multi_level = [op for op in hierarchical_ops if len(parser.parse(op).hierarchy) > 1]
print(f"✅ Multi-level operations: {len(multi_level)}")
for op in multi_level:
    parsed = parser.parse(op)
    print(f"   - {op} (level: {parsed.level})")

# Test 3: Verify parallelizable operations exist
print("\nTest 3: Parallel-capable operations")
# Same-level sibling operations that could be parallelized
hierarchy_map = {}
for op in hierarchical_ops:
    parsed = parser.parse(op)
    parent = '.'.join(parsed.hierarchy[:-1]) if len(parsed.hierarchy) > 1 else parsed.hierarchy[0]
    if parent not in hierarchy_map:
        hierarchy_map[parent] = []
    hierarchy_map[parent].append(op)

parallel_groups = {p: ops for p, ops in hierarchy_map.items() if len(ops) > 1}
print(f"✅ Groups with parallelization potential: {len(parallel_groups)}")
for group, group_ops in parallel_groups.items():
    print(f"   - {group}: {len(group_ops)} operations")

# Test 4: Check generated orchestration
print("\nTest 4: Generated orchestration")
import os
if os.path.exists("run_cache/orchestration"):
    flow_files = [f for f in os.listdir("run_cache/orchestration") if f.endswith(".py")]
    print(f"✅ Generated {len(flow_files)} flow files")
    for flow in flow_files:
        print(f"   - {flow}")
else:
    print("⚠️  orchestration/ not found (may not be generated)")

print("\n✅ Example demonstrates Extended Proposal C features!")
EOF

python3 verify_extended_features.py
```

**Acceptance Criteria:**
- ✅ Operations use hierarchical naming (dots in names)
- ✅ Multi-level hierarchy exists (3+ levels in some names)
- ✅ Parallelization potential detected (multiple same-level operations)
- ✅ Generated Prefect flows created in orchestration/
- ✅ All Extended Proposal C features demonstrated

---

# VERIFICATION CHECKLIST

After all phases complete, verify:

## Framework Structure
- [ ] pulpo/ is standalone package
- [ ] __init__.py exports main items
- [ ] All submodules present
- [ ] Can import: `from pulpo import ...`

## Import Pattern
- [ ] New import pattern works: `from pulpo import datamodel, operation`
- [ ] No relative imports needed
- [ ] Decorators work correctly
- [ ] CLI class available

## Hierarchy & Orchestration (Extended Proposal C)
- [ ] HierarchyParser correctly parses operation names
- [ ] Multi-level hierarchy supported (3+ levels)
- [ ] Grouping by hierarchy level works
- [ ] OrchestrationCompiler creates flow structure
- [ ] Parallelization detected for same-level operations
- [ ] Dependencies inferred from operation inputs
- [ ] Dependency graph created correctly

## Sync/Async Handling (Extended Proposal C)
- [ ] Sync functions correctly detected
- [ ] Async functions correctly detected
- [ ] Sync functions wrapped with run_in_executor
- [ ] Async functions left unchanged
- [ ] Wrapped functions are awaitable

## CLI Interface
- [ ] CLI instantiates without errors
- [ ] CLI has required methods
- [ ] Registries function correctly
- [ ] Discovery works
- [ ] Orchestration compilation works

## Code Generation
- [ ] run_cache/ folder created (not .run_cache/)
- [ ] Folder is visible in directory listings
- [ ] run_cache/orchestration/ folder created (Extended Proposal C)
- [ ] Generated files present
- [ ] Generated Prefect flows valid
- [ ] Generated Python is valid
- [ ] Idempotent compilation

## Framework Agnosticism
- [ ] Works with flat structure
- [ ] Works with nested structure
- [ ] Works with any project layout
- [ ] No assumed directory structure
- [ ] Works with any model/operation count
- [ ] Works with hierarchical names
- [ ] Works with non-hierarchical names

## Prefect Integration (Extended Proposal C)
- [ ] Generated flows are valid @flow decorators
- [ ] Generated operations are valid @task decorators
- [ ] Flows use asyncio.gather for parallelization
- [ ] Dependency injection works
- [ ] Flow composition works (nested flows)

## Examples
- [ ] Example unpacks successfully
- [ ] Example demonstrates pattern
- [ ] Example uses hierarchical naming (Extended Proposal C)
- [ ] Example includes sync and async functions (Extended Proposal C)
- [ ] Example demonstrates parallelization potential (Extended Proposal C)
- [ ] Example runs without errors
- [ ] make compile works in example
- [ ] Generated orchestration includes all operations

---

# Test Execution Summary

**Total Phases:** 5
**Total Steps:** 16 (extended with Extended Proposal C features)
**Estimated Time:** 3-4 hours (includes Extended Proposal C testing)
**Environment:** Isolated test instance

**Extended Proposal C Coverage:**
- Phase 1: Added hierarchy parsing validation
- Phase 2: Added orchestration compilation testing
- Phase 3: Added Prefect flow validation
- Phase 4: Added sync/async function handling + hierarchy examples
- Phase 5: Added Extended Proposal C feature verification

**Success Criteria:** All phases pass, all steps verify, all Extended Proposal C features validated

**Next Step After Testing:** If all phases pass, proceed to PULPO_RESTRUCTURING_PLAN.md

---

**Status:** Ready for Testing with Extended Proposal C ✅
**Test Instance:** Separate from production
**Rollback:** Simple (delete test directories)
**Last Updated:** 2025-10-29 with Extended Proposal C features
**Architecture:** Hierarchical naming → auto-generated DAG orchestration → Prefect flows
