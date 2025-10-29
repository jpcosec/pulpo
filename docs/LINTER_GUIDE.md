# DataModel Linter Guide

The DataModel Linter catches **orthographic and semantic errors** in your `@datamodel` and `@operation` decorators before they cause issues with code generation and architecture diagrams.

## What It Catches

### 1. **Type/Naming Mismatches** ❌ (Errors)

The linter detects when field names suggest a relationship but the type is wrong:

```python
# ❌ WRONG - linter error
class Pokemon(Document):
    attacks: list[str]  # Should be list[Attack]

# ✅ CORRECT
class Pokemon(Document):
    attacks: list[Attack]
```

**Why it matters:**
- Breaks relationship detection in architecture diagrams
- Creates data model inconsistencies
- Makes foreign keys invisible to the framework

### 2. **Missing Documentation** ⚠️ (Warnings)

Checks that models and fields have meaningful descriptions:

```python
# ❌ WRONG
@datamodel(
    name="Pokemon",
    description="Pokemon"  # Too short!
)
class Pokemon(Document):
    name: str  # No description!

# ✅ CORRECT
@datamodel(
    name="Pokemon",
    description="A Pokemon with stats, type, and attacks"
)
class Pokemon(Document):
    name: str = Field(..., description="Pokemon name")
```

### 3. **Orphaned Models** ℹ️ (Info)

Identifies models not used by any operation:

```python
@datamodel(...)
class Element(Document):
    pass

# If no operation has models_in=["Element"] or models_out=["Element"],
# you'll get an info notice
```

### 4. **Unknown Model References** ❌ (Errors)

Catches operations that reference non-existent models:

```python
@operation(
    models_in=["Pokemon"],
    models_out=["NonExistentModel"]  # ❌ Error!
)
async def my_op():
    pass
```

## Usage

### Command Line

```bash
# Run linter from framework directory
cd core/
make lint-models

# Run from any project (loads from .jobhunter.yml)
make lint-models
```

### Output Levels

```bash
# Show only errors (default)
make lint-models

# Show errors + warnings
python3 -m core.cli lint check --level warning

# Show everything including info notices
python3 -m core.cli lint check --level info

# Export as JSON
python3 -m core.cli lint check --format json
```

### In Python

```python
from core.linter import DataModelLinter

linter = DataModelLinter()
errors = linter.lint()

# Get text report
print(linter.report(format="text"))

# Get summary
print(linter.report(format="summary"))
```

## Common Issues and Fixes

### Issue: `list[str]` Instead of `list[Model]`

```python
# ❌ Before (linter error)
class Trainer(Document):
    pokemon_team: list[str] = Field(..., description="List of Pokemon names")

# ✅ After (linter passes)
from models.pokemon import Pokemon

class Trainer(Document):
    pokemon_team: list[Pokemon] = Field(..., description="List of Pokemon in team")
```

**Linter message:**
```
❌ [TYPE_MISMATCH] Trainer.pokemon_team: Field 'pokemon_team' uses list[str]
   but name suggests model reference
   💡 Suggestion: Change to: pokemon_team: list[Pokemon]
```

### Issue: Missing Field Descriptions

```python
# ❌ Before (linter warning)
class Pokemon(Document):
    health: int

# ✅ After (linter passes)
class Pokemon(Document):
    health: int = Field(..., description="Hit Points (HP)")
```

### Issue: Foreign Keys as Strings

```python
# ⚠️ Before (linter warning - still works but won't show in diagrams)
class FightResult(Document):
    pokemon1_id: str

# ✅ After (best practice)
from models.pokemon import Pokemon

class FightResult(Document):
    pokemon1: Pokemon  # Direct reference
```

## Linter Rules Summary

| Code | Level | Issue | Example |
|------|-------|-------|---------|
| `TYPE_MISMATCH` | ERROR | `list[str]` should be `list[Model]` | `attacks: list[str]` → `attacks: list[Attack]` |
| `FK_AS_STRING` | WARNING | Foreign key stored as string | `pokemon_id: str` → `pokemon: Pokemon` |
| `PLURAL_NOT_LIST` | WARNING | Plural name but not a list | `items: str` → `items: list[Item]` |
| `DOC_MISSING` | WARNING | Model lacks description | Add to `@datamodel` |
| `DOC_MISSING_FIELD` | WARNING | Field lacks description | Add `Field(..., description="...")` |
| `DOC_MISSING_OP` | WARNING | Operation lacks description | Add to `@operation` |
| `SPELLING` | INFO | Misspelling in description | Common typos like "pokemons" → "pokemon" |
| `ORPHANED_MODEL` | INFO | Model not used by operations | Either use it or remove it |
| `MODEL_NOT_FOUND` | ERROR | Operation references unknown model | Check model names |

## Integration with Workflow

### Pre-Commit Check

Add to your development workflow:

```bash
# Before compiling, lint your models
make lint-models

# Then compile if linting passes
make compile
```

### In CI/CD

```yaml
# Example GitHub Actions
- name: Lint Models
  run: make lint-models --level error  # Fail if errors found
```

## False Positive Handling

The linter intelligently ignores common fields that end in 's' but aren't collections:

- `status`, `address`, `class`
- `stats`, `gains`, `losses`, `wins`
- `turns`, `bytes`, `access`, `progress`
- `success`, `results`, `bounds`, `basis`
- `compass`, `focus`, `radius`, `lens`, `axis`

If you have a field falsely flagged, it will appear as a `PLURAL_NOT_LIST` warning. You can:

1. Rename the field to be clearer
2. Add to the exceptions list (submit a PR to the framework)
3. Ignore it with `--level error` (warnings won't fail)

## Next Steps

- **Fix errors immediately** - these break your architecture
- **Fix warnings gradually** - these improve consistency
- **Review info notices** - these help you understand your model graph

Run linter regularly as part of your development workflow!
