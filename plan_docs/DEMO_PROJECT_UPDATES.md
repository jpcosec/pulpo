# Demo Project Updates Plan

**Date:** 2025-10-30
**Status:** Planning Phase
**Scope:** Update existing Pokemon demo + create 2 new domain-agnostic examples
**Estimated Duration:** 8-12 hours

---

## Current State Analysis

### Existing Pokemon Demo (`core/demo-project.tar.gz`)

**Current Structure:**
```
test-project-demo/
├── models/
│   ├── pokemon.py (domain-specific)
│   ├── attack.py
│   ├── element.py
│   ├── trainer.py
│   └── fight_result.py
└── operations/
    ├── pokemon_management.py (flat naming: catch_pokemon, train_pokemon)
    ├── pokemon_battles.py
    └── pokemon_evolution.py
```

**Current Metadata Convention (OUTDATED):**
```python
@datamodel(
    name="Pokemon",
    description="...",
    tags=["pokemon", "creature"]
)

@operation(
    name="catch_pokemon",           # ❌ FLAT - should be hierarchical
    category="management",
    description="...",
    inputs=CatchPokemonInput,
    outputs=CatchPokemonOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
```

**Issues:**
- ❌ Flat operation naming (no hierarchy)
- ❌ Domain-specific names (Pokemon, Trainer, Attack)
- ❌ Doesn't demonstrate Operation Hierarchy Graph (OHG) concept
- ❌ Missing category-based organization
- ✅ Good example of @datamodel and @operation decorators
- ✅ Good I/O model patterns

---

## Target Convention (NEW)

### Hierarchical Operation Naming

Operations should use dot-separated naming to show containment and execution flow:

```
DOMAIN.CATEGORY.OPERATION
pokemon.management.catch        # Can be parallelized
pokemon.management.train        # Can be parallelized
pokemon.orchestration.evolve    # Depends on train
pokemon.battles.execute         # Depends on both teams ready
```

### Updated @operation Decorator

```python
@operation(
    name="pokemon.management.catch",      # ✅ Hierarchical
    description="Trainer catches a Pokemon",
    inputs=CatchPokemonInput,
    outputs=CatchPokemonOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
    """Trainer catches a new Pokemon."""
    ...
```

### Generated CLI Structure

Old (flat):
```bash
pulpo ops catch-pokemon --input '{...}'
```

New (hierarchical):
```bash
pulpo pokemon management catch --input '{...}'
pulpo pokemon orchestration evolve --input '{...}'
pulpo pokemon battles execute --input '{...}'
```

---

## Update Plan: Pokemon Demo

### Phase 1: Operation Hierarchy Refactoring

**File:** `test-project-demo/operations/pokemon_management.py`

Changes:
1. Rename operations to use `pokemon.management.*`:
   - `catch_pokemon` → `pokemon.management.catch`
   - `train_pokemon` → `pokemon.management.train`
   - `create_trainer` → `pokemon.management.create_trainer`

2. Update @operation decorators:
   ```python
   @operation(
       name="pokemon.management.catch",
       description="Trainer catches a Pokemon",
       inputs=CatchPokemonInput,
       outputs=CatchPokemonOutput,
       models_in=["Trainer"],
       models_out=["Pokemon"]
   )
   async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
   ```

**File:** `test-project-demo/operations/pokemon_battles.py`

Changes:
1. Operations: `start_battle` → `pokemon.battles.start`
2. Add sequential operations:
   - `pokemon.battles.start` (no dependencies)
   - `pokemon.battles.execute` (depends on start)
   - `pokemon.battles.finish` (depends on execute)

**File:** `test-project-demo/operations/pokemon_evolution.py`

Changes:
1. `evolve_pokemon` → `pokemon.evolution.evolve`
2. Add workflow:
   - `pokemon.evolution.check_ready` (can parallelize with training)
   - `pokemon.evolution.evolve` (depends on check_ready)

### Phase 2: Model Updates (Optional, Domain-Specific OK for Demo)

Keep Pokemon/Trainer models but add comments explaining they're domain-specific examples.

---

## New Example Projects

### Example 1: Todo List Application

**Purpose:** Simple, familiar domain showing CRUD + sequential operations

**Structure:**
```
todo-app/
├── models/
│   ├── todo.py        # Task with title, description, status
│   └── user.py        # User with created_at, updated_at
└── operations/
    ├── tasks.py       # CRUD operations on todos
    └── workflow.py    # Sequential task operations
```

**Models:**
```python
@datamodel(name="Todo", tags=["tasks"])
class Todo(Document):
    title: str
    description: str
    status: str  # "pending", "in_progress", "completed"
    created_by: str
    created_at: datetime
    updated_at: datetime

@datamodel(name="User", tags=["users"])
class User(Document):
    username: str
    email: str
    created_at: datetime
```

**Operations (Hierarchical):**
```
todos.crud.create          # Create new todo
todos.crud.read            # Get todo by ID
todos.crud.update          # Update todo
todos.crud.delete          # Delete todo
todos.workflow.start       # Start work on todo (change status)
todos.workflow.complete    # Complete todo
todos.workflow.reopen      # Reopen completed todo
todos.sync.archive         # Archive completed todos
```

**Timeline:** 4-5 hours

---

### Example 2: E-commerce System

**Purpose:** Complex domain with relationships, showing parallelization

