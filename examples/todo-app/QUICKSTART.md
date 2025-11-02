# Todo List Demo - Quick Start Guide

Get the Todo List demo running in 5 minutes.

## Prerequisites

- Python 3.11+
- Pulpo Core installed: `pip install pulpo-core`
- Docker (for MongoDB, optional - can use local MongoDB)

## Quick Start

### 1. Initialize Project
```bash
cd todo-app
./main init
```

What this does:
- Sets up `.env` file with local MongoDB connection
- Initializes project configuration

### 2. Generate Code
```bash
./main compile
```

What this does:
- Discovers all models (User, Todo) from `main` entrypoint
- Discovers all workflow operations from `main` entrypoint
- Generates:
  - FastAPI routes in `.run_cache/generated_api.py` (includes auto-generated CRUD)
  - React UI configuration in `.run_cache/generated_ui_config.ts`
  - Prefect workflows in `.run_cache/orchestration/`
  - `registry.json` for debugging (check what was discovered)

### 3. Start Services
```bash
./main up
```

What this does:
- Starts MongoDB (database)
- Starts FastAPI API server (http://localhost:8000)
- Starts React UI (http://localhost:3000)
- Starts Prefect orchestrator (http://localhost:4200)

Wait ~30 seconds for all services to be healthy.

### 4. Verify Everything Works

#### Check Registry (Debugging)
```bash
cat .run_cache/registry.json | head -50
```

Should show:
- 2 models: User, Todo
- 4 operations: todos.workflow.start, todos.workflow.complete, todos.workflow.reopen, todos.sync.archive

#### Check API is Running
```bash
curl http://localhost:8000/docs
```

Should show OpenAPI documentation with all endpoints.

#### Create a Todo (CRUD - Automatic)
```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn Pulpo",
    "description": "Understand the framework",
    "status": "pending",
    "created_by": "alice"
  }'
```

Save the returned `id` for next steps.

#### List Todos
```bash
curl http://localhost:8000/todos
```

#### Get Specific Todo
```bash
curl http://localhost:8000/todos/{id}
```

#### Update Todo
```bash
curl -X PUT http://localhost:8000/todos/{id} \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

#### Delete Todo
```bash
curl -X DELETE http://localhost:8000/todos/{id}
```

#### Execute a Workflow Operation (Custom)
```bash
# Start working on a todo
curl -X POST http://localhost:8000/operations/todos/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"todo_id": "{id}"}'

# Mark as complete
curl -X POST http://localhost:8000/operations/todos/workflow/complete \
  -H "Content-Type: application/json" \
  -d '{"todo_id": "{id}"}'

# Reopen if needed
curl -X POST http://localhost:8000/operations/todos/workflow/reopen \
  -H "Content-Type: application/json" \
  -d '{"todo_id": "{id}"}'

# Archive old completed todos
curl -X POST http://localhost:8000/operations/todos/sync/archive \
  -H "Content-Type: application/json" \
  -d '{"days_old": 7}'
```

#### View UI
Open http://localhost:3000 in your browser

#### View API Docs
Open http://localhost:8000/docs in your browser

#### View Graphs
```bash
./main graph
./main flows
```

Generates Mermaid diagrams in `docs/` showing:
- Model relationships
- Operation hierarchy

### 5. Stop Services
```bash
./main down
```

## Project Structure

```
todo-app/
├── main                    # Executable entrypoint (imports models + operations)
├── QUICKSTART.md          # This file
├── README.md              # Comprehensive documentation
├── models/
│   ├── user.py            # User account model
│   └── todo.py            # Todo item with status
└── operations/
    └── workflow.py        # Status transitions and archival
```

**Note:** CRUD operations (create, read, update, delete) are **automatically generated** by Pulpo from the `@datamodel` decorator. No need to define them explicitly!

## How It Works

1. **`main` file** imports all models and operations
   - When imported, decorators (`@datamodel`, `@operation`) register metadata
   - Registries now populated with models and operations

2. **`./main compile`** runs code generators
   - Reads from registries (populated by imports in step 1)
   - Generates FastAPI routes with **automatic CRUD endpoints**
   - Generates React UI config, Prefect workflows

3. **`./main up`** starts all services
   - MongoDB listens on localhost:27017
   - FastAPI listens on 0.0.0.0:8000
   - React listens on localhost:3000
   - Prefect listens on localhost:4200

4. **CRUD endpoints** auto-generated from `@datamodel`
   - GET /todos - List all todos
   - POST /todos - Create new todo
   - GET /todos/{id} - Get specific todo
   - PUT /todos/{id} - Update todo
   - DELETE /todos/{id} - Delete todo
   - Same for /users

5. **Workflow operations** are custom
   - Defined as `@operation` decorators in `operations/workflow.py`
   - Available via `/operations/todos/workflow/*`

## CLI Commands Available

```bash
./main status              # Show project status
./main models              # List registered models
./main compile             # Generate artifacts
./main graph               # Generate relationship diagrams
./main flows               # Generate operation flows
./main docs                # Generate documentation
./main api                 # Start API only
./main up                  # Start all services
./main down                # Stop all services
./main init                # Initialize services
./main clean               # Remove generated artifacts
./main lint                # Lint models and operations
./main ops_list            # List all operations
./main db start/stop       # Manage database
./main prefect start/stop  # Manage Prefect
```

## Debugging

### View Registry
The `registry.json` file shows exactly what was discovered:
```bash
./main compile
cat .run_cache/registry.json | python -m json.tool
```

Should show:
- **2 models**: User, Todo
- **4 operations**: todos.workflow.start, todos.workflow.complete, todos.workflow.reopen, todos.sync.archive

If models/operations are missing, check that `main` file imports them all.

### Check Logs
```bash
./main logs  # View service logs
```

### Restart Services
```bash
./main down
./main up
```

### Reset Everything
```bash
./main clean
./main compile
./main up
```

## Troubleshooting

**"Port already in use"**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
./main up
```

**"MongoDB connection refused"**
```bash
# Make sure MongoDB is started
./main db start
# Or use Docker
docker run -d -p 27017:27017 mongo:latest
```

**"Models not found in registry"**
```bash
./main compile
cat .run_cache/registry.json | grep "models" -A 20
```

If no models listed, check that `main` file imports User and Todo.

**"No workflow operations showing"**
```bash
./main compile
cat .run_cache/registry.json | grep "operations" -A 30
```

Should list todos.workflow.* operations. If not, verify `operations/workflow.py` is imported in `main`.

## Next Steps

1. **Explore the code**: Check `models/` and `operations/` to understand structure
2. **Use CRUD operations**: Create, read, update, delete todos via API
3. **Execute workflows**: Change todo status using workflow operations
4. **Customize**: Add new fields to Todo model or new workflow operations
5. **Integrate**: Connect to notification services, logging, etc.

---

**Questions?** Check README.md for comprehensive documentation.
