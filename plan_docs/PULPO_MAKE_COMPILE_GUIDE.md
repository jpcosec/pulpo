# Make Compile Implementation Guide

**Purpose:** Deep dive into how `make compile` generates Prefect orchestration from Extended Proposal C
**Target:** Framework developers and advanced users
**Status:** Complete implementation guide
**Date:** 2025-10-29

---

## Overview

When a user runs `make compile` in a PulpoCore project, the following happens automatically:

```
make compile
    ↓
1. CLI.discover()           → Find all @operation and @datamodel decorators
2. HierarchyParser          → Parse "flow.step" naming into structure
3. OrchestrationCompiler    → Build DAG and detect parallelization
4. SyncAsyncDetector        → Wrap sync functions with run_in_executor
5. PrefectCodeGenerator     → Generate @flow/@task Python files
6. Write to run_cache/      → Save all generated code
```

---

## Part 1: Makefile Integration

### Standard Makefile Target

```makefile
.PHONY: compile

compile:
	python3 -c "from pulpo.core.cli import CLI; cli = CLI(); cli.compile()"
```

### Alternative (Explicit entry point):

```makefile
compile:
	python3 main.py --compile
```

### What the user sees:

```bash
$ make compile
✅ Discovering operations...
✅ Parsing hierarchy...
✅ Building orchestration...
✅ Generating Prefect code...
✅ Generated run_cache/ (42 files)
```

---

## Part 2: CLI.compile() Implementation

The CLI's compile method orchestrates the entire process:

```python
# In pulpo/core/cli.py

class CLI:
    def compile(self):
        """Compile operations into Prefect orchestration and code artifacts."""

        print("✅ Discovering operations...")
        self.discover()  # Find all decorated items

        print("✅ Parsing hierarchy...")
        orchestration = self._build_orchestration()

        print("✅ Generating Prefect code...")
        generated_code = self._generate_code(orchestration)

        print("✅ Writing artifacts...")
        self._write_artifacts(generated_code)

        print(f"✅ Generated run_cache/ ({len(generated_code)} files)")

    def _build_orchestration(self):
        """Build orchestration from discovered operations."""
        from pulpo.core.orchestration import OrchestrationCompiler
        compiler = OrchestrationCompiler(self)
        return compiler.compile()

    def _generate_code(self, orchestration):
        """Generate Prefect code from orchestration."""
        from pulpo.core.codegen.prefect_codegen import PrefectCodeGenerator
        generator = PrefectCodeGenerator(orchestration)
        return generator.generate_all()

    def _write_artifacts(self, code_dict):
        """Write all generated code to run_cache/."""
        import os
        os.makedirs("run_cache/orchestration", exist_ok=True)

        for filename, content in code_dict.items():
            filepath = f"run_cache/orchestration/{filename}"
            with open(filepath, 'w') as f:
                f.write(content)
```

---

## Part 3: Hierarchy Parsing

### Input Example

User defines operations with hierarchical names:

```python
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(keywords: str) -> RawJobs: ...

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(keywords: str) -> RawJobs: ...

@operation(name="scraping.merge")
async def merge_results(stepstone: RawJobs, linkedin: RawJobs) -> RawJobs: ...
```

### Parsing Process

```python
# In pulpo/core/hierarchy.py

class HierarchyParser:
    """Parse "flow.step.substep" into structured hierarchy."""

    def parse(self, name: str) -> ParsedName:
        """Parse operation name into components."""
        parts = name.split(".")

        return ParsedName(
            full_name=name,
            hierarchy=parts,        # ["scraping", "stepstone", "fetch"]
            level=len(parts),       # 3
            step=parts[-1],         # "fetch"
            parent=".".join(parts[:-1]),  # "scraping.stepstone"
        )

    def group_by_parent(self, names: List[str]) -> Dict[str, List[str]]:
        """Group operations by parent flow."""
        groups = {}

        for name in names:
            parent = self.parse(name).parent

            if parent not in groups:
                groups[parent] = []

            groups[parent].append(name)

        return groups

# Example output:
# {
#     "scraping.stepstone": ["scraping.stepstone.fetch"],
#     "scraping.linkedin": ["scraping.linkedin.fetch"],
#     "scraping": ["scraping.merge"],
# }
```