**Structure:**
```
ecommerce-app/
├── models/
│   ├── product.py      # Products with inventory
│   ├── order.py        # Orders with items
│   ├── customer.py     # Customers with addresses
│   └── payment.py      # Payment records
└── operations/
    ├── orders.py       # Order management
    ├── fulfillment.py  # Order fulfillment
    └── payments.py     # Payment processing
```

**Models:**
```python
@datamodel(name="Product", tags=["catalog"])
class Product(Document):
    sku: str
    name: str
    price: float
    inventory: int

@datamodel(name="Order", tags=["orders"])
class Order(Document):
    order_number: str
    customer_id: str
    items: list[OrderItem]  # (product_id, quantity)
    status: str

@datamodel(name="Customer", tags=["customers"])
class Customer(Document):
    email: str
    name: str
    addresses: list[Address]

@datamodel(name="Payment", tags=["payments"])
class Payment(Document):
    order_id: str
    amount: float
    status: str  # "pending", "completed", "failed"
```

**Operations (Hierarchical, showing parallelization):**
```
orders.checkout.validate_items      # Parallel: check inventory
orders.checkout.validate_payment    # Parallel: validate payment method
orders.checkout.calculate_shipping  # Parallel: get shipping cost
orders.fulfillment.reserve_items    # Depends on all checkout validations
orders.fulfillment.pick_items       # Depends on reserve
orders.fulfillment.pack_items       # Depends on pick
orders.fulfillment.ship_items       # Depends on pack
orders.tracking.update_customer     # Depends on ship
payments.processing.charge          # Parallel to fulfillment
payments.processing.confirm         # Depends on charge
payments.reconciliation.verify      # Depends on confirm
```

**Parallelization Example:**
```
In OHG:
├─ orders.checkout.validate_items ──┐
├─ orders.checkout.validate_payment ├──→ orders.fulfillment.reserve_items
├─ orders.checkout.calculate_shipping──┘

(All three run in parallel, then reserve_items runs)
```

**Timeline:** 5-6 hours

---

## Implementation Approach

### Step 1: Update Pokemon Demo (In-Place)
1. Rename operations in code
2. Update @operation decorators
3. Update docstrings
4. Create new tarball: `core/demo-project.tar.gz`

### Step 2: Create Todo List Example
1. Create `examples/todo-app/` directory
2. Implement models and operations
3. Create README with features
4. Create tarball: `examples/todo-app.tar.gz`

### Step 3: Create E-commerce Example
1. Create `examples/ecommerce-app/` directory
2. Implement models and operations
3. Create README with architecture explanation
4. Create tarball: `examples/ecommerce-app.tar.gz`

### Step 4: Documentation
1. Update docs/README.md to reference examples
2. Create docs/EXAMPLES.md with:
   - Feature comparison
   - When to use each example
   - How to extract and run
3. Create plan_docs/EXAMPLE_PROJECTS.md with detailed architecture

---

## Documentation Updates

### Files to Update

**docs/EXAMPLES.md** (NEW)
- Overview of all example projects
- Quick start guide
- Comparison table
- Architecture diagrams

**docs/ARCHITECTURE_OVERVIEW.md**
- Add section: "Example Project Architectures"
- Reference to hierarchical operation naming

**CLAUDE.md**
- Update operation naming examples
- Use new `domain.category.operation` format
- Show Pokemon example with new convention

**README.md**
- Add "Example Projects" section
- Links to example projects with descriptions

---

## Success Criteria

### Pokemon Demo ✅
- [ ] All operations use `pokemon.*.*` naming
- [ ] Operations organized into logical categories
- [ ] CLI generates hierarchical commands
- [ ] Demonstrates parallelization (battles)
- [ ] Tarball extracts and initializes correctly

### Todo List Example ✅
- [ ] Simple, familiar domain
- [ ] Models: Todo, User
- [ ] Operations: CRUD + sequential workflow
- [ ] Shows status transition workflow
- [ ] Complete documentation
- [ ] Tarball works with `pulpo compile`

### E-commerce Example ✅
- [ ] Complex domain with relationships
- [ ] Models: Product, Order, Customer, Payment
- [ ] Demonstrates parallelization (checkout validations)
- [ ] Shows dependencies (fulfillment → tracking)
- [ ] Complete architecture documentation
- [ ] Tarball works with `pulpo compile`

### Documentation ✅
- [ ] All examples linked in main README
- [ ] Each example has own README
- [ ] Comparison table available
- [ ] Architecture diagrams provided
- [ ] CLAUDE.md uses new operation naming

---

## Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Update Pokemon demo | 2-3 hours | Not started |
| 2 | Create Todo example | 4-5 hours | Not started |
| 3 | Create E-commerce example | 5-6 hours | Not started |
| 4 | Update documentation | 2-3 hours | Not started |
| **TOTAL** | **All example projects** | **13-17 hours** | **Planned** |

---

## Integration with Phase 3 Testing

Once examples are complete, they become test fixtures for:
- **Iteration 3:** Artifact generation (test each example)
- **Iteration 4:** Generated code execution (run each example)
- **Iteration 10:** Real example integration (end-to-end tests)

The examples serve as reference implementations for:
- Proper @datamodel/@operation usage
- Hierarchical operation naming
- Parallelization patterns
- Error handling patterns
- Documentation practices

---

## Notes

1. **Keep Pokemon Domain-Specific:** It's an example, demonstrating a specific domain with well-known concepts
2. **Make Others Domain-Agnostic:** Todo and E-commerce are generic enough for users to relate
3. **Show OHG Concepts:** Each example should clearly show containment and execution flow
4. **Focus on Patterns:** Document the WHY behind architectural choices

---
