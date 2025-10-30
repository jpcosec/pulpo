# Todo List Application Example

Simple todo list application demonstrating Pulpo Core's CRUD operations and workflow management.

## Overview

This example shows how to build a task management application with:
- Simple data models (User, Todo)
- CRUD operations for todos
- Workflow operations (status transitions)
- Hierarchical operation naming

## Project Structure

```
todo-app/
├── models/
│   ├── user.py         # User account model
│   └── todo.py         # Todo item model with status
└── operations/
    ├── crud.py         # Create, Read, Update, Delete operations
    └── workflow.py     # Status transitions and archival
```

## Models

### User
```python
@datamodel(name="User", tags=["user", "account"])
class User(Document):
    username: str          # Unique username
    email: str            # Email address
    created_at: datetime  # Account creation time
    updated_at: datetime  # Last update time
```

### Todo
```python
@datamodel(name="Todo", tags=["task", "todo"])
class Todo(Document):
    title: str                    # Task title
    description: str              # Detailed description
    status: TodoStatus            # pending | in_progress | completed
    created_by: str              # Creator username
    created_at: datetime         # Creation timestamp
    updated_at: datetime         # Last update timestamp
```

## Operations

### CRUD Operations (todos.crud.*)

All CRUD operations can run in parallel since they don't depend on each other.

```bash
# Create a new todo
pulpo todos crud create --input '{
  "title": "Learn Pulpo",
  "description": "Understand how Pulpo works",
  "created_by": "alice"
}'

# Read a todo
pulpo todos crud read --input '{"todo_id": "507f1f77bcf86cd799439011"}'

# Update a todo
pulpo todos crud update --input '{
  "todo_id": "507f1f77bcf86cd799439011",
  "title": "Updated title"
}'

# Delete a todo
pulpo todos crud delete --input '{"todo_id": "507f1f77bcf86cd799439011"}'
```

### Workflow Operations (todos.workflow.*)

Status transition operations that change todo state.

```bash
# Start working on a todo
pulpo todos workflow start --input '{"todo_id": "507f1f77bcf86cd799439011"}'

# Mark todo as completed
pulpo todos workflow complete --input '{"todo_id": "507f1f77bcf86cd799439011"}'

# Reopen a completed todo
pulpo todos workflow reopen --input '{"todo_id": "507f1f77bcf86cd799439011"}'
```

### Sync Operations (todos.sync.*)

Maintenance operations for data cleanup.

```bash
# Archive old completed todos
pulpo todos sync archive --input '{"days_old": 7}'
```

## Operation Hierarchy Graph (OHG)

```
todos (domain)
├── crud (category)
│   ├── create    ┐
│   ├── read      ├─ Can parallelize (no dependencies)
│   ├── update    ├─ Each is independent
│   └── delete    ┘
├── workflow (category)
│   ├── start     # Changes status
│   ├── complete  # Marks done
│   └── reopen    # Reopens completed
└── sync (category)
    └── archive   # Cleans up old todos
```

## Generated Artifacts

Running `pulpo compile` generates:

```
.run_cache/
├── generated_api.py              # FastAPI routes for CRUD + operations
├── generated_ui_config.ts        # React/UI configuration
└── orchestration/
    └── generated_flows.py        # Prefect workflows
```

### Generated API Endpoints

```
# CRUD endpoints
GET    /todos                      # List all todos
POST   /todos                      # Create new todo
GET    /todos/{id}                # Get todo by ID
PUT    /todos/{id}                # Update todo
DELETE /todos/{id}                # Delete todo

# Operation endpoints
POST   /operations/todos/crud/create
POST   /operations/todos/crud/read
POST   /operations/todos/crud/update
POST   /operations/todos/crud/delete
POST   /operations/todos/workflow/start
POST   /operations/todos/workflow/complete
POST   /operations/todos/workflow/reopen
POST   /operations/todos/sync/archive
```

### Generated CLI Commands

```
pulpo todos crud create
pulpo todos crud read
pulpo todos crud update
pulpo todos crud delete
pulpo todos workflow start
pulpo todos workflow complete
pulpo todos workflow reopen
pulpo todos sync archive
```

## Running the Example

### 1. Extract the project
```bash
tar -xzf todo-app.tar.gz
cd todo-app
```

### 2. Install Pulpo Core
```bash
pip install pulpo-core
```

### 3. Initialize the project
```bash
pulpo cli init
```

This creates:
- `.pulpo.yml` - Project configuration
- `.env` - Environment variables
- `Makefile` - Development commands
- `docker-compose.yml` - Services orchestration

### 4. Generate code
```bash
pulpo compile
```

This generates:
- API routes (FastAPI)
- CLI commands (Typer)
- React UI configuration
- Prefect workflows

### 5. Start services
```bash
pulpo up
```

This starts:
- MongoDB (database)
- FastAPI server (port 8000)
- React frontend (port 3000)
- Prefect orchestrator

### 6. Use the application

#### Via API
```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn Pulpo",
    "description": "Understand the framework",
    "created_by": "user123"
  }'
```

#### Via CLI
```bash
pulpo todos crud create --input '{
  "title": "Learn Pulpo",
  "description": "Understand the framework",
  "created_by": "user123"
}'
```

#### Via UI
Open http://localhost:3000 in browser

### 7. Stop services
```bash
pulpo down
```

## Key Concepts Demonstrated

### 1. Hierarchical Operation Naming
```
Domain: todos
Category: crud, workflow, sync
Operation: create, read, update, delete, start, complete, reopen, archive

Name format: {domain}.{category}.{operation}
Example: todos.crud.create
```

### 2. Async Operations
All operations are async:
```python
@operation(name="todos.crud.create", ...)
async def create_todo(input_data: CreateTodoInput) -> CreateTodoOutput:
    ...
```

### 3. Input/Output Models
Pydantic models for type validation:
```python
class CreateTodoInput(BaseModel):
    title: str
    description: str
    created_by: str

class CreateTodoOutput(BaseModel):
    success: bool
    todo_id: str
    message: str
```

### 4. Model Registration
Models and operations registered via decorators:
- `@datamodel` - Register data models
- `@operation` - Register operations

### 5. Metadata-Driven Generation
All code (API, CLI, UI, workflows) generated from decorator metadata.

## Use Cases

### Personal Task Management
Use for managing personal todo lists:
- Create tasks
- Track progress (pending → in_progress → completed)
- Archive old tasks

### Team Task Board
Extend with team collaboration:
- Assign todos to users
- Add due dates
- Add comments/notes

### Project Management
Integrate with larger system:
- Hierarchy of projects and tasks
- Time tracking
- Resource allocation

## Testing

All operations are covered by Phase 3 tests:
```bash
python -m pytest tests/phase3/test_real_example.py -v
```

Tests verify:
- Operations are discoverable
- Generated code is valid
- Flows execute correctly
- Status transitions work

## Next Steps

1. Customize for your use case
2. Add additional fields to models
3. Add more sophisticated workflows
4. Integrate with external systems
5. Add user authentication

---

**Pulpo Core v0.6.0** - Framework for building full-stack applications
