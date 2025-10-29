# Phase 2: Prefect Integration - Discussion & Planning

**Current Status:** Ready to design Phase 2 implementation
**Architecture:** Extended Proposal C - Hierarchical naming with auto-generated Prefect orchestration

---

## What Phase 2 Needs to Accomplish

### Goal
Enable automatic Prefect flow generation from hierarchical operation naming.

Users write:
```python
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(): ...

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(): ...

@operation(name="scraping.merge")
async def merge(stepstone, linkedin): ...
```

Framework automatically generates:
```python
# run_cache/orchestration/scraping_flow.py
@flow
async def scraping_flow():
    # Parallel execution of same-level tasks
    stepstone_result, linkedin_result = await asyncio.gather(
        fetch_stepstone_task(),
        fetch_linkedin_task(),
    )
    # Dependency injection from operation signatures
    return await merge_task(stepstone_result, linkedin_result)
```

---

## Components to Build

### 1. Hierarchy Parser (`core/hierarchy.py`)

**Purpose:** Parse operation names into hierarchical structure

**Input:** Operation name like `"scraping.stepstone.fetch"`
**Output:**
```python
{
    "full_name": "scraping.stepstone.fetch",
    "hierarchy": ["scraping", "stepstone", "fetch"],
    "level": 3,
    "step": "fetch",
    "parent": "scraping.stepstone"
}
```

**Key Methods:**
- `parse(name: str) -> ParsedName` - Parse single name
- `group_by_parent(names: List[str]) -> Dict[str, List[str]]` - Group siblings
- `get_level(name: str) -> int` - Get nesting level
- `find_dependencies(names: List[str]) -> Dict[str, List[str]]` - Find parallel groups

**Questions for Discussion:**
1. Should we support flat names (no dots) or require hierarchy?
2. What's the maximum nesting level we should support?
3. How to detect which operations are parallelizable?

---

### 2. Orchestration Compiler (`core/orchestration/compiler.py`)

**Purpose:** Generate Prefect flow code from operation registry

**Inputs:**
- ModelRegistry (for validation)
- OperationRegistry (for operations to orchestrate)
- HierarchyParser (for parsing names)

**Output:** Generated Prefect @flow/@task Python code

**Key Classes:**
- `OrchestrationCompiler` - Main compiler
- `FlowGroup` - Represents a @flow with its @tasks
- `Orchestration` - Complete flow structure

**Logic Flow:**
1. Parse all operation names into hierarchy
2. Group by parent (same-level operations)
3. Detect parallelizable groups (no dependencies)
4. Build dependency graph from operation input/output types
5. Generate Prefect code from structure

**Questions for Discussion:**
1. How to infer dependencies from operation signatures?
   - Option A: By input/output type matching
   - Option B: By explicit dependency hints in decorator
   - Option C: Both?
2. How to handle operations with multiple inputs?
3. How to handle mixed sync/async operations in same flow?

---

### 3. Sync/Async Detector (`core/orchestration/sync_async.py`)

**Purpose:** Handle sync functions in async Prefect flows

**Problem:** Prefect flows are async, but users may write sync operations

**Solution:** Wrap sync functions with `run_in_executor`

**Key Methods:**
- `is_async(func: Callable) -> bool` - Check if async
- `wrap_if_sync(func: Callable) -> Callable` - Wrap sync to async
- `detect_and_wrap(func: Callable) -> Callable` - Auto-detect and wrap

**Example:**
```python
# User writes sync function
@operation(name="parsing.clean")
def clean_text(text: str) -> str:
    return text.strip()

# Framework wraps it
async def clean_text_wrapped(text: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, clean_text, text)

# Used in Prefect flow
@task
async def clean_text_task(text: str) -> str:
    return await clean_text_wrapped(text)
```

**Questions for Discussion:**
1. Should we auto-detect or require explicit async marking?
2. How to handle sync operations that are CPU-bound vs I/O-bound?
3. Should we add a parameter to control threading vs process pool?

---

### 4. Code Generation Templates

**Purpose:** Generate valid, readable Prefect flow Python code

**Locations:**
- `templates/` or embedded in compiler

**Template Variables:**
- Flow name (from hierarchy parent)
- Tasks (operations at this level)
- Dependencies
- Inputs/outputs

**Example Output Structure:**
```python
# run_cache/orchestration/scraping.py
"""Auto-generated Prefect flow for scraping operations."""

from prefect import flow, task
import asyncio

@task
async def fetch_stepstone_task(keywords: str) -> dict:
    """Wrapped task for scraping.stepstone.fetch"""
    # Import and call original operation
    from user_project import fetch_stepstone
    return await fetch_stepstone(keywords)

@task
async def fetch_linkedin_task(keywords: str) -> dict:
    """Wrapped task for scraping.linkedin.fetch"""
    from user_project import fetch_linkedin
    return await fetch_linkedin(keywords)

@task
async def merge_task(stepstone: dict, linkedin: dict) -> dict:
    """Wrapped task for scraping.merge"""
    from user_project import merge
    return await merge(stepstone, linkedin)

@flow
async def scraping_flow(keywords: str) -> dict:
    """Auto-generated flow for scraping operations"""
    # Parallel execution
    stepstone, linkedin = await asyncio.gather(
        fetch_stepstone_task(keywords),
        fetch_linkedin_task(keywords),
    )
    # Sequential with dependencies
    return await merge_task(stepstone, linkedin)

if __name__ == "__main__":
    scraping_flow("python jobs")
```

**Questions for Discussion:**
1. Should generated code be human-readable or minimal?
2. How to handle imports (direct vs lazy)?
3. Should flows be executable standalone or require orchestrator?

