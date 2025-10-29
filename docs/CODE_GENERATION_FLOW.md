# Code Generation Flow (Import-Based Registration)

## Overview

The framework now uses **import-based registration** instead of file-system discovery. This means:

✅ **Path-agnostic** - folder structure doesn't matter
✅ **Flexible** - organize code however you want
✅ **Simple** - just import your models/operations, then compile

## How It Works

### Step 1: Define Models and Operations

Create your models and operations anywhere with decorators:

```python
# my_app/models.py
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="Pokemon",
    description="A Pokemon",
    tags=["pokemon"]
)
class Pokemon(Document):
    name: str = Field(..., description="Name")
```

```python
# my_app/operations.py
from pydantic import BaseModel, Field
from core.decorators import operation

@operation(
    name="catch_pokemon",
    description="Catch a Pokemon",
    inputs=CatchInput,
    outputs=CatchOutput,
    models_in=["Pokemon"],
    models_out=["Pokemon"]
)
async def catch_pokemon(input_data: CatchInput) -> CatchOutput:
    return CatchOutput(...)
```

### Step 2: Create Entry Point

Create an entry point that imports everything BEFORE compilation:

```python
# my_app/__main__.py
"""Entry point for code generation."""

# Import models/operations - decorators auto-register them
from my_app import models, operations

# Now compile
from core import compile_all

if __name__ == "__main__":
    compile_all()
```

### Step 3: Generate Code

```bash
python3 -m my_app
# Generates:
#   - .run_cache/generated_api.py
#   - .run_cache/generated_frontend/
#   - .run_cache/cli/jobhunter
#   - docs/
```

## For the Framework Examples

The Pokemon examples are already set up:

```bash
# Generate code from framework examples
python3 -m core.examples
```

This:
1. Imports `core.examples` (which imports all models/operations)
2. Decorators register everything in ModelRegistry/OperationRegistry
3. Calls `compile_all()` which reads from registries
4. Generates code

## Project Structure (Flexible)

You can organize code however you want:

```
# Option 1: Flat
my-project/
├── models.py
├── operations.py
└── __main__.py

# Option 2: By feature
my-project/
├── pokemon/
│   ├── models.py
│   ├── operations.py
│   └── __init__.py
├── trainer/
│   ├── models.py
│   ├── operations.py
│   └── __init__.py
└── __main__.py

# Option 3: Traditional
my-project/
├── models/
│   ├── pokemon.py
│   ├── trainer.py
│   └── __init__.py
├── operations/
│   ├── management.py
│   ├── battles.py
│   └── __init__.py
└── __main__.py
```

All work the same way - just import everything in `__main__.py`.

## Key Changes from Old System

| Old (File-System Discovery) | New (Import-Based) |
|---|---|
| Scanned `models/` and `operations/` folders | You import: `from my_app import models, operations` |
| Used `.jobhunter.yml` for discovery paths | Config only for non-code settings |
| `make compile` auto-discovered files | `make compile` requires user to import first |
| Folder structure = required | Folder structure = optional |

## Usage Pattern

**Framework Examples (already set up):**
```bash
cd core/
python3 -m core.examples
```

**Your Project:**
```bash
# 1. Create __main__.py with imports
# 2. Run:
python3 -m my_app
```

Or integrate into Makefile:

```makefile
codegen:
	python3 -m my_app
```

## Benefits

1. **Path-agnostic** - No folder structure requirements
2. **Explicit** - You control what gets imported and registered
3. **Simple** - No special discovery logic, just Python imports
4. **Flexible** - Organize code however makes sense for your project
5. **Clear dependencies** - `__main__.py` shows exactly what's being compiled

## If You Have Existing Projects

Just create a simple `__main__.py`:

```python
# Old: made discoveries automatic
# make compile  # scanned models/ and operations/

# New: explicit imports
# __main__.py
from my_app import models, operations
from core import compile_all

if __name__ == "__main__":
    compile_all()

# Run:
# python3 -m my_app
```
