# How Core Works

**Core Principle:** Define models and operations once with decorators → Auto-generate API, CLI, and UI surfaces

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│  DataExplorer UI (React + Refine)                            │
│  └─ Auto-generated from @datamodel metadata                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  API (FastAPI)                                               │
│  ├─ CRUD endpoints from @datamodel                           │
│  └─ Operation endpoints from @operation                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Core (THIS REPOSITORY)                                      │
│  ├─ @datamodel → Registers models → CRUD API + UI Explorer  │
│  ├─ @operation → Registers async tasks → Creates TaskRun    │
│  └─ Registries → Single source of truth                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Database (MongoDB + Beanie)                                 │
│  └─ TaskRun collection for audit trail                       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Orchestration (Prefect) - OPTIONAL                          │
│  ├─ Flows (@flow) → Compose tasks into workflows            │
│  ├─ Tasks (@task) → Wrap @operation for orchestration       │
│  └─ Operations (@operation) → Run standalone OR orchestrated │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

**DataExplorer UI (React + Refine)**
- Auto-generated list/detail views from `@datamodel`
- Auto-generated action buttons/forms from `@operation`

**API (FastAPI)**
- Auto-generated CRUD endpoints from `@datamodel`
- Auto-generated operation endpoints from `@operation`

**Database (MongoDB)**
- Beanie ODM for async MongoDB access
- TaskRun collection for complete audit trail

**Orchestration (Prefect) - Optional**
- Flows compose multiple operations into workflows
- Tasks wrap operations for retry/scheduling/monitoring
- Operations detect Prefect context automatically

### The Three Execution Layers

**1. Operations** - Individual reusable tasks
```python
@operation(name="process_job", ...)
async def process_job(input) -> output:
    # Business logic
    pass
```
- Can run standalone (API, CLI)
- Can be orchestrated (Prefect)
- Always create TaskRun audit records

**2. Prefect Tasks** - Orchestration wrappers
```python
@task(retries=3)
async def process_job_task(input):
    return await process_job(input)  # Wraps operation
```
- Add retry logic, dependencies
- Link TaskRuns to Prefect runs
- Enable workflow composition

**3. Prefect Flows** - Complete workflows
```python
@flow
async def daily_processing():
    scrape_result = await scrape_task()
    process_result = await process_task(scrape_result.job_ids)
    # Multi-step orchestration
```
- Compose multiple tasks
- Define execution order
- Schedule periodic runs

## The Flow

```
1. Define model with @datamodel
2. Register operation with @operation
3. Registries collect metadata
4. Surfaces consume registries to generate endpoints/commands/UI
5. (Optional) Wrap operations in Prefect tasks/flows for orchestration
```

## Part 1: Data Models

### Define a Model

```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="Job",                    # Public name
    description="Job posting",     # Human description
    tags=["jobs", "scraping"],     # For grouping/filtering
    ui={                           # UI generation hints
        "icon": "💼",
        "primary_field": "title",
        "list_fields": ["title", "company", "location"],
    }
)
class Job(Document):
    """Beanie document - use it directly, no repositories."""

    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Location")

    class Settings:
        name = "jobs"  # MongoDB collection
```

### What Happens

1. `@datamodel` decorator captures metadata
2. Stores `ModelInfo` in `ModelRegistry._models`
3. API reads registry → creates `/models/Job/` CRUD endpoints
4. Frontend reads registry → generates list/detail views

### Use the Model

```python
# Create
job = Job(title="Developer", company="Acme", location="Berlin")
await job.insert()

# Query (Beanie built-in)
jobs = await Job.find(Job.company == "Acme").to_list()

# Update
job.location = "Munich"
await job.save()

# Delete
await job.delete()
```

**No repository needed** - Beanie already provides everything.

## Part 1.5: Beanie & Database

**Beanie:** MongoDB ODM (Object-Document Mapper) built on Motor and Pydantic

### Why Beanie?

1. **Async-first** - Built for asyncio/FastAPI
2. **Pydantic integration** - Models are Pydantic models
3. **Type-safe** - Full type hints
4. **No repository needed** - Built-in query methods
5. **Migration-friendly** - Easy schema evolution

### Database Setup

**Initialization** (`core/examples/models/connection.py`):

```python
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.examples.models.models import TestItem, TaskRun, Job, User

async def init_database():
    """Initialize MongoDB + Beanie at app startup."""

    # 1. Connect to MongoDB (Motor client)
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client["jobhunter"]

    # 2. Register all Document models with Beanie
    await init_beanie(
        database=database,
        document_models=[
            TestItem,
            TaskRun,
            Job,
            User,
            # ... all your models
        ]
    )

    # 3. Beanie automatically:
    #    - Creates collections if needed
    #    - Creates indexes defined in Settings.indexes
    #    - Sets up query builders for each model

    return database
```

