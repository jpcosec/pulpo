# External Project Structure Guide

This document shows how to structure your external project to work with the JobHunter Core Framework.

## Core Principle

**The framework is path-agnostic.** You organize your code however makes sense. The only requirement is:

1. Create models with `@datamodel` decorator
2. Create operations with `@operation` decorator
3. Import them in an entry point **before** calling `compile_all()`

## Project Structure Options

### Option 1: Simple/Flat Structure (Recommended for Small Projects)

```
my-pokemon-app/
├── __main__.py              # Entry point for compilation
├── models.py                # All models in one file
├── operations.py            # All operations in one file
├── .jobhunter.yml          # Configuration (optional)
└── docs/                    # Generated docs (created by framework)
```

**models.py:**
```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="Pokemon",
    description="A Pokemon creature",
    tags=["pokemon"]
)
class Pokemon(Document):
    name: str = Field(..., description="Pokemon name")
    level: int = Field(default=1, description="Level 1-100")

    class Settings:
        name = "pokemons"

@datamodel(
    name="Trainer",
    description="A Pokemon trainer",
    tags=["trainer"]
)
class Trainer(Document):
    name: str = Field(..., description="Trainer name")

    class Settings:
        name = "trainers"
```

**operations.py:**
```python
from pydantic import BaseModel, Field
from core.decorators import operation

class CatchPokemonInput(BaseModel):
    trainer_name: str = Field(..., description="Trainer name")
    pokemon_name: str = Field(..., description="Pokemon name")

class CatchPokemonOutput(BaseModel):
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Result message")

@operation(
    name="catch_pokemon",
    description="Trainer catches a Pokemon",
    inputs=CatchPokemonInput,
    outputs=CatchPokemonOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
    return CatchPokemonOutput(
        success=True,
        message=f"Caught {input_data.pokemon_name}!"
    )
```

**__main__.py:**
```python
"""Entry point for code generation."""

# Import models and operations - decorators auto-register them
import my_pokemon_app.models
import my_pokemon_app.operations

# Now compile
from core import compile_all

if __name__ == "__main__":
    compile_all()
```

**Run:**
```bash
python3 -m my_pokemon_app
```

---

### Option 2: Organized Structure (Recommended for Medium Projects)

```
my-pokemon-app/
├── __main__.py              # Entry point for compilation
├── models/
│   ├── __init__.py
│   ├── pokemon.py
│   ├── trainer.py
│   └── attack.py
├── operations/
│   ├── __init__.py
│   ├── management.py        # catch, train, etc
│   ├── battles.py           # pokemon vs pokemon
│   └── evolution.py         # evolution operations
├── .jobhunter.yml          # Configuration (optional)
└── docs/                    # Generated docs
```

**models/__init__.py:**
```python
"""Pokemon models."""

from my_pokemon_app.models.pokemon import Pokemon
from my_pokemon_app.models.trainer import Trainer
from my_pokemon_app.models.attack import Attack

__all__ = ["Pokemon", "Trainer", "Attack"]
```

**models/pokemon.py:**
```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="Pokemon",
    description="A Pokemon with stats and moves",
    tags=["pokemon", "creature"]
)
class Pokemon(Document):
    name: str = Field(..., description="Pokemon name")
    level: int = Field(default=1, description="Level 1-100")
    health: int = Field(default=20, description="HP")

    class Settings:
        name = "pokemons"
```

**operations/__init__.py:**
```python
"""Pokemon operations."""

# Import modules to register decorators
from my_pokemon_app.operations import management, battles, evolution

__all__ = ["management", "battles", "evolution"]
```

**operations/management.py:**
```python
from pydantic import BaseModel, Field
from core.decorators import operation

class CatchPokemonInput(BaseModel):
    trainer_name: str = Field(...)
    pokemon_name: str = Field(...)

class CatchPokemonOutput(BaseModel):
    success: bool = Field(...)

@operation(
    name="catch_pokemon",
    description="Trainer catches a Pokemon",
    inputs=CatchPokemonInput,
    outputs=CatchPokemonOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
    return CatchPokemonOutput(success=True)
```