---

### 5. Integration: `compile()` Method

**Current:** `cli.compile()` calls `compile_all()` which generates API/UI

**Needed:** Also generate Prefect flows

**Changes:**
```python
def compile(self):
    # Existing code
    from .codegen import compile_all
    compile_all()

    # NEW: Generate Prefect flows
    compiler = OrchestrationCompiler(self.model_registry, self.operation_registry)
    orchestration = compiler.compile()

    # Generate flow code to run_cache/orchestration/
    self._generate_prefect_flows(orchestration)
```

**Questions for Discussion:**
1. Where exactly should flows be generated?
   - Option A: `run_cache/orchestration/` (one file per flow)
   - Option B: `run_cache/orchestration.py` (all flows in one file)
   - Option C: Other structure?
2. Should flows be importable or just for Prefect server?

---

### 6. Integration: `prefect()` Method

**Current:** Placeholder that prints "not implemented"

**Needed:** Actually start Prefect with generated flows

**Possible Approaches:**

**Approach A: Use Prefect Server**
```python
def prefect(self):
    self._ensure_compiled()

    # Start Prefect server
    import subprocess
    subprocess.run(["prefect", "server", "start"])
```

**Approach B: Deploy Flows to Prefect Cloud**
```python
def prefect(self):
    self._ensure_compiled()

    # Import and deploy flows
    from run_cache.orchestration import all_flows
    for flow in all_flows:
        flow.deploy(...)
```

**Approach C: Run Flows Directly**
```python
def prefect(self):
    self._ensure_compiled()

    # Import and run a flow
    from run_cache.orchestration import scraping_flow
    result = scraping_flow.run()
```

**Approach D: Interactive Flow Selection**
```python
def prefect(self):
    self._ensure_compiled()

    # List available flows
    flows = self._discover_flows()
    # Let user choose which to run
    # Execute selected flow
```

**Questions for Discussion:**
1. Which approach makes most sense for user experience?
2. Should there be a separate command for each flow or a menu?
3. How to pass inputs to flows from CLI?

---

## Key Design Questions

Before implementation, we need to discuss:

### A. Dependency Detection
How should we know that `merge()` depends on `fetch_stepstone()` and `fetch_linkedin()`?

**Options:**
1. **Type-based:** If `merge(stepstone: dict, linkedin: dict)` and fetches return dict, infer dependency
2. **Name-based:** If parameter names match operation names, infer dependency
3. **Explicit hints:** Add `@operation(depends_on=["scraping.stepstone.fetch", "scraping.linkedin.fetch"])`
4. **Hierarchy-based:** Just by hierarchy (same parent = dependency)
5. **Smart hybrid:** Combination of above

**Recommendation:** ?

### B. Operation Imports
How to import user's original operations in generated flow code?

**Options:**
1. **Direct import:** Assume operations are importable from user module
2. **Registry lookup:** Look up operation function from OperationRegistry at runtime
3. **Embed wrapper:** Generate wrapper that calls operation directly
4. **Discovery-based:** Auto-discover where operations are defined

**Recommendation:** ?

### C. Flow Granularity
Should we generate one flow per operation or group by parent?

**Options:**
1. **One per parent:** `scraping_flow` for all scraping.* operations
2. **One per operation:** `scraping_stepstone_fetch_flow` for each
3. **Top-level only:** One root flow orchestrating everything
4. **Configurable:** User-controlled via hints

**Recommendation:** ?

### D. Error Handling
How to handle errors in generated flows?

**Options:**
1. **Default Prefect:** Let Prefect handle retries/failures
2. **Custom hooks:** Add error handling callbacks
3. **Transaction-like:** All-or-nothing execution
4. **Partial:** Continue with partial results

**Recommendation:** ?

### E. Testing Generated Flows
How should users test generated Prefect flows?

**Options:**
1. **Unit test** - Test individual @task functions
2. **Integration test** - Run entire @flow with mocks
3. **End-to-end** - Run with real operations
4. **Snapshot test** - Compare generated code

**Recommendation:** ?

---

## Implementation Sequence

**Suggested order:**
1. Start with **Hierarchy Parser** (simplest, no dependencies)
2. Move to **Sync/Async Detector** (needed for task generation)
3. Implement **Orchestration Compiler** (core logic)
4. Create **Code Templates** (generate the actual code)
5. Wire **compile()** method (integrate into CLI)
6. Wire **prefect()** method (user-facing interface)

---

## Questions for You

Before we start coding, let's discuss:

1. **Dependency detection:** Which option do you prefer (type-based, name-based, explicit, hierarchy, or hybrid)?

2. **Operation imports:** How should generated flows import user operations?

3. **Flow structure:** One flow per parent or per operation?

4. **Execution model:** Should `cli.prefect()` start a server or run flows directly?

5. **Test strategy:** How should users test the generated flows?

6. **Flat operations:** Should we support operations without dots (e.g., just `"my_op"`) or require hierarchy?

7. **Maximum nesting:** Any limit on hierarchy depth (e.g., max 5 levels)?

---

## Success Criteria for Phase 2

✅ When Phase 2 is complete:
- [ ] Hierarchy parser correctly parses operation names
- [ ] Orchestration compiler builds correct dependency graphs
- [ ] Sync/async detector wraps functions correctly
- [ ] Generated Prefect code is valid Python
- [ ] `cli.compile()` generates flows to run_cache/orchestration/
- [ ] `cli.prefect()` successfully starts Prefect with generated flows
- [ ] Test suite passes (when we do Phase 3)
- [ ] Example with hierarchical operations works end-to-end

---

Let's discuss these points and finalize the design before we start coding!