**Application startup** (FastAPI example):

```python
from fastapi import FastAPI
from core.examples.models.connection import init_database

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Run on application startup."""
    await init_database()
    print("✓ Database initialized")

@app.on_event("shutdown")
async def shutdown():
    """Run on application shutdown."""
    await close_database()
```

### Beanie Document Anatomy

```python
from beanie import Document, Indexed
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

class Job(Document):
    """Beanie Document = Pydantic Model + MongoDB Collection"""

    # Fields (Pydantic types)
    title: str = Field(..., description="Job title")
    company: Indexed(str)  # Index this field
    location: str | None = None
    match_score: float | None = Field(None, ge=0, le=100)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Settings: Configure MongoDB behavior
    class Settings:
        name = "jobs"  # MongoDB collection name

        # Define compound/complex indexes
        indexes = [
            # Compound index on (company, created_at)
            IndexModel(
                [("company", ASCENDING), ("created_at", DESCENDING)]
            ),

            # Unique index on (source, external_id)
            IndexModel(
                [("source", ASCENDING), ("external_id", ASCENDING)],
                unique=True
            ),

            # Text search index
            IndexModel(
                [("title", "text"), ("description", "text")]
            ),
        ]

    # Helper methods (optional)
    def full_title(self) -> str:
        return f"{self.title} at {self.company}"
```

**What Beanie provides:**
- Automatic validation (Pydantic)
- Type hints everywhere
- Serialization (to JSON, to dict)
- Index management
- Query builder
- Aggregation pipeline
- Change streams

### Beanie Query Patterns

**Basic Queries:**

```python
# Find all
jobs = await Job.find_all().to_list()

# Find with filter
jobs = await Job.find(Job.company == "Acme").to_list()

# Find with multiple conditions
jobs = await Job.find(
    Job.company == "Acme",
    Job.match_score > 80
).to_list()

# Find with operators
jobs = await Job.find(
    Job.match_score >= 70,
    Job.match_score <= 90
).to_list()

# Find with $in
jobs = await Job.find(
    Job.company.in_(["Acme", "TechCorp", "StartupCo"])
).to_list()

# Find one
job = await Job.find_one(Job.external_id == "12345")

# Get by ID
job = await Job.get("507f1f77bcf86cd799439011")
```

**Sorting, Limiting, Pagination:**

```python
# Sort
jobs = await Job.find().sort(-Job.created_at).to_list()
# or
jobs = await Job.find().sort("+match_score").to_list()

# Limit
jobs = await Job.find().limit(10).to_list()

# Skip (pagination)
jobs = await Job.find().skip(20).limit(10).to_list()

# Count
count = await Job.find(Job.company == "Acme").count()

# Exists
exists = await Job.find_one(Job.external_id == "12345").exists()
```

**Advanced Queries:**

```python
# Regex
jobs = await Job.find(
    Job.title.regex("python", options="i")  # Case-insensitive
).to_list()

# Array contains
jobs = await Job.find(
    Job.required_skills.contains("Python")
).to_list()

# Nested fields
jobs = await Job.find(
    Job.location.city == "Berlin"
).to_list()

# Text search (requires text index)
jobs = await Job.find(
    {"$text": {"$search": "python developer"}}
).to_list()
```

**Aggregation Pipeline:**

```python
# Complex aggregation
pipeline = [
    {"$match": {"match_score": {"$gte": 80}}},
    {"$group": {
        "_id": "$company",
        "avg_score": {"$avg": "$match_score"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"avg_score": -1}},
    {"$limit": 10}
]

results = await Job.aggregate(pipeline).to_list()
# → [{"_id": "Acme", "avg_score": 85.5, "count": 12}, ...]
```

### CRUD Operations

**Create:**

```python
# Method 1: Create and insert
job = Job(
    title="Python Developer",
    company="Acme",
    location="Berlin"
)
await job.insert()
print(f"Created job with ID: {job.id}")

# Method 2: Create many
jobs = [
    Job(title="Dev 1", company="A"),
    Job(title="Dev 2", company="B"),
]
await Job.insert_many(jobs)
```

**Read:**