### Key Insight

The hierarchy creates a **natural DAG structure** without users writing any graph logic!

---

## Part 4: Orchestration Compilation

### Building Flows

```python
# In pulpo/core/orchestration/compiler.py

class OrchestrationCompiler:
    """Compile operations into Prefect flow structure."""

    def compile(self) -> Orchestration:
        """Build orchestration from all discovered operations."""

        operations = self.operation_registry.get_all()
        parser = HierarchyParser()

        # Step 1: Group by parent
        flows = {}
        for op_name in operations:
            parsed = parser.parse(op_name)
            parent = parsed.parent

            if parent not in flows:
                flows[parent] = FlowGroup(parent)

            flows[parent].add_operation(op_name, parsed)

        # Step 2: Detect dependencies
        self._detect_dependencies(flows, operations)

        # Step 3: Detect parallelization
        self._detect_parallelization(flows)

        return Orchestration(flows, self.operation_registry)

    def _detect_dependencies(self, flows, operations):
        """Infer dependencies from operation signatures."""

        for op_name in operations:
            op_func = self.operation_registry.get_function(op_name)

            # Get input parameters
            sig = inspect.signature(op_func)
            params = list(sig.parameters.keys())

            # Map to upstream operations
            dependencies = []
            for param in params:
                # Look for operation that produces this type
                for other_op in operations:
                    if other_op == op_name:
                        continue

                    other_func = self.operation_registry.get_function(other_op)
                    output_type = self._get_return_type(other_func)

                    if self._types_compatible(param, output_type):
                        dependencies.append(other_op)

            # Store dependencies
            self.operation_registry.set_dependencies(op_name, dependencies)

    def _detect_parallelization(self, flows):
        """Detect operations that can run in parallel."""

        for flow_name, flow_group in flows.items():
            # Get operations at same level
            ops = list(flow_group.operations.keys())

            # Find operations with no dependencies on each other
            parallel_groups = []
            for i, op1 in enumerate(ops):
                for op2 in ops[i+1:]:
                    deps1 = self.operation_registry.get_dependencies(op1)
                    deps2 = self.operation_registry.get_dependencies(op2)

                    # Can parallelize if no cross-dependencies
                    if op2 not in deps1 and op1 not in deps2:
                        parallel_groups.append((op1, op2))

            flow_group.parallel_groups = parallel_groups
```

### Output Example

```python
Orchestration(
    flows={
        "scraping": FlowGroup(
            name="scraping",
            operations={
                "scraping.merge": ParsedName(...),
            },
            parallel_groups=[
                ("scraping.stepstone.fetch", "scraping.linkedin.fetch"),
            ],
        ),
        "scraping.stepstone": FlowGroup(
            name="scraping.stepstone",
            operations={
                "scraping.stepstone.fetch": ParsedName(...),
            },
        ),
    }
)
```

---

## Part 5: Sync/Async Handling

### Detection

```python
# In pulpo/core/orchestration/sync_async.py

class SyncAsyncDetector:
    """Detect and handle sync/async functions transparently."""

    def is_async(self, func: Callable) -> bool:
        """Check if function is async."""
        return inspect.iscoroutinefunction(func)

    def analyze(self, operation_registry):
        """Analyze all operations for sync/async."""

        analysis = {}

        for op_name in operation_registry.get_all():
            func = operation_registry.get_function(op_name)

            analysis[op_name] = {
                "is_async": self.is_async(func),
                "needs_wrapper": not self.is_async(func),
            }

        return analysis
```

### Wrapping at Code Generation

```python
# Example: User wrote sync function
@operation(name="parsing.clean")
def clean_text(text: str) -> str:
    return text.strip().lower()

# Framework generates:
from prefect import task
import asyncio

@task
async def clean_text_wrapper(text: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, clean_text, text)
```

---

## Part 6: Prefect Code Generation

### Template System

