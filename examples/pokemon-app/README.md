# Pokemon Demo Project

Example Pulpo Core project demonstrating operation hierarchy and data modeling using the Pokemon domain.

## Overview

This project shows how to structure operations using hierarchical naming and demonstrates:
- Model definition with `@datamodel` decorator
- Operation organization with `@operation` decorator
- Parallel operations (Pokemon battles)
- Sequential operations (Evolution workflow)
- Operation composition (Trainer battles depend on Pokemon battles)

## Project Structure

```
test-project-demo/
├── models/                    # Data models
│   ├── pokemon.py            # Pokemon creature model
│   ├── trainer.py            # Trainer model
│   ├── attack.py             # Attack/Move model
│   ├── element.py            # Element/Type model
│   └── fight_result.py        # Battle result model
└── operations/               # Operations (operations)
    ├── pokemon_management.py  # Catch, train, create trainer
    ├── pokemon_battles.py     # Pokemon vs Pokemon, Trainer vs Trainer
    └── pokemon_evolution.py   # Evolution stages
```

## Models

### Pokemon
```python
@datamodel(name="Pokemon", tags=["pokemon", "creature"])
class Pokemon(Document):
    """A Pokemon with stats, type, and attacks."""
```
- Health, Attack, Defense, Special Attack, Special Defense, Speed stats
- Attacks/Moves list
- Evolution tracking (evolves_into, evolution_level)

### Trainer
```python
@datamodel(name="Trainer", tags=["trainer"])
class Trainer(Document):
    """A Pokemon trainer managing a team of Pokemon."""
```

### Related Models
- **Attack**: Move/Attack definition with power, accuracy, type
- **Element**: Pokemon type/element definition
- **FightResult**: Battle outcome record

## Operations

### Management Category
Operations organized under `pokemon.management.*`:

```
pokemon.management.catch            # Trainer catches a Pokemon
pokemon.management.train            # Train Pokemon to increase stats
pokemon.management.trainer_create   # Create new trainer with starter
```

**These can run in parallel** - no dependencies between them.

### Battles Category
Operations under `pokemon.battles.*`:

```
pokemon.battles.execute             # Single Pokemon battle
pokemon.battles.trainer_execute     # Full Trainer battle (multiple Pokemon)
```

**Sequential execution** - trainer battle uses Pokemon battle logic.

### Evolution Category
Operations under `pokemon.evolution.*`:

```
pokemon.evolution.stage1            # Evolve to first form
pokemon.evolution.stage2            # Evolve to final form
```

**Sequential workflow** - Stage 2 requires completing Stage 1.

## Generated CLI Commands

After running `pulpo compile`, operations create CLI commands:

```bash
# Management operations
pulpo pokemon management catch --input '{"trainer_name": "Ash", "pokemon_name": "Pikachu", "element": "Electric"}'
pulpo pokemon management train --input '{"pokemon_name": "Pikachu", "training_hours": 100}'
pulpo pokemon management trainer_create --input '{"trainer_name": "Misty", "region": "Cerulean"}'

# Battle operations
pulpo pokemon battles execute --input '{"pokemon1_name": "Pikachu", "pokemon2_name": "Charizard"}'
pulpo pokemon battles trainer_execute --input '{"trainer1_name": "Ash", "trainer2_name": "Brock"}'

# Evolution operations
pulpo pokemon evolution stage1 --input '{"pokemon_name": "Charmander"}'
pulpo pokemon evolution stage2 --input '{"pokemon_name": "Charmeleon"}'
```

## API Endpoints

Generated FastAPI endpoints:

```
POST /operations/pokemon/management/catch
POST /operations/pokemon/management/train
POST /operations/pokemon/management/trainer_create
POST /operations/pokemon/battles/execute
POST /operations/pokemon/battles/trainer_execute
POST /operations/pokemon/evolution/stage1
POST /operations/pokemon/evolution/stage2
```

## Key Concepts Demonstrated

### 1. Hierarchical Operation Naming
```python
@operation(name="pokemon.management.catch")
@operation(name="pokemon.battles.execute")
@operation(name="pokemon.evolution.stage1")
```

Naming convention: `DOMAIN.CATEGORY.OPERATION`
- **Domain**: pokemon (the project/namespace)
- **Category**: management, battles, evolution (logical grouping)
- **Operation**: catch, execute, stage1 (specific action)

### 2. Operation Hierarchy Graph (OHG)
Shows execution flow and containment:

```
pokemon (domain)
├── management
│   ├── catch     ┐ (can parallelize)
│   ├── train     ├─→ (sequential if needed)
│   └── trainer_create
├── battles
│   ├── execute   (fundamental operation)
│   └── trainer_execute (uses execute internally)
└── evolution
    ├── stage1    ─→ (sequential)
    └── stage2
```

### 3. Async Operations
All operations are async functions:

```python
@operation(name="pokemon.management.catch", ...)
async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
    return CatchPokemonOutput(...)
```

### 4. I/O Models with Pydantic
```python
class CatchPokemonInput(BaseModel):
    trainer_name: str
    pokemon_name: str
    element: str

class CatchPokemonOutput(BaseModel):
    success: bool
    message: str
    team_size: int
```

## Using This Example

### 1. Extract the Project
```bash
tar -xzf demo-project.tar.gz
cd test-project-demo
```

### 2. Install Dependencies
```bash
pip install pulpo-core
```

### 3. Initialize Infrastructure
```bash
pulpo cli init
```

### 4. Generate Code
```bash
pulpo compile
```

### 5. Start Services
```bash
pulpo up
```

### 6. Use the API
```bash
curl -X POST http://localhost:8000/operations/pokemon/management/catch \
  -H "Content-Type: application/json" \
  -d '{"trainer_name":"Ash","pokemon_name":"Pikachu","element":"Electric"}'
```

## What This Demonstrates

✅ **Decorator-based metadata**: @datamodel and @operation decorators
✅ **Hierarchical operation naming**: Domain.category.operation structure
✅ **Parallel operations**: Management operations (no dependencies)
✅ **Sequential operations**: Evolution workflow (stage1 → stage2)
✅ **Async design**: All operations are async
✅ **Type safety**: Pydantic models for I/O validation
✅ **Code generation**: Automatic API, CLI, UI from metadata

## Next Steps

For a simpler example, see: **Todo List Application**
For a complex example, see: **E-commerce System**

---

**Pulpo Core v0.6.0** - Metadata-driven code generation framework