```python
# By ID
job = await Job.get("507f1f77bcf86cd799439011")

# With query
job = await Job.find_one(Job.external_id == "12345")

# Get or None (doesn't raise)
job = await Job.find_one(Job.external_id == "nonexistent")
# → None if not found

# Get or raise
job = await Job.get("invalid-id")
# → Raises DocumentNotFound
```

**Update:**

```python
# Method 1: Modify and save
job = await Job.get(job_id)
job.match_score = 85
job.updated_at = datetime.utcnow()
await job.save()

# Method 2: Update query (bulk)
await Job.find(Job.company == "Acme").update(
    {"$set": {"is_verified": True}}
)

# Method 3: Update one
await Job.find_one(Job.external_id == "12345").update(
    {"$set": {"match_score": 90}}
)

# Method 4: Upsert
await Job.find_one(Job.external_id == "12345").upsert(
    {"$set": {"title": "Senior Dev"}},
    on_insert=Job(external_id="12345", company="Acme")
)
```

**Delete:**

```python
# Delete instance
job = await Job.get(job_id)
await job.delete()

# Delete by query
await Job.find(Job.company == "OldCompany").delete()

# Delete one
await Job.find_one(Job.external_id == "12345").delete()
```

### Index Management

**Simple index:**

```python
class Job(Document):
    company: Indexed(str)  # Single-field index
    created_at: Indexed(datetime)
```

**Compound index:**

```python
class Job(Document):
    class Settings:
        indexes = [
            # (company, created_at) compound index
            IndexModel([
                ("company", ASCENDING),
                ("created_at", DESCENDING)
            ])
        ]
```

**Unique index:**

```python
class Job(Document):
    source: str
    external_id: str

    class Settings:
        indexes = [
            # Unique constraint on (source, external_id)
            IndexModel(
                [("source", ASCENDING), ("external_id", ASCENDING)],
                unique=True
            )
        ]
```

**Sparse index:**

```python
class TaskRun(Document):
    idempotency_key: str | None = None

    class Settings:
        indexes = [
            # Only index documents where idempotency_key exists
            IndexModel(
                [("idempotency_key", ASCENDING)],
                unique=True,
                sparse=True  # Don't index None values
            )
        ]
```

**Text search index:**

```python
class Job(Document):
    class Settings:
        indexes = [
            # Full-text search on title and description
            IndexModel([
                ("title", "text"),
                ("description", "text")
            ])
        ]

# Query with text search
jobs = await Job.find(
    {"$text": {"$search": "python developer"}}
).to_list()
```

### Schema Evolution

**Beanie handles schema changes gracefully:**

```python
# Version 1: Simple model
class Job(Document):
    title: str
    company: str

# Version 2: Add optional field
class Job(Document):
    title: str
    company: str
    match_score: float | None = None  # ✓ Old docs have None

# Version 3: Add field with default
class Job(Document):
    title: str
    company: str
    match_score: float | None = None
    is_verified: bool = False  # ✓ Old docs get default value

# Version 4: Rename field (migration required)
# Old: company: str
# New: company_name: str
# → Write migration script to update all docs
```

**Migration script example:**

```python
async def migrate_company_field():
    """Rename 'company' to 'company_name'."""
    await Job.find_all().update_many({
        "$rename": {"company": "company_name"}
    })
```

### Connection Patterns

**Single connection (recommended):**

```python
# Initialize once at startup
_db_client = None

async def init_database():
    global _db_client
    _db_client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=_db_client["jobhunter"], ...)

async def close_database():
    global _db_client
    if _db_client:
        _db_client.close()
```