**__main__.py:**
```python
"""Entry point for code generation."""

import my_pokemon_app.models
import my_pokemon_app.operations

from core import compile_all

if __name__ == "__main__":
    compile_all()
```

---

### Option 3: Feature-Based Structure (Recommended for Large Projects)

```
my-pokemon-app/
├── __main__.py
├── pokemon/
│   ├── models.py
│   ├── operations.py
│   └── __init__.py
├── trainer/
│   ├── models.py
│   ├── operations.py
│   └── __init__.py
├── battle/
│   ├── models.py
│   ├── operations.py
│   └── __init__.py
├── .jobhunter.yml
└── docs/
```

**pokemon/__init__.py:**
```python
"""Pokemon feature."""

from my_pokemon_app.pokemon import models as pokemon_models
from my_pokemon_app.pokemon import operations as pokemon_operations

__all__ = ["pokemon_models", "pokemon_operations"]
```

**pokemon/models.py:**
```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(name="Pokemon", description="...", tags=["pokemon"])
class Pokemon(Document):
    # ...
    class Settings:
        name = "pokemons"
```

**pokemon/operations.py:**
```python
from pydantic import BaseModel, Field
from core.decorators import operation

@operation(
    name="train_pokemon",
    description="Train a Pokemon",
    # ...
)
async def train_pokemon(input_data):
    return TrainPokemonOutput()
```

**__main__.py:**
```python
"""Entry point."""

# Import all features
from my_pokemon_app import pokemon, trainer, battle

from core import compile_all

if __name__ == "__main__":
    compile_all()
```

---

## Essential Requirements

### 1. Entry Point (`__main__.py`)

Every project **must** have a `__main__.py` that:

```python
"""Project entry point for code generation."""

# Step 1: Import everything that uses @datamodel or @operation decorators
from my_app import models, operations

# Step 2: Call compile_all()
from core import compile_all

if __name__ == "__main__":
    compile_all()
```

**Why?** Decorators auto-register models/operations when imported. The framework reads from registries, not the file system.

### 2. Models with `@datamodel`

```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="Pokemon",                    # ✅ Required: unique name
    description="...",                 # ✅ Required: human-readable description
    tags=["pokemon"]                   # Optional: for organization
)
class Pokemon(Document):
    name: str = Field(..., description="Pokemon name")  # ✅ Required: field descriptions

    class Settings:
        name = "pokemons"              # ✅ Required: MongoDB collection name
```

**Checklist:**
- ✅ `@datamodel` decorator with `name`, `description`
- ✅ All fields have `description` parameter
- ✅ Inherits from `Document` (Beanie)
- ✅ `class Settings` with collection `name`

### 3. Operations with `@operation`

```python
from pydantic import BaseModel, Field
from core.decorators import operation

class MyOperationInput(BaseModel):
    param1: str = Field(..., description="What is this?")

class MyOperationOutput(BaseModel):
    result: str = Field(..., description="What is this?")

@operation(
    name="my_operation",               # ✅ Required: unique name
    description="...",                 # ✅ Required: what it does
    inputs=MyOperationInput,           # ✅ Required: Pydantic model
    outputs=MyOperationOutput,         # ✅ Required: Pydantic model
    category="management",             # ✅ Required: for organization (management, business, etc)
    models_in=["Pokemon"],             # ✅ Required: list of input model names (from registy)
    models_out=["Trainer"]             # ✅ Required: list of output model names
)
async def my_operation(input_data: MyOperationInput) -> MyOperationOutput:
    return MyOperationOutput(result="...")
```

**Checklist:**
- ✅ `@operation` decorator with `name`, `description`, `category`
- ✅ Input/output Pydantic models with field descriptions
- ✅ `models_in` and `models_out` (must match registered model names)
- ✅ `async` function

