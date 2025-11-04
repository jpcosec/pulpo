# 1. Getting Started

## Quick Start Guide

### What You'll Learn
In this quick start, you'll learn how to get Pulpo Core running in under 5 minutes.

### Prerequisites
- Python 3.11 or higher
- pip or Poetry for package management
- Docker (optional, but recommended for MongoDB and services)
- Basic familiarity with Python and command line

### The Fastest Way to Start: Run an Example Project

Pulpo Core comes with three complete, pre-built example projects. The easiest way to get started is to run one of these.

#### Step 1: Navigate to an Example
```bash
cd examples/pokemon-app    # or todo-app, ecommerce-app
```

#### Step 2: Initialize Services
```bash
./main init
```
This command sets up all necessary services and dependencies.

#### Step 3: Generate Code
```bash
./main compile
```
This generates the API, CLI, and UI from your decorators.

#### Step 4: Start Everything
```bash
./main up
```

#### Step 5: Access Your Application
- **API:** http://localhost:8000/docs (Swagger UI)
- **UI:** http://localhost:3000 (React Admin Interface)
- **CLI:** Use `./main help` to see available commands

That's it! Your full-stack application is now running.

---

## Installation & Setup

### Option 1: Install from PyPI (Recommended for Users)

```bash
pip install pulpo-core
```

This installs the framework as a library that you can import into your own projects.

### Option 2: Install from Source (For Development)

```bash
git clone <repository-url>
cd pulpo
poetry install
```

Install with workflow support (includes Prefect):
```bash
poetry install -E workflow
```

### Option 3: Docker Installation

If you prefer not to install dependencies locally:

```bash
docker run -it pulpo-core:latest /bin/bash
```

(Requires Docker to be running)

### Verify Installation

```bash
python -c "from core import datamodel, operation; print('Pulpo Core installed!')"
```

---

## Your First Project

### Create a New Project Structure

Create a new directory for your project:

```bash
mkdir my-pulpo-app
cd my-pulpo-app
```

### Create the Main Entrypoint File

Create a file named `main` (no extension):

```bash
cat > main << 'EOF'
#!/usr/bin/env python3
"""Your Pulpo project entrypoint."""
from models.user import User
from models.product import Product
from operations.create_user import create_user
from operations.purchase import purchase
from core import CLI

if __name__ == "__main__":
    app = CLI()
    app.run()
EOF

chmod +x main
```

### Create Your First Data Model

Create `models/` directory:
```bash
mkdir -p models
```

Create `models/user.py`:
```python
from beanie import Document
from core import datamodel

@datamodel(
    name="User",
    description="A user in the system",
    tags=["users"]
)
class User(Document):
    """Represents a user account."""

    email: str
    name: str
    age: int
    is_active: bool = True

    class Settings:
        name = "users"  # MongoDB collection name
```

### Create Your First Operation

Create `operations/` directory:
```bash
mkdir -p operations
```

Create `operations/create_user.py`:
```python
from pydantic import BaseModel
from core import operation

class CreateUserInput(BaseModel):
    email: str
    name: str
    age: int

class CreateUserOutput(BaseModel):
    user_id: str
    message: str

@operation(
    name="user.create",
    description="Create a new user",
    inputs=CreateUserInput,
    outputs=CreateUserOutput,
    category="user-management"
)
async def create_user(input: CreateUserInput) -> CreateUserOutput:
    """Create a new user in the system."""
    # Your logic here
    return CreateUserOutput(
        user_id="generated-id",
        message=f"User {input.name} created successfully"
    )
```

### Generate Your Application

```bash
./main compile
```

This generates:
- REST API endpoints
- CLI commands
- React UI configuration
- Prefect workflow definitions

### Run Your Application

```bash
./main up
```

Your application is now available at:
- **API:** http://localhost:8000
- **UI:** http://localhost:3000
- **CLI:** `./main ops create user.create --input '{"email":"test@example.com","name":"John","age":30}'`

---

## Running Examples

### Example 1: Todo App (Beginner)

Perfect for learning the basics of CRUD operations and simple workflows.

```bash
cd examples/todo-app
./main init
./main compile
./main up
```

Then explore:
- Create a todo: `./main ops create todos --input '{"title":"Learn Pulpo","description":"Master the framework"}'`
- View API docs: http://localhost:8000/docs
- Use UI: http://localhost:3000

### Example 2: Pokemon App (Intermediate)

Demonstrates domain modeling, game mechanics, and complex operations.

```bash
cd examples/pokemon-app
./main init
./main compile
./main up
```

This example shows:
- Multiple related models (Pokemon, Trainer, Attack, Element)
- Complex business logic (battles, evolution, training)
- Hierarchical operations for orchestration

### Example 3: E-commerce App (Advanced)

Shows real-world patterns like parallel checkout and sequential fulfillment.

```bash
cd examples/ecommerce-app
./main init
./main compile
./main up
```

This example demonstrates:
- Nested data models (Orders, Payments, Fulfillment)
- Parallel execution (processing multiple payments)
- Sequential pipelines (checkout → fulfillment → shipping)
- Advanced orchestration patterns

### Run Tests on Examples

Each example includes tests. Run them:

```bash
cd examples/pokemon-app
./main test
```

---

## Common Setup Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'core'"

**Solution:** Make sure Pulpo Core is installed:
```bash
pip install pulpo-core
# or if developing locally
pip install -e .
```

### Issue: "Connection refused" when starting services

**Solution:** MongoDB might not be running. Start it:
```bash
./main db start
```

### Issue: "Port 8000 already in use"

**Solution:** Specify a different port:
```bash
./main api --port 8001
```

### Issue: "Permission denied" when running ./main

**Solution:** Make the file executable:
```bash
chmod +x main
```

---

## Next Steps

Now that you have Pulpo Core running, here's what to do next:

1. **Explore the API:** Visit http://localhost:8000/docs to see auto-generated API documentation
2. **Try the UI:** Visit http://localhost:3000 to explore the admin interface
3. **Read Core Concepts:** Understand the "Define Once, Generate Everywhere" pattern
4. **Understand Decorators:** Learn how `@datamodel` and `@operation` work
5. **Study Architecture:** Understand how the framework components fit together
6. **Review Examples:** Study the complete example projects to see best practices
7. **Start Building:** Create your own models and operations

---

## Getting Help

### Built-in Help

```bash
# Show all available commands
./main help

# Show help for a specific model
./main help model User

# Show help for a specific operation
./main help operation user.create

# Show framework documentation
./main help framework datamodel
```

### Documentation

- **[Core Concepts](02_Core_Concepts.md)** - Understand the framework design
- **[Architecture](03_Architecture.md)** - Learn system components
- **[Examples](15_Examples_Deep_Dive.md)** - Study complete applications

### Troubleshooting

See [19. Troubleshooting & FAQ](19_Troubleshooting_FAQ.md) for common issues and solutions.

### Community & Support

- Check example projects for patterns and best practices
- Review framework documentation in `/docs/` directory
- Check git issues for known problems

---

## Key Concepts to Remember

1. **Decorators register metadata** - `@datamodel` and `@operation` don't change execution, just register information
2. **Code is generated** - Running `./main compile` creates API, CLI, and UI code in `.run_cache/`
3. **All operations are async** - Operations must be `async def` functions
4. **Main entrypoint controls discovery** - Only models and operations imported in `main` are discovered
5. **Services run independently** - API, UI, and Database run as separate services managed by the CLI

---

**You're now ready to build full-stack applications with Pulpo Core!**