**Context manager (for tests):**

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def test_database():
    """Temporary database for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["jobhunter_test"]

    await init_beanie(database=db, document_models=[Job, User])

    try:
        yield db
    finally:
        # Cleanup
        await db.client.drop_database("jobhunter_test")
        client.close()

# Usage
async def test_job_creation():
    async with test_database() as db:
        job = Job(title="Test", company="Test")
        await job.insert()
        assert await Job.count() == 1
```

### Why No Repository Pattern?

**Beanie provides everything repositories do:**

```python
# ❌ With repository (unnecessary abstraction)
class JobRepository:
    async def find_by_company(self, company: str) -> list[Job]:
        return await Job.find(Job.company == company).to_list()

    async def create(self, job: Job) -> Job:
        await job.insert()
        return job

repo = JobRepository()
jobs = await repo.find_by_company("Acme")

# ✓ Without repository (use Beanie directly)
jobs = await Job.find(Job.company == "Acme").to_list()

job = Job(title="Dev", company="Acme")
await job.insert()
```

**When you might need a repository:**
- Complex business logic spanning multiple models
- Need to mock database for tests
- Enforcing access control/permissions

**But usually:**
- Put complex queries in model class methods
- Use Beanie's built-in methods directly
- Keep it simple!

### Database Configuration

**Settings** (`src/utils/config.py`):

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "jobhunter"

    class Config:
        env_file = ".env"

# Usage
settings = Settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
```

**Environment variables** (`.env`):

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=jobhunter

# Or for Atlas (cloud)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### Summary: Beanie Benefits

1. **Type-safe**: Full type hints, no runtime surprises
2. **Async-native**: Built for FastAPI/async Python
3. **Pydantic integration**: Validation, serialization for free
4. **No boilerplate**: No repositories, just use models directly
5. **Index management**: Declare indexes in code, Beanie creates them
6. **Schema evolution**: Handles optional fields, defaults gracefully
7. **Rich queries**: Expressive query API, aggregation support
8. **Testing-friendly**: Easy to create test databases

**Architecture:**
```
┌──────────────┐
│  Your Code   │  await Job.find(Job.company == "Acme").to_list()
└──────┬───────┘
       │
┌──────▼───────┐
│    Beanie    │  ODM layer (query building, validation)
└──────┬───────┘
       │
┌──────▼───────┐
│    Motor     │  Async MongoDB driver
└──────┬───────┘
       │
┌──────▼───────┐
│   MongoDB    │  Database
└──────────────┘
```

## Part 2: Operations

### Define an Operation

```python
from pydantic import BaseModel, Field
from core.decorators import operation

# 1. Define typed input/output
class SearchJobsInput(BaseModel):
    keywords: list[str] = Field(..., description="Search keywords")
    location: str | None = Field(None, description="Location filter")

class SearchJobsOutput(BaseModel):
    jobs: list[dict] = Field(..., description="Matching jobs")
    count: int = Field(..., description="Result count")

# 2. Register operation
@operation(
    name="search_jobs",
    description="Search for jobs by keywords",
    category="jobs",                    # Group operations
    inputs=SearchJobsInput,             # Input schema
    outputs=SearchJobsOutput,           # Output schema
    tags=["search", "jobs"],
    models_in=["Job"],                  # Reads from Job
    models_out=[],                      # Doesn't create anything
    async_enabled=True,                 # Enable async execution
)
async def search_jobs(input: SearchJobsInput) -> SearchJobsOutput:
    """Implementation - just write normal async Python."""

    # Build query
    query = {}
    if input.location:
        query["location"] = input.location

    # Use Beanie directly
    jobs = await Job.find(query).to_list()

    # Filter by keywords (example)
    matches = [
        job for job in jobs
        if any(kw.lower() in job.title.lower() for kw in input.keywords)
    ]

    return SearchJobsOutput(
        jobs=[{"title": j.title, "company": j.company} for j in matches],
        count=len(matches)
    )
```

### What Happens

1. `@operation` decorator captures metadata
2. Stores `OperationMetadata` in `OperationRegistry._ops`
3. API reads registry → creates `POST /operations/search_jobs/` endpoint
4. CLI reads registry → generates `jobhunter ops search_jobs` command
5. Frontend reads registry → generates operation buttons/forms

### Auto-Generated Features

**Observability (if `async_enabled=True`):**
- Decorator wraps your function
- Creates `TaskRun` record before execution
- Tracks: input, output, status, timing, errors
- Links to documents via `result_refs`

**Prefect Integration:**
- Detects if running in Prefect flow
- Links `TaskRun` to flow/task run IDs

## Part 2.5: Prefect Orchestration

**Prefect's Role:** Orchestration layer for complex multi-step workflows

### The Layers

```
┌─────────────────────────────────────────┐
│  Prefect Flows (workflows/flows.py)    │  Multi-step orchestration
│  └─ @flow decorator                    │  Retries, scheduling, monitoring
└──────────────┬──────────────────────────┘
               │ calls
               ▼
┌─────────────────────────────────────────┐
│  Prefect Tasks (workflows/tasks.py)    │  Wrappers for operations
│  └─ @task decorator                    │  Individual step execution
└──────────────┬──────────────────────────┘
               │ calls
               ▼
┌─────────────────────────────────────────┐
│  Operations (operations/*.py)           │  Core business logic
│  └─ @operation decorator               │  Creates TaskRun records
└─────────────────────────────────────────┘
```

### When to Use Prefect

**Use Prefect flows when:**
- Multi-step workflows (scrape → process → apply)
- Need retries, scheduling, or monitoring
- Orchestrating multiple operations
- Long-running batch processes

**Don't use Prefect when:**
- Simple single operations
- Direct API calls
- CLI commands
- Synchronous CRUD operations

### Example: Without Prefect (Direct Operation)

```python
# Simple API call - no Prefect needed
from core.examples.operations.test_ops import create_test_item, CreateTestItemInput

async def api_endpoint(request):
    """Direct operation call from API."""
    input_data = CreateTestItemInput(name="Test", value=42)
    result = await create_test_item(input_data)
    # Operation creates TaskRun automatically (async_enabled=True)
    return {"success": result.success, "item_id": result.item_id}
```

**What happens:**
1. API receives request
2. Calls operation directly
3. `@operation` decorator creates `TaskRun` (observability)
4. `TaskRun.orchestrated = False` (not in Prefect flow)
5. Returns result

### Example: With Prefect (Complex Workflow)

```python
# workflows/tasks.py - Wrap operations in Prefect tasks
from prefect import task
from core.examples.operations.scraping_ops import scrape_jobs, ScrapeJobsInput

@task(name="scrape_task", retries=3, retry_delay_seconds=60)
async def scrape_task(keywords: str, limit: int = 10) -> ScrapeJobsOutput:
    """Prefect task wrapping scrape_jobs operation."""
    input_data = ScrapeJobsInput(keywords=keywords, limit=limit)
    return await scrape_jobs(input_data)  # Calls actual operation

@task(name="process_task", retries=2)
async def process_task(job_ids: list[str]) -> ProcessJobsOutput:
    """Prefect task wrapping process_jobs operation."""
    input_data = ProcessJobsInput(job_ids=job_ids)
    return await process_jobs(input_data)

# workflows/flows.py - Compose tasks into workflow
from prefect import flow

@flow(name="scrape_and_process_flow")
async def scrape_and_process_flow(keywords: str, limit: int = 10):
    """Multi-step workflow orchestrated by Prefect."""

    # Step 1: Scrape jobs (with retries)
    scrape_result = await scrape_task(keywords=keywords, limit=limit)

    if not scrape_result.success:
        return {"success": False, "error": "Scraping failed"}

    # Step 2: Process scraped jobs (with retries)
    process_result = await process_task(job_ids=scrape_result.job_ids)

    return {
        "success": True,
        "jobs_scraped": len(scrape_result.job_ids),
        "jobs_processed": process_result.processed_count
    }
```

**What happens:**
1. Flow starts → Prefect creates flow run
2. `scrape_task` runs → Prefect creates task run
3. `scrape_jobs` operation executes
4. `@operation` decorator detects Prefect context:
   ```python
   from prefect.context import FlowRunContext, TaskRunContext
   flow_ctx = FlowRunContext.get()  # ✓ Found!
   task_ctx = TaskRunContext.get()  # ✓ Found!
   ```
5. Creates `TaskRun` with Prefect IDs:
   ```python
   TaskRun(
       operation_name="scrape_jobs",
       orchestrated=True,  # ✓ Running in Prefect
       prefect_flow_run_id="abc-123",  # Link to flow
       prefect_task_run_id="def-456",  # Link to task
       ...
   )
   ```
6. If task fails → Prefect retries (3x with 60s delay)
7. `process_task` runs with results from scrape
8. Prefect monitors entire flow, provides UI dashboard

### TaskRun + Prefect Integration

The `@operation` decorator automatically detects Prefect context:

```python
# From src/core/decorators.py

@operation(name="scrape_jobs", async_enabled=True, ...)
async def scrape_jobs(input: ScrapeJobsInput) -> ScrapeJobsOutput:
    # Your implementation
    ...

# Decorator wrapper (automatic):
async def _wrapped_async(*args, **kwargs):
    # Try to detect Prefect context
    try:
        from prefect.context import FlowRunContext, TaskRunContext

        flow_ctx = FlowRunContext.get()
        task_ctx = TaskRunContext.get()

        orchestrated = bool(flow_ctx or task_ctx)
        prefect_flow_run_id = str(flow_ctx.flow_run.id) if flow_ctx else None
        prefect_task_run_id = str(task_ctx.task_run.id) if task_ctx else None
    except (ImportError, Exception):
        # No Prefect or not in flow → direct execution
        orchestrated = False
        prefect_flow_run_id = None
        prefect_task_run_id = None

    # Create TaskRun with Prefect info
    taskrun = TaskRun(
        operation_name="scrape_jobs",
        orchestrated=orchestrated,
        prefect_flow_run_id=prefect_flow_run_id,
        prefect_task_run_id=prefect_task_run_id,
        ...
    )
    await taskrun.insert()

    # Execute operation
    result = await scrape_jobs_impl(*args, **kwargs)

    # Update TaskRun
    taskrun.mark_success(result_refs=...)
    await taskrun.save()

    return result
```

### TaskRun Model Fields

```python
class TaskRun(Document):
    """Audit log with Prefect integration."""

    # Basic execution info
    operation_name: str                # "scrape_jobs"
    status: str                        # "success", "failed", etc.
    started_at: datetime
    finished_at: datetime
    duration_ms: int

    # Prefect orchestration
    orchestrated: bool                 # True if in Prefect flow
    prefect_flow_run_id: str | None    # Link to Prefect flow
    prefect_task_run_id: str | None    # Link to Prefect task

    # Input/Output
    input_dump: dict                   # Serialized input
    result_refs: list[dict]            # Created documents
    error_message: str | None
    error_traceback: str | None
```

### Benefits of Prefect Integration

**1. Observability**
```python
# Query TaskRuns from specific Prefect flow
flow_runs = await TaskRun.find(
    TaskRun.prefect_flow_run_id == "abc-123"
).to_list()

# See all operations that ran in that flow
for tr in flow_runs:
    print(f"{tr.operation_name}: {tr.status} ({tr.duration_ms}ms)")
```

**2. Debugging**
```python
# Find failed operations in Prefect flow
failed = await TaskRun.find(
    TaskRun.prefect_flow_run_id == "abc-123",
    TaskRun.status == "failed"
).to_list()

# See exact inputs that caused failures
for tr in failed:
    print(f"Operation: {tr.operation_name}")
    print(f"Input: {tr.input_dump}")
    print(f"Error: {tr.error_message}")
    print(f"Traceback: {tr.error_traceback}")
```

**3. Replay**
```python
# Replay failed operation with same input
failed_taskrun = await TaskRun.get("taskrun-id")

# Get operation from registry
op_meta = OperationRegistry.get(failed_taskrun.operation_name)

# Reconstruct input from saved dump
input_model = op_meta.input_schema(**failed_taskrun.input_dump)

# Re-run operation
result = await op_meta.function(input_model)
```

**4. Analytics**
```python
# Average duration for scraping operations in Prefect flows
from pymongo import DESCENDING

pipeline = [
    {"$match": {"operation_name": "scrape_jobs", "orchestrated": True}},
    {"$group": {
        "_id": None,
        "avg_duration": {"$avg": "$duration_ms"},
        "total_runs": {"$sum": 1},
        "success_rate": {
            "$avg": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
        }
    }}
]

stats = await TaskRun.aggregate(pipeline).to_list()
# → {"avg_duration": 15000, "total_runs": 250, "success_rate": 0.96}
```

### Real-World Flow Example

```python
# workflows/flows.py

@flow(name="daily_job_hunt", retries=1)
async def daily_job_hunt_flow(
    user_id: str,
    keywords: list[str],
    auto_apply: bool = False,
):
    """Complete daily job hunting workflow.

    1. Scrape jobs from multiple sources
    2. Match jobs against user profile
    3. Generate CVs for high-match jobs
    4. Auto-apply if enabled
    5. Send daily summary email
    """

    # Step 1: Scrape from multiple sources (parallel)
    stepstone_task = scrape_stepstone_task.submit(keywords=keywords)
    indeed_task = scrape_indeed_task.submit(keywords=keywords)

    stepstone_result = await stepstone_task
    indeed_result = await indeed_task

    all_job_ids = (
        stepstone_result.job_ids +
        indeed_result.job_ids
    )

    # Step 2: Match jobs (sequential)
    match_result = await match_jobs_task(
        user_id=user_id,
        job_ids=all_job_ids
    )

    high_match_jobs = [
        job_id for job_id, score in match_result.scores.items()
        if score >= 0.8
    ]

    # Step 3: Generate CVs for high matches (parallel)
    cv_tasks = [
        generate_cv_task.submit(job_id=job_id, user_id=user_id)
        for job_id in high_match_jobs
    ]
    cv_results = await asyncio.gather(*cv_tasks)

    # Step 4: Auto-apply if enabled (sequential)
    applications = []
    if auto_apply:
        for job_id, cv_result in zip(high_match_jobs, cv_results):
            apply_result = await apply_job_task(
                job_id=job_id,
                user_id=user_id,
                cv_id=cv_result.cv_id
            )
            applications.append(apply_result)

    # Step 5: Send summary
    await notify_task(
        user_id=user_id,
        message=f"Daily hunt complete: {len(all_job_ids)} jobs, "
                f"{len(high_match_jobs)} high matches, "
                f"{len(applications)} applications"
    )

    return {
        "jobs_scraped": len(all_job_ids),
        "high_matches": len(high_match_jobs),
        "applications": len(applications)
    }
```

**Prefect provides:**
- Flow visualization in UI
- Automatic retries on failures
- Parallel task execution
- Scheduled runs (daily at 8am)
- Email alerts on failures
- Performance metrics

**TaskRun provides:**
- Detailed audit trail for each operation
- Input/output snapshots
- Error details for debugging
- Link back to Prefect flow
- Analytics and replay capability

### Summary: Three Execution Modes

**1. Direct (API/CLI)**
```python
result = await operation(input)
# → TaskRun created (orchestrated=False)
# → Fast, simple, no Prefect overhead
```

**2. Prefect Task (in Flow)**
```python
@flow
async def my_flow():
    result = await task_wrapper()  # Calls operation
    # → TaskRun created (orchestrated=True)
    # → Links to Prefect flow/task IDs
    # → Prefect handles retries, monitoring
```

**3. Prefect Flow (scheduled/complex)**
```python
@flow
async def complex_workflow():
    # Multi-step orchestration
    result1 = await task1()
    result2 = await task2(result1.data)
    result3 = await task3(result2.data)
    # → Multiple TaskRuns created
    # → All linked to same flow
    # → Complete audit trail + Prefect orchestration
```

**Choose based on complexity:**
- Single operation → Direct
- Needs retries/monitoring → Prefect Task
- Multi-step workflow → Prefect Flow

## Part 3: Registries

### ModelRegistry

```python
from core.registries import ModelRegistry

# List all registered models
models = ModelRegistry.list_all()  # → [ModelInfo, ModelInfo, ...]

# Get specific model
job_info = ModelRegistry.get("Job")
# → ModelInfo(name="Job", document_cls=Job, ui_hints={...}, ...)
```

### OperationRegistry

```python
from core.registries import OperationRegistry

# List all operations
ops = OperationRegistry.list_all()  # → [OperationMetadata, ...]

# Get specific operation
search_op = OperationRegistry.get("search_jobs")
# → OperationMetadata(name="search_jobs", input_schema=SearchJobsInput, ...)

# Group by category
job_ops = OperationRegistry.by_category("jobs")
```

## Part 4: Auto-Generation

### API (FastAPI)

```python
from fastapi import FastAPI
from core.registries import ModelRegistry, OperationRegistry

app = FastAPI()

# Auto-generate CRUD endpoints
for model_info in ModelRegistry.list_all():
    # Creates:
    # GET    /models/{name}/           - List
    # POST   /models/{name}/           - Create
    # GET    /models/{name}/{id}       - Get
    # PUT    /models/{name}/{id}       - Update
    # DELETE /models/{name}/{id}       - Delete
    mount_model_routes(app, model_info)

# Auto-generate operation endpoints
for op_meta in OperationRegistry.list_all():
    # Creates:
    # POST /operations/{name}/
    mount_operation_route(app, op_meta)

# Discovery endpoint
# GET /operations/graph - Returns operation metadata for UI
```

### CLI (Typer)

```python
import typer
from core.registries import OperationRegistry

cli = typer.Typer()

# Auto-generate commands
for op_meta in OperationRegistry.list_all():
    # Creates: jobhunter ops {name}
    create_typer_command(cli, op_meta)
```

### Frontend (React + Refine)

```typescript
// Fetch model metadata from API
const models = await fetch('/models/').then(r => r.json())

// Generate list view
models.forEach(model => {
  // Creates resource with:
  // - List view with model.ui_hints.list_fields
  // - Detail view with model.ui_hints.detail_sections
  // - Form with fields from schema
  createResource(model)
})

// Fetch operation metadata
const operations = await fetch('/operations/graph').then(r => r.json())

// Generate action buttons
operations.forEach(op => {
  // Creates button/form based on op.input_schema
  createActionButton(op)
})
```

## Concrete Example: Full Flow

### 1. Define Model

```python
@datamodel(name="TestItem", tags=["test"])
class TestItem(Document):
    name: str
    value: int
```

### 2. Define Operation

```python
@operation(
    name="create_item",
    inputs=CreateItemInput,
    outputs=CreateItemOutput,
    category="testing",
)
async def create_item(input: CreateItemInput) -> CreateItemOutput:
    item = TestItem(name=input.name, value=input.value)
    await item.insert()
    return CreateItemOutput(success=True, item_id=str(item.id))
```

### 3. What You Get Automatically

**API:**
```bash
# CRUD
GET    /models/TestItem/           # List all
POST   /models/TestItem/           # Create
GET    /models/TestItem/{id}       # Get one
PUT    /models/TestItem/{id}       # Update
DELETE /models/TestItem/{id}       # Delete

# Operation
POST   /operations/create_item/    # Execute operation
```

**CLI:**
```bash
jobhunter ops create_item --name "Test" --value 42
```

**Frontend:**
- TestItem list view (table)
- TestItem detail view (form)
- "Create Item" action button

**Database:**
- `test_items` collection (from Settings.name)
- `taskruns` collection (audit trail)

## Key Files

```
src/core/
├── decorators.py       # @datamodel, @operation definitions
├── registries.py       # ModelRegistry, OperationRegistry storage
├── base.py            # Optional DataModelBase, OperationBase classes
└── renderers/         # API/CLI renderer contracts (not implementations)
```

## Testing

```python
import pytest
from core.registries import ModelRegistry, OperationRegistry

def test_model_registration():
    """Models auto-register on import."""
    from core.examples.models.models.test_model import TestItem

    info = ModelRegistry.get("TestItem")
    assert info is not None
    assert info.document_cls == TestItem

def test_operation_registration():
    """Operations auto-register on import."""
    from core.examples.operations.test_ops import create_test_item

    meta = OperationRegistry.get("create_test_item")
    assert meta is not None
    assert meta.category == "testing"
```

## Extension Patterns

### Source-Specific Fields

```python
class Job(Document):
    # Core fields
    title: str
    company: str

    # Extension bag for platform-specific data
    source_fields: dict[str, dict[str, Any]] = Field(default_factory=dict)
    # Example: {"stepstone": {"workload": "full-time", "salary_band": "50-70k"}}

# Get source field
job.get_source_field("workload")  # → "full-time"

# Set source field
job.set_source_field("salary_band", "50-70k")
```

### UI Field Extensions

Adapters can contribute platform-specific UI metadata:

```python
stepstone_fields = {
    "workload": {"label": "Arbeitslast", "widget": "select"},
    "salary_band": {"label": "Gehaltsspanne", "widget": "text"}
}

# Merged with model.ui_hints at runtime
```

### Operation Options

Forward-compatible operation tweaks:

```python
class ProcessJobInput(BaseModel):
    job_id: str
    options: dict[str, Any] = Field(default_factory=dict)
    # Can add new options without breaking schema:
    # {"skip_matching": true, "force_reprocess": true}
```

## Why This Works

1. **Single source of truth**: Metadata lives in one place (registries)
2. **Type safety**: Pydantic everywhere (models, inputs, outputs)
3. **No duplication**: Don't write API routes, CLI commands, or UI forms manually
4. **Forward compatible**: Extension bags and options prevent breaking changes
5. **Simple**: Just write Beanie documents and async functions

## Common Patterns

### Simple CRUD Operation

```python
@operation(name="update_job", ...)
async def update_job(input: UpdateJobInput) -> UpdateJobOutput:
    job = await Job.get(input.job_id)
    job.title = input.title
    await job.save()
    return UpdateJobOutput(success=True)
```

### Batch Operation

```python
@operation(name="bulk_delete", async_enabled=True, ...)
async def bulk_delete(input: BulkDeleteInput) -> BulkDeleteOutput:
    for job_id in input.job_ids:
        job = await Job.get(job_id)
        await job.delete()
    return BulkDeleteOutput(deleted_count=len(input.job_ids))
```

### Complex Operation with External API

```python
@operation(name="enrich_job", async_enabled=True, ...)
async def enrich_job(input: EnrichJobInput) -> EnrichJobOutput:
    job = await Job.get(input.job_id)

    # Call external API
    company_data = await fetch_company_info(job.company)

    # Update job
    job.company_info = company_data
    await job.save()

    return EnrichJobOutput(success=True, enriched_fields=["company_info"])
```

## Summary

```
┌─────────────────┐
│  @datamodel     │  Register model metadata
│  @operation     │  Register operation metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ModelRegistry  │  Store model info
│  OperationReg   │  Store operation info
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API (FastAPI)  │  Mount CRUD + operation endpoints
│  CLI (Typer)    │  Generate commands
│  UI (React)     │  Generate forms/tables/actions
└─────────────────┘
```

**You write:** Models + Operations
**You get:** Full-stack application
