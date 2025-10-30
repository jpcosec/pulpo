# Phase 2: Service Management Discussion

**Critical Insight:** This is a library, not a framework. Service management must work within user projects.

---

## Understanding the Context

### What Pulpo IS
- A **library** installed in user projects via `pip install pulpocore`
- Provides "plug and play" orchestration, DB, UI, API infrastructure
- User projects import and use it: `from pulpo import CLI, datamodel, operation`
- Users don't manage Pulpo globally; it's part of their project

### Current Service Management Problem
The question: "How does `pulpo up/down` work when it's a library in a user's project?"

This is fundamentally different from a global framework. We need to discuss:

---

## Problem 1: Flow Composition - CLARIFIED ✅

**Your clarification:** Prefect allows composition/nesting of flows.

**Structure should be:**
```
scraping_flow (main flow)
├── stepstone_flow (subflow)
│   └── fetch_stepstone_task
├── linkedin_flow (subflow)
│   └── fetch_linkedin_task
└── merge_task

parsing_flow (main flow)
├── clean_text_task
└── validate_task
```

**Code generation:**
```python
# run_cache/orchestration/scraping.py

@flow
async def stepstone_flow() -> dict:
    return await fetch_stepstone_task()

@flow
async def linkedin_flow() -> dict:
    return await fetch_linkedin_task()

@task
async def merge_task(stepstone: dict, linkedin: dict) -> dict:
    ...

@flow
async def scraping_flow() -> dict:
    stepstone = await stepstone_flow()
    linkedin = await linkedin_flow()
    return await merge_task(stepstone, linkedin)
```

**This matches the hierarchy perfectly:**
- `scraping` → main flow
- `scraping.stepstone` → subflow
- `scraping.stepstone.fetch` → task in subflow

---

## Problem 2: Standalones - NEEDS DECISION

**Question:** Can Prefect run tasks without wrapping in a flow?

**If NO:** Wrap all standalones in flows
```python
# run_cache/orchestration/standalones.py

@flow
async def validate_flow() -> bool:
    return await validate_task()

@flow
async def process_flow() -> dict:
    return await process_task()
```

**If YES:** Could create tasks without flows, but for consistency:
- Still wrap in flows so they're executable consistently
- Users can call via Prefect or directly

**Recommendation:** Always wrap standalones in flows for consistency. This way:
- All operations are executable via Prefect
- All operations are discoverable
- Standalones aren't second-class citizens

---

## Problem 3: Service Management - NEEDS DISCUSSION 🔴

**The Core Question:** How does a **library** in a **user project** manage services?

This is not like a global command-line tool. Let's think through scenarios:

### Scenario A: Local Development

**User workflow:**
```bash
cd my_project/
pip install pulpocore

# What should this do?
pulpo up  # Start: DB, Prefect, API, UI
pulpo down # Stop all
pulpo prefect run scraping_flow --param keywords="python"
```

**Problems:**
- Where do services run? Different machines, different setups
- Docker? Subprocess? Local processes?
- How to manage multiple users on same machine?
- Database: separate instance per project or shared?

### Scenario B: Docker-based Development

**User might have docker-compose.yml:**
```yaml
version: '3'
services:
  mongodb:
    image: mongo
  api:
    build: .
  prefect:
    image: prefecthq/prefect:3
  ui:
    image: ...
```

**Then:**
```bash
pulpo up      # Runs: docker-compose up
pulpo down    # Runs: docker-compose down
pulpo logs    # Runs: docker-compose logs
```

### Scenario C: Cloud Deployment

**User deploying to cloud:**
```bash
pulpo build           # Build Docker images
pulpo deploy --cloud  # Deploy to cloud platform
pulpo status          # Check cloud status
```

### Scenario D: Hybrid (Most Likely)

**Development:**
```bash
pulpo dev up    # Start local services (Docker or subprocesses)
pulpo dev down
pulpo dev logs
```

**Production:**
```bash
pulpo prod deploy  # Deploy to cloud
pulpo prod logs
```

---

## Key Design Questions for Service Management

### Q1: What should `pulpo up` actually do?

**Option A: Direct Docker Management**
```python
def up(self):
    # CLI directly orchestrates Docker
    docker_compose_up()
    wait_for_services()
```
- **Pro:** Simple, single interface
- **Con:** Requires Docker, doesn't match user's setup

**Option B: Use User's docker-compose.yml**
```python
def up(self):
    # Look for docker-compose.yml in project root
    # Run: docker-compose up
    subprocess.run(["docker-compose", "up", "-d"])
```
- **Pro:** Flexible, user has control
- **Con:** User must maintain docker-compose.yml