```python
# In pulpo/core/codegen/prefect_codegen.py

FLOW_TEMPLATE = '''
from prefect import flow, task
import asyncio

{task_definitions}

@flow(name="{flow_name}")
async def {flow_var_name}({parameters}):
    """{docstring}"""

    {task_calls}

    return {return_value}
'''

TASK_TEMPLATE = '''
@task
async def {task_name}({parameters}):
    """{docstring}"""

    {task_body}

    return {return_value}
'''

PARALLEL_TASK_TEMPLATE = '''
@task
async def {task_group_name}({parameters}):
    """{docstring}"""

    results = await asyncio.gather(
        {task_call_1}({args_1}),
        {task_call_2}({args_2}),
        # ... more parallel tasks
    )

    return results
'''
```

### Code Generation Process

```python
class PrefectCodeGenerator:
    """Generate valid Prefect code from orchestration."""

    def generate_all(self) -> Dict[str, str]:
        """Generate all flow and task files."""

        code_files = {}

        for flow_name, flow_group in self.orchestration.flows.items():
            # Generate flow file
            flow_code = self.generate_flow(flow_group)
            code_files[f"{flow_name}_flow.py"] = flow_code

            # Generate task files
            for op_name in flow_group.operations:
                task_code = self.generate_task(op_name)
                code_files[f"{op_name}_task.py"] = task_code

        return code_files

    def generate_flow(self, flow_group: FlowGroup) -> str:
        """Generate @flow decorated function."""

        # Get flow parameters and body
        parameters = self._get_parameters(flow_group)
        task_calls = self._get_task_calls(flow_group)
        return_value = self._get_return_value(flow_group)

        # Generate parallel sections if needed
        if flow_group.parallel_groups:
            task_calls = self._generate_parallel_section(
                flow_group.parallel_groups
            )

        # Render template
        return FLOW_TEMPLATE.format(
            flow_name=flow_group.name,
            parameters=parameters,
            task_calls=task_calls,
            return_value=return_value,
            docstring=f"Auto-generated flow: {flow_group.name}",
        )
```

---

## Part 7: Complete Example

### User Code

```python
# main.py
from pulpo import datamodel, operation, CLI

@datamodel(name="RawJobs")
class RawJobs:
    jobs: list

@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(keywords: str) -> RawJobs:
    """Fetch from Stepstone"""
    jobs = await scrape_stepstone_api(keywords)
    return RawJobs(jobs=jobs)

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(keywords: str) -> RawJobs:
    """Fetch from LinkedIn"""
    jobs = await scrape_linkedin_api(keywords)
    return RawJobs(jobs=jobs)

@operation(name="scraping.merge")
async def merge_results(stepstone: RawJobs, linkedin: RawJobs) -> RawJobs:
    """Merge results from parallel operations"""
    all_jobs = stepstone.jobs + linkedin.jobs
    return RawJobs(jobs=list(set(all_jobs)))

@operation(name="parsing.clean_text")
def clean_title(title: str) -> str:
    """Sync function - auto-wrapped"""
    return title.strip().lower()

cli = CLI()

if __name__ == "__main__":
    cli.run()
```

### Generated Code (run_cache/orchestration/)

```python
# scraping_flow.py (generated)
from prefect import flow, task
import asyncio

@task
async def scraping_stepstone_fetch_task(keywords: str):
    """Auto-generated task wrapper"""
    from main import fetch_stepstone
    return await fetch_stepstone(keywords)

@task
async def scraping_linkedin_fetch_task(keywords: str):
    """Auto-generated task wrapper"""
    from main import fetch_linkedin
    return await fetch_linkedin(keywords)

@task
async def scraping_merge_task(stepstone, linkedin):
    """Auto-generated task wrapper"""
    from main import merge_results
    return await merge_results(stepstone, linkedin)

@flow(name="scraping")
async def scraping_flow(keywords: str):
    """Auto-generated flow with parallel fetch operations"""

    # Parallel execution detected
    stepstone_result, linkedin_result = await asyncio.gather(
        scraping_stepstone_fetch_task(keywords),
        scraping_linkedin_fetch_task(keywords),
    )

    # Merge results
    final_result = await scraping_merge_task(stepstone_result, linkedin_result)

    return final_result
```