### 4. Optional: `.jobhunter.yml` Configuration

```yaml
project_name: "My Pokemon App"
version: "1.0.0"

# Basic config - most projects don't need this
server:
  host: localhost
  port: 8000
```

**Usually not needed.** Only for advanced configuration.

---

## Running the Framework

### Step 1: Define Models and Operations

Create your models.py, operations.py, etc.

### Step 2: Create Entry Point

Create `__main__.py` that imports everything and calls `compile_all()`.

### Step 3: Generate Code

```bash
# Run from project root
python3 -m my_app
```

**Generates:**
- `.run_cache/generated_api.py` - FastAPI app
- `.run_cache/generated_frontend/` - React UI
- `.run_cache/cli/jobhunter` - CLI tool
- `docs/` - Architecture diagrams

### Step 4: Use Generated Code

**API:**
```bash
python3 -m uvicorn .run_cache.generated_api:app --reload
```

**Frontend:**
```bash
cd .run_cache/generated_frontend
npm install
npm run dev
```

**CLI:**
```bash
./.run_cache/cli/jobhunter list
```

---

## Common Patterns

### Pattern 1: Organizing by Feature

```
app/
├── __main__.py
├── features/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── operations.py
│   ├── posts/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── operations.py
```

**__main__.py:**
```python
from app.features import users, posts
from core import compile_all

if __name__ == "__main__":
    compile_all()
```

### Pattern 2: Shared Models, Separate Operations

```
app/
├── __main__.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── post_service.py
```

**__main__.py:**
```python
from app import models, services
from core import compile_all

if __name__ == "__main__":
    compile_all()
```

### Pattern 3: Single File (Very Small Projects)

```
app.py
```

```python
from beanie import Document
from pydantic import BaseModel, Field
from core.decorators import datamodel, operation
from core import compile_all

@datamodel(name="Item", description="...", tags=[])
class Item(Document):
    name: str = Field(...)
    class Settings:
        name = "items"

@operation(name="create_item", description="...", ...)
async def create_item(input_data):
    return CreateItemOutput()

if __name__ == "__main__":
    compile_all()
```

**Run:** `python3 app.py`

---

## Checklist: Is Your Project Ready?

- ✅ All models use `@datamodel` decorator
- ✅ All models have `description` parameter
- ✅ All fields have `description` parameter
- ✅ All models inherit from `beanie.Document`
- ✅ All models have `class Settings` with collection `name`
- ✅ All operations use `@operation` decorator
- ✅ All operations have `description` and `category`
- ✅ All operations have `inputs` and `outputs` (Pydantic models)
- ✅ All operations have `models_in` and `models_out`
- ✅ `__main__.py` imports all models and operations
- ✅ `__main__.py` calls `compile_all()`
- ✅ Entry point is runnable: `python3 -m my_app`

---

## Troubleshooting

### "Model 'X' already registered"

**Problem:** You're importing the same model twice.

**Solution:** Check your `__main__.py` - make sure you're not importing the same module twice through different import paths.

### "Unknown model in models_in/models_out"

**Problem:** Operation references a model name that doesn't exist.

**Solution:** Check the model's `@datamodel(name="...")` parameter matches what you put in `models_in`/`models_out`.

### "No models or operations registered"

**Problem:** `compile_all()` ran but nothing was generated.

**Solution:** Make sure `__main__.py` imports your models and operations **before** calling `compile_all()`. The decorator registration happens during import.

### "ImportError: cannot import..."

**Problem:** Entry point tries to import something that doesn't exist.

**Solution:** Make sure all imports in `__main__.py` are correct and point to actual files/modules.

---

## Next Steps

1. Choose a structure that matches your project size
2. Create models with `@datamodel`
3. Create operations with `@operation`
4. Create `__main__.py` that imports everything
5. Run: `python3 -m my_app`
6. Use generated code in `.run_cache/`

Questions? Check the example in `core/core/examples/` for a working reference!