**Option C: Generate docker-compose.yml**
```python
def compile(self):
    # Generate docker-compose.yml based on used services
    # Then `pulpo up` uses it
    generate_docker_compose()

def up(self):
    subprocess.run(["docker-compose", "up", "-d"])
```
- **Pro:** Automatic, matches selected services
- **Con:** Complex generation logic

**Option D: Just provide code, user runs their way**
```bash
# CLI generates Prefect flows and Docker configs
pulpo compile

# User manages services their own way
docker-compose up
python -m api
prefect server start
```
- **Pro:** Maximum flexibility
- **Con:** More manual steps for users

### Q2: Should `pulpo` be a CLI command or just a library?

**Option A: Both**
```bash
pulpo up           # Typer CLI command
```
```python
from pulpo import CLI
cli = CLI()
cli.up()           # Programmatic interface
```

**Option B: Just library (user writes their own CLI)**
```python
# user_project/main.py
from pulpo import CLI

cli = CLI()

if __name__ == "__main__":
    cli.run()
```

**Option C: Generate user CLI as part of compile**
```python
# pulpo compile generates:
# run_cache/cli.py - User's custom CLI
# run_cache/manage.sh - Shell wrapper

# User runs:
python run_cache/cli.py up
# or
./run_cache/manage.sh up
```

### Q3: Where do services run?

**Option A: Docker Containers**
```bash
pulpo up
# Starts: MongoDB container, API container, Prefect container, UI container
```

**Option B: Local Processes**
```bash
pulpo up
# Starts: MongoDB subprocess, API subprocess, Prefect subprocess
```

**Option C: Mixed**
```bash
pulpo up --mode docker     # Use Docker
pulpo up --mode local      # Use local processes
pulpo up --mode cloud      # Deploy to cloud
```

**Option D: User's choice**
```bash
# User has docker-compose.yml
pulpo up
# Detects docker-compose.yml and uses it

# Or no docker-compose.yml
pulpo up --mode local
# Uses local processes
```

### Q4: What about development vs production?

**Option A: Single setup**
```bash
pulpo up        # Works for both dev and prod
```

**Option B: Separate commands**
```bash
pulpo dev up      # Development (hot reload, debug, etc)
pulpo prod up     # Production (optimized, scaled, etc)
```

**Option C: Configuration-based**
```bash
# pulpo.yaml
environment: development
services:
  api:
    reload: true
    debug: true
  db:
    persist: true

pulpo up  # Reads config and adjusts
```

### Q5: Project dependencies between services

**For example:**
```bash
pulpo up

# What order?
# 1. Start DB (others depend on it)
# 2. Wait for DB to be ready
# 3. Initialize DB schema
# 4. Start API (depends on DB)
# 5. Start Prefect (independent)
# 6. Start UI (depends on API)
```

Should CLI handle this or just run all together?

---

## My Recommendation

For a **library** in **user projects**, I suggest:

**Option: Hybrid Generation + Docker Compose**

```
pulpo compile
# Generates:
# - run_cache/docker-compose.yml (with all services)
# - run_cache/orchestration/ (Prefect flows)
# - run_cache/Dockerfile (API image)
# - etc

pulpo up
# Detects docker-compose.yml exists
# Runs: docker-compose up -d
# Manages dependencies in compose file

pulpo down
# Runs: docker-compose down

pulpo logs <service>
# Runs: docker-compose logs <service>

pulpo status
# Shows: docker-compose ps
```

**Benefits:**
- User has full control (docker-compose.yml is editable)
- Standard Docker tooling (no custom orchestration)
- Works locally and in CI/CD
- Services managed with correct dependencies
- Works with existing Docker knowledge

**Implementation:**
1. Generate `docker-compose.yml` that:
   - Has MongoDB, API, Prefect, UI services
   - Sets up dependencies (api depends_on: db)
   - Mounts volumes for code, data, etc
   - Sets environment variables

2. `pulpo up/down/logs/status` wraps Docker Compose

3. For Prefect specifically:
   ```bash
   pulpo prefect deploy <flow>  # Deploy flow to server
   pulpo prefect run <flow>     # Run flow directly
   ```

---

## Questions for You

Before we implement, please clarify:

1. **Flow Composition:** Use nested flows matching hierarchy? YES ✅

2. **Standalones:** Always wrap in flows even if Prefect allows bare tasks?
   - YES (consistency) or explore Prefect's capabilities first?

3. **Service Management Approach:**
   - Should we use Docker Compose as I suggested?
   - Or something else?
   - Is this for local dev, production, or both?
   - Should users be able to run without Docker?

4. **CLI Interface:**
   - Should users call `pulpo up` directly?
   - Or should they write their own CLI/script?
   - Should generated code include a management script?

5. **Development vs Production:**
   - Single `pulpo up` for both, or separate commands?
   - Different configs needed?

Once we clarify service management, we can finalize the implementation plan!