```python
# parsing_flow.py (generated)
from prefect import flow, task
import asyncio

@task
async def parsing_clean_text_task(title: str):
    """Auto-generated task for sync function"""
    from main import clean_title
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, clean_title, title)

@flow(name="parsing")
async def parsing_flow(title: str):
    """Auto-generated flow"""

    cleaned = await parsing_clean_text_task(title)
    return cleaned
```

---

## Part 8: Algorithm Details

### Dependency Inference

The compiler infers dependencies from function signatures:

```python
# User writes:
@operation(name="scraping.merge")
async def merge(stepstone: RawJobs, linkedin: RawJobs) -> RawJobs:
    ...

# Framework infers:
# - This operation needs 2 RawJobs inputs
# - "scraping.stepstone.fetch" produces RawJobs
# - "scraping.linkedin.fetch" produces RawJobs
# - These are dependencies!

# Generated dependency graph:
#   stepstone.fetch ──┐
#                     ├─→ merge
#   linkedin.fetch ───┘
```

### Parallelization Detection Algorithm

```
For each parent flow:
    1. Get all child operations
    2. For each pair of operations:
        a. Get their dependencies
        b. Check if they depend on each other
        c. If NO mutual dependencies → can parallelize
    3. Build parallel groups from compatible operations
    4. Generate asyncio.gather() for parallel group
```

### Code Generation Order

```
1. Extract operation signatures and types
2. Detect sync vs async
3. Group by parent flow (hierarchy)
4. Detect parallelization
5. Infer dependencies
6. Generate task wrappers
7. Generate flow orchestrators
8. Write to run_cache/
```

---

## Part 9: Edge Cases and Handling

### Case 1: Sync Function

```python
@operation(name="parsing.clean")
def clean(text: str) -> str:  # Sync, no async
    return text.lower()

# Generated:
@task
async def parsing_clean_task(text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, clean, text)
```

### Case 2: Multiple Return Types

```python
@operation(name="validate.check")
async def check(job: Job) -> ValidatedJob:
    ...

@operation(name="validate.log")
async def log(result: ValidatedJob) -> None:
    ...

# Dependencies correctly inferred based on ValidatedJob type
```

### Case 3: No Hierarchy (Flat Names)

```python
@operation(name="validate")
@operation(name="transform")
@operation(name="save")

# Still works! Generated as single-level flow
# with sequential execution (no parallelization)
```

### Case 4: Deep Hierarchy

```python
@operation(name="scraping.stepstone.fetch.parse")
@operation(name="scraping.stepstone.fetch.clean")

# Creates deeply nested flows
# run_cache/orchestration/scraping/stepstone/fetch/...
```

---

## Part 10: Performance Considerations

### Parallelization Benefit

```
Without parallelization (sequential):
  fetch_stepstone (1 sec) → merge (0.5 sec) = 1.5 sec total

With parallelization (parallel):
  fetch_stepstone (1 sec) ──┐
                             ├→ merge (0.5 sec) = 1.5 sec total
  fetch_linkedin  (1 sec) ──┘

Total time: max(1, 1) + 0.5 = 1.5 sec (same in this case)
But with 3 sources:
  Without: 1 + 1 + 1 + 0.5 = 3.5 sec
  With:    max(1, 1, 1) + 0.5 = 1.5 sec (2.3x faster!)
```

### Optimization Opportunities

1. **Lazy generation** - Only generate flows actually used
2. **Caching** - Cache compiled flows between runs
3. **Incremental** - Only regenerate changed operations
4. **Prefect optimizations** - Leverage Prefect's built-in optimization

---

## Summary

The `make compile` process transforms:
- **User decorators** → Parsed hierarchy → **Orchestration graph** → **Prefect flows**

All without the user writing any orchestration code!

Key features:
- ✅ Hierarchical naming creates DAG automatically
- ✅ Parallelization detected from dependencies
- ✅ Sync functions wrapped transparently
- ✅ Multi-level hierarchy support
- ✅ All code generated and verified
- ✅ Zero boilerplate needed

---

**File created:** 2025-10-29
**Purpose:** Implementation reference for framework developers
**Related:** PULPO_TESTING_PLAN.md, PULPO_RESTRUCTURING_PLAN.md
