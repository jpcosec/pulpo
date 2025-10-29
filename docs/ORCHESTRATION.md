# Prefect Orchestration

**Version:** 1.0.0
**Date:** 2025-10-15

## Table of Contents

1. [Overview](#overview)
2. [When to Use Orchestration](#when-to-use-orchestration)
3. [The Three Execution Layers](#the-three-execution-layers)
4. [Architecture Integration](#architecture-integration)
5. [Operations: The Foundation](#operations-the-foundation)
6. [Prefect Tasks: Orchestration Wrappers](#prefect-tasks-orchestration-wrappers)
7. [Prefect Flows: Complete Workflows](#prefect-flows-complete-workflows)
8. [TaskRun + Prefect Integration](#taskrun--prefect-integration)
9. [Real-World Examples](#real-world-examples)
10. [Deployment & Scheduling](#deployment--scheduling)
11. [Best Practices](#best-practices)

---

## Overview

JobHunter uses **Prefect** as an optional orchestration layer for complex multi-step workflows. Operations can run standalone (via API, CLI) OR be orchestrated through Prefect flows.

### Key Concept

```
Operations = Reusable business logic
Prefect Tasks = Orchestration wrappers
Prefect Flows = Complete workflows
```

**Operations work in THREE modes:**

1. **Direct execution** - API/CLI calls operation directly
2. **Orchestrated** - Prefect flow calls operation via task wrapper
3. **Scheduled** - Prefect runs flows on schedule (daily, hourly, etc.)

---

## When to Use Orchestration

### Use Prefect When You Need:

✅ **Multi-step workflows**
- Scrape → Process → Match → Apply (4 steps)
- Each step depends on previous results
- Want to visualize entire workflow

✅ **Retry logic**
- Network requests that might fail
- External API calls (rate limits, timeouts)
- Want automatic retries with backoff

✅ **Scheduling**
- Daily job scraping at 8 AM
- Weekly CV generation
- Monthly cleanup tasks

✅ **Parallel execution**
- Scrape multiple job boards simultaneously
- Process 100 jobs in parallel batches
- Generate CVs for multiple jobs concurrently

✅ **Monitoring & alerts**
- Email notifications on failures
- Slack alerts for critical errors
- Dashboard showing workflow health

### Don't Use Prefect When:

❌ **Simple single operations**
- Creating a single job record
- Updating user profile
- Deleting an item
→ Use direct API/CLI call

❌ **Synchronous CRUD**
- Basic database operations
- Reading/writing single records
→ Use operations directly

❌ **Real-time user requests**
- User clicks button, expects instant response
- Interactive UI actions
→ Use API endpoints directly

---

## The Three Execution Layers

```
┌─────────────────────────────────────────────────┐
│ Layer 3: Prefect Flows (@flow)                  │
│                                                  │
│ Purpose: Complete workflows                     │
│ - Compose multiple tasks                        │
│ - Define execution order                        │
│ - Handle overall logic & branching              │
│ - Schedule periodic runs                        │
│                                                  │
│ Example: daily_job_hunt_flow()                  │
│   → Scrape jobs from 3 sources                  │
│   → Match against user profile                  │
│   → Generate CVs for top matches                │
│   → Auto-apply to best opportunities            │
└──────────────────────┬──────────────────────────┘
                       │ calls
┌──────────────────────▼──────────────────────────┐
│ Layer 2: Prefect Tasks (@task)                  │
│                                                  │
│ Purpose: Orchestration wrappers                 │
│ - Wrap @operation functions                     │
│ - Add retry logic (3x with 60s delay)           │
│ - Define dependencies between steps             │
│ - Enable parallel execution                     │
│                                                  │
│ Example: scrape_jobs_task()                     │
│   → Wraps scrape_jobs() operation               │
│   → Adds retries for network failures           │
│   → Links to Prefect flow context               │
└──────────────────────┬──────────────────────────┘
                       │ calls
┌──────────────────────▼──────────────────────────┐
│ Layer 1: Operations (@operation)                │
│                                                  │
│ Purpose: Core business logic                    │
│ - Pure business logic (scraping, matching, etc) │
│ - Can run standalone OR orchestrated            │
│ - Always create TaskRun audit records           │
│ - Detect Prefect context automatically          │
│                                                  │
│ Example: scrape_jobs()                          │
│   → Scrapes jobs from a source                  │
│   → Returns job IDs                             │
│   → Creates TaskRun for audit                   │
└─────────────────────────────────────────────────┘
```

### Why Three Layers?

**Separation of Concerns:**
- **Operations** = Pure business logic (reusable anywhere)
- **Tasks** = Orchestration concerns (retries, dependencies)
- **Flows** = Workflow composition (steps, branching, scheduling)

**Flexibility:**
- Operations work in API, CLI, or Prefect
- Can change orchestration without touching business logic
- Easy to test operations independently

---

## Architecture Integration

### How Orchestration Fits

```
┌────────────────────────────────────────┐
│ User Interface                         │
│ • Web UI (direct API calls)            │
│ • CLI (direct operation calls)         │
└──────────────────┬─────────────────────┘
                   │
                   │ Direct calls (no orchestration)
                   │
┌──────────────────▼─────────────────────┐
│ API Layer (FastAPI)                    │
│ • POST /operations/{name}              │
│ • Validates input                      │
│ • Calls operation directly             │
└──────────────────┬─────────────────────┘
                   │
                   │
┌──────────────────▼─────────────────────┐
│ Operations (@operation)                │
│ • Core business logic                  │
│ • Detects execution context            │
│ • Creates TaskRun audit record         │
└──────────────────┬─────────────────────┘
                   │
                   ├─→ TaskRun(orchestrated=False)  [Direct]
                   │
                   └─→ TaskRun(orchestrated=True)   [Prefect]
                            ↑
                            │
┌───────────────────────────┴────────────┐
│ Prefect Orchestration (Optional)       │
│                                        │
│ ┌────────────────────────────────┐    │
│ │ Flows (@flow)                  │    │
│ │ • Compose tasks                │    │
│ │ • Schedule runs                │    │
│ └────────┬───────────────────────┘    │
│          │ calls                      │
│ ┌────────▼───────────────────────┐    │
│ │ Tasks (@task)                  │    │
│ │ • Wrap operations              │    │
│ │ • Add retries                  │    │
│ │ • Provide Prefect context      │────┘
│ └────────────────────────────────┘
└────────────────────────────────────────┘
```

### Context Detection

Operations automatically detect if they're running in Prefect:

```python
# From src/core/decorators.py - @operation wrapper

try:
    from prefect.context import FlowRunContext, TaskRunContext

    flow_ctx = FlowRunContext.get()
    task_ctx = TaskRunContext.get()

    if flow_ctx or task_ctx:
        # Running in Prefect!
        orchestrated = True
        prefect_flow_run_id = str(flow_ctx.flow_run.id)
        prefect_task_run_id = str(task_ctx.task_run.id)
    else:
        # Direct execution
        orchestrated = False
except (ImportError, Exception):
    # Prefect not installed or no context
    orchestrated = False

# Create TaskRun with context info
taskrun = TaskRun(
    operation_name="scrape_jobs",
    orchestrated=orchestrated,
    prefect_flow_run_id=prefect_flow_run_id,
    prefect_task_run_id=prefect_task_run_id,
    ...
)
```

---

## Operations: The Foundation

### What is an Operation?

An **operation** is a single reusable async task decorated with `@operation`:

```python
from core.decorators import operation
from pydantic import BaseModel

class ScrapeJobsInput(BaseModel):
    source: str
    keywords: str
    limit: int = 10

class ScrapeJobsOutput(BaseModel):
    success: bool
    job_ids: list[str]
    jobs_created: int

@operation(
    name="scrape_jobs",
    description="Scrape jobs from a source",
    category="scraping",
    inputs=ScrapeJobsInput,
    outputs=ScrapeJobsOutput,
    tags=["scraping", "jobs"],
    async_enabled=True,  # Enable TaskRun tracking
)
async def scrape_jobs(input: ScrapeJobsInput) -> ScrapeJobsOutput:
    """Core scraping logic - works standalone or orchestrated."""

    # Business logic here
    jobs = await scrape_from_source(input.source, input.keywords)

    # Save to database
    job_ids = []
    for job_data in jobs[:input.limit]:
        job = Job(**job_data)
        await job.insert()
        job_ids.append(str(job.id))

    return ScrapeJobsOutput(
        success=True,
        job_ids=job_ids,
        jobs_created=len(job_ids)
    )
```

### Key Features

1. **Type-safe** - Pydantic input/output schemas
2. **Reusable** - Can be called from API, CLI, or Prefect
3. **Observable** - Creates TaskRun for every execution
4. **Context-aware** - Detects Prefect orchestration automatically

### Direct Execution

```python
# From API endpoint
input_data = ScrapeJobsInput(source="stepstone", keywords="Python", limit=10)
result = await scrape_jobs(input_data)
# → Creates TaskRun(orchestrated=False)
```

---

## Prefect Tasks: Orchestration Wrappers

### What is a Prefect Task?

A **task** wraps an operation for orchestration:

```python
from prefect import task
from core.examples.operations.scraping_ops import scrape_jobs, ScrapeJobsInput

@task(
    name="scrape_jobs_task",
    description="Scrape jobs with retry logic",
    retries=3,                    # Retry 3 times on failure
    retry_delay_seconds=60,       # Wait 60s between retries
    timeout_seconds=300,          # 5 minute timeout
    tags=["scraping", "prefect"]
)
async def scrape_jobs_task(
    source: str,
    keywords: str,
    limit: int = 10
) -> ScrapeJobsOutput:
    """Prefect task wrapping scrape_jobs operation.

    Adds:
    - Automatic retries on network failures
    - Timeout protection
    - Prefect context for tracking
    """
    input_data = ScrapeJobsInput(
        source=source,
        keywords=keywords,
        limit=limit
    )

    # Call the operation
    return await scrape_jobs(input_data)
    # → Creates TaskRun(orchestrated=True, prefect_task_run_id="...")
```

### Why Wrap Operations in Tasks?

**Orchestration concerns:**
- ✅ Retry logic (network failures, rate limits)
- ✅ Timeout protection
- ✅ Dependencies between steps
- ✅ Parallel execution
- ✅ Prefect UI visualization

**Business logic stays clean:**
- Operation remains pure business logic
- Can test operation without Prefect
- Can reuse operation in API/CLI

### Task Configuration Options

```python
@task(
    # Identification
    name="scrape_jobs_task",
    description="Scrape jobs with retry logic",
    tags=["scraping", "production"],

    # Retry logic
    retries=3,                      # Number of retries
    retry_delay_seconds=60,         # Delay between retries
    retry_jitter_factor=0.5,        # Add randomness to delay

    # Timeouts
    timeout_seconds=300,            # Task timeout (5 min)

    # Logging
    log_prints=True,                # Capture print statements

    # Results
    persist_result=True,            # Save result for downstream tasks
    result_storage_key="scrape_{date}",

    # Caching (optional)
    cache_key_fn=...,               # Cache function
    cache_expiration=timedelta(hours=1),
)
async def scrape_jobs_task(...):
    ...
```

---

## Prefect Flows: Complete Workflows

### What is a Prefect Flow?

A **flow** composes multiple tasks into a complete workflow:

```python
from prefect import flow
from core.examples.workflows.tasks import (
    scrape_jobs_task,
    process_jobs_task,
    match_jobs_task,
    generate_cvs_task,
    apply_jobs_task,
    notify_task
)

@flow(
    name="daily_job_hunt",
    description="Complete daily job hunting workflow",
    retries=1,                      # Retry entire flow once on failure
    timeout_seconds=3600,           # 1 hour timeout for entire flow
    log_prints=True,
    tags=["production", "scheduled"]
)
async def daily_job_hunt_flow(
    user_id: str,
    keywords: list[str],
    sources: list[str],
    auto_apply: bool = False,
    match_threshold: float = 0.8
):
    """Complete daily job hunting workflow.

    Steps:
    1. Scrape jobs from multiple sources (parallel)
    2. Process and enrich jobs
    3. Match jobs against user profile
    4. Generate CVs for high-match jobs (parallel)
    5. Auto-apply if enabled
    6. Send summary notification
    """

    # Step 1: Scrape from multiple sources (parallel)
    scrape_tasks = []
    for source in sources:
        for keyword in keywords:
            task = scrape_jobs_task.submit(  # .submit() = run in parallel
                source=source,
                keywords=keyword,
                limit=50
            )
            scrape_tasks.append(task)

    # Wait for all scraping to complete
    scrape_results = [await task for task in scrape_tasks]

    # Collect all job IDs
    all_job_ids = []
    for result in scrape_results:
        if result.success:
            all_job_ids.extend(result.job_ids)

    if not all_job_ids:
        await notify_task(
            user_id=user_id,
            message="No jobs found for your search criteria"
        )
        return {"success": False, "reason": "no_jobs_found"}

    # Step 2: Process jobs (enrich, clean, deduplicate)
    process_result = await process_jobs_task(job_ids=all_job_ids)

    # Step 3: Match jobs against user profile
    match_result = await match_jobs_task(
        user_id=user_id,
        job_ids=process_result.processed_job_ids
    )

    # Filter high-match jobs
    high_match_jobs = [
        job_id for job_id, score in match_result.scores.items()
        if score >= match_threshold
    ]

    if not high_match_jobs:
        await notify_task(
            user_id=user_id,
            message=f"Found {len(all_job_ids)} jobs, but no high matches (threshold: {match_threshold})"
        )
        return {
            "success": True,
            "jobs_scraped": len(all_job_ids),
            "high_matches": 0,
            "applications": 0
        }

    # Step 4: Generate CVs for high-match jobs (parallel)
    cv_tasks = [
        generate_cvs_task.submit(
            job_id=job_id,
            user_id=user_id
        )
        for job_id in high_match_jobs
    ]

    cv_results = [await task for task in cv_tasks]

    # Step 5: Auto-apply if enabled
    applications = []
    if auto_apply:
        for job_id, cv_result in zip(high_match_jobs, cv_results):
            if cv_result.success:
                apply_result = await apply_jobs_task(
                    job_id=job_id,
                    user_id=user_id,
                    cv_id=cv_result.cv_id
                )
                applications.append(apply_result)

    # Step 6: Send summary notification
    await notify_task(
        user_id=user_id,
        message=f"""Daily Job Hunt Complete!

        📊 Jobs scraped: {len(all_job_ids)}
        ⭐ High matches: {len(high_match_jobs)} (>= {match_threshold*100}%)
        📝 CVs generated: {len([r for r in cv_results if r.success])}
        ✉️  Applications: {len([a for a in applications if a.success])}
        """
    )

    return {
        "success": True,
        "jobs_scraped": len(all_job_ids),
        "high_matches": len(high_match_jobs),
        "cvs_generated": len([r for r in cv_results if r.success]),
        "applications": len([a for a in applications if a.success])
    }
```

### Flow Features

**Sequential execution:**
```python
result1 = await task1()
result2 = await task2(result1.data)  # Waits for task1
```

**Parallel execution:**
```python
task1_future = task1.submit()
task2_future = task2.submit()
result1 = await task1_future
result2 = await task2_future
```

**Conditional logic:**
```python
if result1.success:
    await task2()
else:
    await fallback_task()
```

**Error handling:**
```python
try:
    result = await risky_task()
except Exception as e:
    await error_notification_task(error=str(e))
    raise
```

---

## TaskRun + Prefect Integration

### TaskRun Model Fields

```python
class TaskRun(Document):
    """Audit log with Prefect integration."""

    # Basic execution info
    operation_name: str                # "scrape_jobs"
    status: str                        # "pending", "running", "success", "failed"
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None

    # Actor tracking
    actor: Actor                       # Who triggered this

    # Prefect orchestration
    orchestrated: bool                 # True if running in Prefect flow
    prefect_flow_run_id: str | None    # Link to Prefect flow run
    prefect_task_run_id: str | None    # Link to Prefect task run

    # Input/Output
    input_dump: dict                   # Serialized input
    result_refs: list[dict]            # Created/modified documents

    # Error tracking
    error_message: str | None
    error_traceback: str | None

    # Metadata
    tags: list[str]
    metadata: dict
```

### Linking TaskRuns to Prefect

**Automatic linking:**

```python
# When operation runs in Prefect flow:
TaskRun(
    operation_name="scrape_jobs",
    orchestrated=True,                    # ✓ Detected Prefect context
    prefect_flow_run_id="abc-123-xyz",    # ✓ Flow run ID
    prefect_task_run_id="def-456-uvw",    # ✓ Task run ID
    ...
)
```

**Query TaskRuns by flow:**

```python
# Find all operations in a specific flow run
taskruns = await TaskRun.find(
    TaskRun.prefect_flow_run_id == "abc-123-xyz"
).to_list()

# See what happened in that flow
for tr in taskruns:
    print(f"{tr.operation_name}: {tr.status} ({tr.duration_ms}ms)")
```

**Debugging flows:**

```python
# Find failed operations in a flow
failed = await TaskRun.find(
    TaskRun.prefect_flow_run_id == "abc-123-xyz",
    TaskRun.status == "failed"
).to_list()

# See exact inputs that caused failures
for tr in failed:
    print(f"Operation: {tr.operation_name}")
    print(f"Input: {tr.input_dump}")
    print(f"Error: {tr.error_message}")
    print(f"Traceback:\n{tr.error_traceback}")
```

**Replay operations:**

```python
# Replay failed operation with same input
failed_taskrun = await TaskRun.get("taskrun-id")

# Get operation from registry
from core.registries import OperationRegistry
op_meta = OperationRegistry.get(failed_taskrun.operation_name)

# Reconstruct input
input_model = op_meta.input_schema(**failed_taskrun.input_dump)

# Re-run
result = await op_meta.function(input_model)
```

---

## Real-World Examples

### Example 1: Simple Scraping Flow

```python
@flow(name="scrape_stepstone_jobs")
async def scrape_stepstone_jobs(keywords: str, limit: int = 50):
    """Simple scraping flow with retries."""

    result = await scrape_jobs_task(
        source="stepstone",
        keywords=keywords,
        limit=limit
    )

    if result.success:
        print(f"✓ Scraped {result.jobs_created} jobs")
    else:
        print(f"✗ Scraping failed")

    return result
```

### Example 2: Scrape & Process Flow

```python
@flow(name="scrape_and_process")
async def scrape_and_process_flow(
    sources: list[str],
    keywords: str,
    limit: int = 50
):
    """Scrape from multiple sources, then process."""

    # Scrape from all sources in parallel
    scrape_futures = [
        scrape_jobs_task.submit(source=src, keywords=keywords, limit=limit)
        for src in sources
    ]

    scrape_results = [await f for f in scrape_futures]

    # Collect all job IDs
    all_job_ids = []
    for result in scrape_results:
        if result.success:
            all_job_ids.extend(result.job_ids)

    # Process all jobs
    if all_job_ids:
        process_result = await process_jobs_task(job_ids=all_job_ids)
        return {
            "jobs_scraped": len(all_job_ids),
            "jobs_processed": process_result.processed_count
        }
    else:
        return {"jobs_scraped": 0, "jobs_processed": 0}
```

### Example 3: Conditional Flow

```python
@flow(name="smart_job_application")
async def smart_job_application_flow(
    user_id: str,
    job_id: str,
    auto_apply_threshold: float = 0.9
):
    """Match job, generate CV, and conditionally apply."""

    # Step 1: Match job against user profile
    match_result = await match_job_task(user_id=user_id, job_id=job_id)

    # Step 2: Conditional - only proceed if high match
    if match_result.score < auto_apply_threshold:
        print(f"Match score {match_result.score} below threshold {auto_apply_threshold}")
        return {"applied": False, "reason": "low_match_score"}

    # Step 3: Generate CV
    cv_result = await generate_cv_task(user_id=user_id, job_id=job_id)

    if not cv_result.success:
        return {"applied": False, "reason": "cv_generation_failed"}

    # Step 4: Apply
    apply_result = await apply_job_task(
        user_id=user_id,
        job_id=job_id,
        cv_id=cv_result.cv_id
    )

    return {
        "applied": apply_result.success,
        "match_score": match_result.score,
        "cv_id": cv_result.cv_id,
        "application_id": apply_result.application_id if apply_result.success else None
    }
```

---

## Deployment & Scheduling

### Local Development

```python
# Run flow directly
import asyncio
from core.examples.workflows.flows import daily_job_hunt_flow

asyncio.run(
    daily_job_hunt_flow(
        user_id="user-123",
        keywords=["Python", "Data Engineer"],
        sources=["stepstone", "indeed"],
        auto_apply=False
    )
)
```

### Deploy with Prefect 2.x

```python
# deploy_flows.py
from prefect import serve
from core.examples.workflows.flows import (
    daily_job_hunt_flow,
    scrape_and_process_flow,
    maintenance_flow
)

if __name__ == "__main__":
    asyncio.run(
        serve(
            # Daily job hunt at 9 AM
            daily_job_hunt_flow.to_deployment(
                name="daily-job-hunt",
                cron="0 9 * * *",
                parameters={
                    "user_id": "user-123",
                    "keywords": ["Python", "Machine Learning"],
                    "sources": ["stepstone", "indeed"],
                    "auto_apply": True,
                    "match_threshold": 0.85
                },
                tags=["scheduled", "production"]
            ),

            # Scrape & process every 6 hours
            scrape_and_process_flow.to_deployment(
                name="periodic-scraping",
                cron="0 */6 * * *",
                parameters={
                    "sources": ["stepstone"],
                    "keywords": "Data Engineer",
                    "limit": 100
                },
                tags=["scheduled", "scraping"]
            ),

            # Cleanup daily at 2 AM
            maintenance_flow.to_deployment(
                name="daily-maintenance",
                cron="0 2 * * *",
                parameters={
                    "cleanup_days": 30
                },
                tags=["scheduled", "maintenance"]
            )
        )
    )
```

### Running the Deployment

```bash
# Start Prefect server
prefect server start

# In another terminal, deploy flows
python deploy_flows.py

# Flows now run on schedule automatically!
```

---

## Best Practices

### 1. Keep Operations Pure

✅ **Good:** Pure business logic
```python
@operation(name="scrape_jobs", ...)
async def scrape_jobs(input):
    # Just scraping logic, no retries/orchestration
    jobs = await fetch_jobs(input.source)
    return ScrapeJobsOutput(job_ids=jobs)
```

❌ **Bad:** Mixing orchestration with logic
```python
@operation(name="scrape_jobs", ...)
async def scrape_jobs(input):
    # Don't do retries in operation!
    for attempt in range(3):
        try:
            jobs = await fetch_jobs(input.source)
            break
        except:
            time.sleep(60)  # ❌ Bad
```

### 2. Use Tasks for Orchestration

✅ **Good:** Retries in task wrapper
```python
@task(retries=3, retry_delay_seconds=60)
async def scrape_jobs_task(source):
    return await scrape_jobs(ScrapeJobsInput(source=source))
```

### 3. Name Tasks Descriptively

✅ **Good:** Clear names
```python
@task(name="scrape_stepstone_jobs")
@task(name="match_jobs_against_profile")
@task(name="generate_cv_for_job")
```

❌ **Bad:** Generic names
```python
@task(name="task1")
@task(name="do_stuff")
```

### 4. Use Parallel Execution

✅ **Good:** Parallel when possible
```python
# Scrape multiple sources in parallel
tasks = [scrape_task.submit(source=s) for s in sources]
results = [await t for t in tasks]
```

❌ **Bad:** Sequential when not needed
```python
# Slow - waits for each to finish
for source in sources:
    await scrape_task(source=source)
```

### 5. Handle Failures Gracefully

✅ **Good:** Check results, provide fallbacks
```python
scrape_result = await scrape_task(source="stepstone")

if not scrape_result.success:
    # Try backup source
    scrape_result = await scrape_task(source="indeed")

if not scrape_result.success:
    # Notify and exit gracefully
    await notify_task(message="All scraping sources failed")
    return {"success": False}
```

### 6. Use TaskRun for Analytics

```python
# Analyze operation performance
pipeline = [
    {"$match": {"operation_name": "scrape_jobs", "orchestrated": True}},
    {"$group": {
        "_id": "$actor.user_id",
        "avg_duration": {"$avg": "$duration_ms"},
        "success_rate": {
            "$avg": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
        },
        "total_runs": {"$sum": 1}
    }}
]

stats = await TaskRun.aggregate(pipeline).to_list()
```

---

## Summary

### Key Takeaways

1. **Operations** = Core reusable business logic (works anywhere)
2. **Tasks** = Orchestration wrappers (retries, dependencies)
3. **Flows** = Complete workflows (composition, scheduling)

### When to Use Each

| Need | Solution |
|------|----------|
| Single task, instant response | Direct operation call (API/CLI) |
| Single task with retries | Prefect task |
| Multi-step workflow | Prefect flow |
| Scheduled runs | Prefect flow with cron deployment |
| Parallel execution | Prefect flow with `.submit()` |

### Architecture Benefits

✅ **Separation of concerns** - Business logic separate from orchestration
✅ **Reusability** - Operations work in API, CLI, and Prefect
✅ **Testability** - Test operations without Prefect
✅ **Observability** - TaskRun tracks everything
✅ **Flexibility** - Add/remove orchestration without changing operations

---

## Related Documentation

- [HOW_CORE_WORKS.md](./HOW_CORE_WORKS.md) - Overall architecture
- [OPERATION_DECORATOR.md](./OPERATION_DECORATOR.md) - Operations in detail
- [TaskRun Model](../../src/database/models/taskrun.py) - Audit trail implementation

---

**Next Steps:**
1. Read [HOW_CORE_WORKS.md](./HOW_CORE_WORKS.md) for overall architecture
2. Create your first operation
3. Wrap it in a Prefect task
4. Compose multiple tasks into a flow
5. Deploy and schedule!
