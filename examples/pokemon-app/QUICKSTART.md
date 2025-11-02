# Pokemon Demo - Quick Start Guide

Get the Pokemon demo running in 5 minutes.

## Prerequisites

- Python 3.11+
- Pulpo Core installed: `pip install pulpo-core`
- Docker (for MongoDB, optional - can use local MongoDB)

## Quick Start

### 1. Initialize Project
```bash
cd pokemon-app
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
- Discovers all models (Pokemon, Trainer, Attack, Element, FightResult) from `main` entrypoint
- Discovers all operations (management, battles, evolution) from `main` entrypoint
- Generates:
  - FastAPI routes in `.run_cache/generated_api.py`
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
- 5 models: Pokemon, Trainer, Attack, Element, FightResult
- 7 operations: pokemon.management.*, pokemon.battles.*, pokemon.evolution.*

#### Check API is Running
```bash
curl http://localhost:8000/docs
```

Should show OpenAPI documentation with all endpoints.

#### Create a Pokemon (CRUD - Automatic)
```bash
curl -X POST http://localhost:8000/pokemon \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pikachu",
    "hp": 35,
    "attack": 55,
    "defense": 40,
    "sp_attack": 50,
    "sp_defense": 50,
    "speed": 90,
    "element": "Electric",
    "attacks": ["Thunderbolt", "Quick Attack"]
  }'
```

#### List Pokemon
```bash
curl http://localhost:8000/pokemon
```

#### Execute a Workflow Operation
```bash
curl -X POST http://localhost:8000/operations/pokemon/management/catch \
  -H "Content-Type: application/json" \
  -d '{
    "trainer_name": "Ash",
    "pokemon_name": "Pikachu",
    "element": "Electric"
  }'
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
pokemon-app/
├── main                    # Executable entrypoint (imports models + operations)
├── QUICKSTART.md          # This file
├── README.md              # Comprehensive documentation
├── models/
│   ├── pokemon.py         # Pokemon model with stats
│   ├── trainer.py         # Trainer model
│   ├── attack.py          # Attack/Move model
│   ├── element.py         # Element/Type model
│   └── fight_result.py    # Battle result model
└── operations/
    ├── pokemon_management.py  # Catch, train, create trainer
    ├── pokemon_battles.py     # Pokemon vs Pokemon, Trainer vs Trainer
    └── pokemon_evolution.py   # Evolution stages
```

## How It Works

1. **`main` file** imports all models and operations
   - When imported, decorators (`@datamodel`, `@operation`) register metadata
   - Registries now populated with models and operations

2. **`./main compile`** runs code generators
   - Reads from registries (populated by imports in step 1)
   - Generates FastAPI routes, React UI config, Prefect workflows

3. **`./main up`** starts all services
   - MongoDB listens on localhost:27017
   - FastAPI listens on 0.0.0.0:8000
   - React listens on localhost:3000
   - Prefect listens on localhost:4200

4. **CRUD endpoints** auto-generated
   - GET/POST/PUT/DELETE on `/pokemon`, `/trainer`, etc.
   - No explicit operations needed - Beanie + FastAPI handle it

5. **Workflow operations** are custom
   - Defined as `@operation` decorators in `operations/`
   - Available via `/operations/pokemon/management/*, /pokemon/battles/*, /pokemon/evolution/*`

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

If no models listed, check that `main` file imports all models.

## Next Steps

1. **Explore the code**: Check `models/` and `operations/` to understand structure
2. **Run operations**: Use the CLI or API to execute workflow operations
3. **Customize**: Add new models or operations following the same pattern
4. **Integrate**: Connect to external services using operation functions

---

**Questions?** Check README.md for comprehensive documentation.
