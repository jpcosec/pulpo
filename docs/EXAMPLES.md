# Example Projects

Pulpo Core includes complete, production-quality example projects demonstrating best practices and common patterns. Each example is a self-contained application that can be extracted and used as a template.

## Quick Start

### Extract an example:
```bash
cd examples/
tar -xzf todo-app.tar.gz
cd todo-app
```

### Run an example:
```bash
# Install Pulpo
pip install -e ../../core

# Initialize
pulpo cli init

# Compile
pulpo compile

# Start services
pulpo up

# Use the API
curl -X POST http://localhost:8000/todos/crud/create ...
```

## Example 1: Todo List Application

**Location:** `examples/todo-app/`
**Tarball:** `examples/todo-app.tar.gz` (4.9K)

### Overview

A simple todo list management system demonstrating:
- **Basic CRUD operations** - Create, read, update, delete todos
- **Workflow operations** - Status transitions (start, complete, reopen)
- **Parallel execution** - CRUD operations can run independently
- **Data persistence** - Beanie/MongoDB integration
- **Type-safe I/O** - Pydantic input/output validation

### Data Models

**User Model**
```python
@datamodel(name="User", ...)
class User(Document):
    username: str              # Unique username
    email: str                 # Email address
    created_at: datetime       # Account creation time
    updated_at: datetime       # Last update time
```

**Todo Model**
```python
@datamodel(name="Todo", ...)
class Todo(Document):
    title: str                 # Task title
    description: str           # Detailed description
    status: TodoStatus         # pending | in_progress | completed
    created_by: str            # Creator username
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last update timestamp
```

### Operations (8 Total)

#### CRUD Operations (Parallel)
- `todos.crud.create` - Create new todo
- `todos.crud.read` - Get todo by ID
- `todos.crud.update` - Update todo fields
- `todos.crud.delete` - Delete todo permanently

**Key characteristic:** Can execute in parallel - no dependencies between them

#### Workflow Operations (Sequential)
- `todos.workflow.start` - Mark pending → in_progress
- `todos.workflow.complete` - Mark in_progress → completed
- `todos.workflow.reopen` - Mark completed → pending

#### Maintenance Operations
- `todos.sync.archive` - Archive completed todos

### Operation Hierarchy Graph (OHG)

```
todos (domain)
├── crud (parallelizable)
│   ├── create      ──┐
│   ├── read         ├──→ (can run simultaneously)
│   ├── update       ├──→
│   └── delete      ──┘
├── workflow (sequential)
│   ├── start  → complete  → reopen
└── sync (maintenance)
    └── archive
```

### Generated Artifacts

**API Endpoints:**
```
POST   /operations/todos/crud/create
GET    /operations/todos/crud/read
PUT    /operations/todos/crud/update
DELETE /operations/todos/crud/delete
POST   /operations/todos/workflow/start
POST   /operations/todos/workflow/complete
POST   /operations/todos/workflow/reopen
POST   /operations/todos/sync/archive
```

**CLI Commands:**
```bash
pulpo todos crud create --input '{...}'
pulpo todos crud read --input '{...}'
pulpo todos workflow start --input '{...}'
```

### Learning Objectives

This example teaches:
1. ✅ How to structure models with `@datamodel`
2. ✅ How to implement operations with `@operation`
3. ✅ Hierarchical operation naming (`domain.category.operation`)
4. ✅ Input/output validation with Pydantic
5. ✅ Async operation implementation
6. ✅ Simple workflow state transitions

### Use Cases

- Learning Pulpo Core basics
- Template for simple CRUD applications
- Reference for user management patterns
- Introduction to operation hierarchies

---

## Example 2: E-commerce Order Management System

**Location:** `examples/ecommerce-app/`
**Tarball:** `examples/ecommerce-app.tar.gz` (7.4K)

### Overview

A complex e-commerce system demonstrating enterprise patterns:
- **Parallelization** - Checkout validations run concurrently
- **Sequential pipelines** - Fulfillment steps with strict ordering
- **Independent domains** - Payment processing parallel to fulfillment
- **Model relationships** - Nested models and references
- **Complex workflows** - Multi-stage order processing

### Data Models (4 Total)

**Product Model**
```python
@datamodel(name="Product", ...)
class Product(Document):
    sku: str                   # Stock-keeping unit (unique ID)
    name: str                  # Product name
    description: str           # Product details
    price: float               # Price in USD
    inventory: int             # Current stock
    category: str              # Product category
```

**Customer Model**
```python
class Address(BaseModel):
    street: str               # Street address
    city: str                 # City
    state: str                # State/Province
    zip_code: str             # Postal code
    country: str = "US"       # Country

@datamodel(name="Customer", ...)
class Customer(Document):
    email: str                # Email address
    name: str                 # Full name
    phone: Optional[str]      # Phone number
    addresses: list[Address]  # Shipping/billing addresses (nested)
    created_at: datetime
    updated_at: datetime
```

**Order Model**
```python
class OrderItem(BaseModel):
    product_id: str           # Reference to Product
    product_name: str         # Product name (denormalized)
    quantity: int             # How many
    unit_price: float         # Price per unit
    total_price: float        # Line total

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@datamodel(name="Order", ...)
class Order(Document):
    order_number: str         # Unique order ID
    customer_id: str          # Reference to Customer
    items: list[OrderItem]    # Ordered items (nested)
    status: OrderStatus       # Current order status
    subtotal: float           # Pre-tax total
    shipping_cost: float      # Shipping fees
    tax: float                # Sales tax
    total: float              # Final amount
    shipping_address_id: str  # Selected address
    payment_method: str       # Payment type
    tracking_number: str      # Shipping tracking
    created_at: datetime
    shipped_at: datetime
    delivered_at: datetime
```

**Payment Model**
```python
class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@datamodel(name="Payment", ...)
class Payment(Document):
    order_id: str             # Reference to Order
    amount: float             # Payment amount
    status: PaymentStatus     # Current status
    transaction_id: str       # Payment processor ID
    error_message: str        # Error if failed
    created_at: datetime
    updated_at: datetime
```

### Operations (12 Total)

#### Checkout Phase (Parallel)
Three operations that can execute simultaneously since they have no dependencies:

- `orders.checkout.validate_items` - Verify inventory available
- `orders.checkout.validate_payment` - Validate payment method
- `orders.checkout.calculate_shipping` - Calculate shipping cost

**Key pattern:**
```
┌─ validate_items ──┐
├─ validate_payment ├──→ (fulfillment starts)
└─ calculate_shipping
```

#### Fulfillment Phase (Sequential)
Five operations that must execute in strict order:

- `orders.fulfillment.reserve_items` - Hold inventory
- `orders.fulfillment.pick_items` - Retrieve from warehouse
- `orders.fulfillment.pack_items` - Prepare for shipment
- `orders.fulfillment.ship_items` - Hand off to carrier

**Key pattern:**
```
reserve_items → pick_items → pack_items → ship_items
```

#### Tracking Phase
- `orders.tracking.update_customer` - Notify customer of shipment

#### Payment Phase (Parallel to Fulfillment)
Three operations in sequential order but running parallel to fulfillment:

- `payments.processing.charge` - Charge payment method
- `payments.processing.confirm` - Confirm charge settled
- `payments.reconciliation.verify` - Verify in accounting

**Key pattern:**
```
charge → confirm → verify    (runs parallel to fulfillment)
```

### Operation Hierarchy Graph (OHG)

```
orders (domain)
├── checkout (parallelizable)
│   ├── validate_items      ──┐
│   ├── validate_payment     ├──→ fulfillment starts
│   └── calculate_shipping   ──┘
│
├── fulfillment (sequential pipeline)
│   ├── reserve_items
│   ├── pick_items
│   ├── pack_items
│   ├── ship_items
│   └── tracking
│       └── update_customer
│
payments (domain, parallel to fulfillment)
└── processing (sequential)
    ├── charge
    └── confirm
        └── verify
```

### Generated Artifacts

**API Endpoints:** 12 operation endpoints + CRUD for 4 models (16 total)

```
# Order CRUD
POST   /orders              # Create
GET    /orders              # List
GET    /orders/{id}         # Get
PUT    /orders/{id}         # Update
DELETE /orders/{id}         # Delete

# Operation endpoints
POST   /operations/orders/checkout/validate_items
POST   /operations/orders/checkout/validate_payment
POST   /operations/orders/checkout/calculate_shipping
POST   /operations/orders/fulfillment/reserve_items
POST   /operations/orders/fulfillment/pick_items
POST   /operations/orders/fulfillment/pack_items
POST   /operations/orders/fulfillment/ship_items
POST   /operations/orders/tracking/update_customer
POST   /operations/payments/processing/charge
POST   /operations/payments/processing/confirm
POST   /operations/payments/reconciliation/verify
```

### Execution Flow Analysis

**Traditional Sequential Approach:**
```
Total Time: validate + reserve + pick + pack + ship + charge + confirm + verify
          ≈ 10 seconds (if each takes 1 second)
```

**With Parallelization:**
```
Parallel checkout:     1 second (3 operations simultaneously)
Sequential fulfill:    5 seconds (reserve→pick→pack→ship→update)
Parallel payments:     3 seconds (charge→confirm→verify, overlaps with fulfill)

Total Time: max(1) + max(5, 3) = 6 seconds
Result: 40% faster! (6s vs 10s)
```

### Prefect Workflow Example

```python
@flow(name="orders")
async def orders_flow(order_data: dict):
    # Parallel checkout validations
    validate_results = await asyncio.gather(
        validate_items(order_data),
        validate_payment(order_data),
        calculate_shipping(order_data)
    )

    # Start payment processing in parallel
    payment_task = asyncio.create_task(payment_workflow(order_data))

    # Sequential fulfillment
    await reserve_items(order_data)
    await pick_items(order_data)
    await pack_items(order_data)
    await ship_items(order_data)
    await update_customer(order_data)

    # Wait for payment to complete
    payment_result = await payment_task

    return {"validate_results": validate_results, "payment": payment_result}
```

### Learning Objectives

This example teaches:
1. ✅ Complex model relationships (nested models, references)
2. ✅ Parallelization patterns (independent operations)
3. ✅ Sequential pipelines (dependent operations)
4. ✅ Multi-domain coordination (orders + payments)
5. ✅ Enterprise workflow patterns
6. ✅ Performance optimization through parallelization
7. ✅ Prefect flow generation from operation hierarchy

### Use Cases

- Learning advanced Pulpo patterns
- Template for e-commerce applications
- Reference for parallel/sequential orchestration
- Example of multi-domain coordination
- Teaching parallelization benefits
- Performance optimization demonstration

---

## Example 3: Pokemon Battle Simulation

**Location:** `examples/pokemon-app/`
**Tarball:** `examples/pokemon-app.tar.gz` (5.5K)

### Overview

A classic Pokemon trainer battle system demonstrating domain-specific modeling:
- **Pokemon management** - Catch and train Pokemon
- **Battle system** - Execute trainer vs trainer battles
- **Evolution mechanics** - Multi-stage Pokemon evolution
- **Hierarchical operations** - Domain-organized operation structure
- **Parallel + sequential** - Parallel battles with sequential evolution

### Data Models (5 Total)

**Pokemon Model**
```python
@datamodel(name="Pokemon", ...)
class Pokemon(Document):
    name: str                  # Pokemon species name
    element: str               # Fire, Water, Grass, etc.
    level: int                 # Current level (1-100)
    experience: int            # Experience points
    stats: dict                # Attack, defense, speed, etc.
    evolution_stage: int       # Stage 1, 2, or 3
```

**Trainer Model**
```python
@datamodel(name="Trainer", ...)
class Trainer(Document):
    name: str                  # Trainer name
    pokemon_team: list[str]    # IDs of caught Pokemon
    badges: int                # Gym badges earned
    wins: int                  # Battle wins
    losses: int                # Battle losses
```

**Attack, Element, and FightResult Models**
- Attack: Damage calculations and move sets
- Element: Type matchups (fire > grass > water > fire)
- FightResult: Battle outcome tracking

### Operations (7 Total)

#### Management Operations (Parallel)
- `pokemon.management.catch` - Trainer catches a Pokemon
- `pokemon.management.train` - Increase Pokemon stats
- `pokemon.management.trainer_create` - Create new trainer

#### Battle Operations (Sequential + Parallel)
- `pokemon.battles.execute` - One-on-one Pokemon battle
- `pokemon.battles.trainer_execute` - Full trainer battles (use parallel execute)

#### Evolution Operations (Dependent)
- `pokemon.evolution.stage1` → `pokemon.evolution.stage2` - Progressive evolution

### Operation Hierarchy Graph (OHG)

```
pokemon (domain)
├── management (parallelizable)
│   ├── catch         ──┐
│   ├── train          ├──→ (can run simultaneously)
│   └── trainer_create ──┘
│
├── battles (orchestrated)
│   ├── execute (Pokemon vs Pokemon, parallelizable)
│   └── trainer_execute (uses execute operations)
│
└── evolution (sequential)
    ├── stage1 → stage2 (progressive evolution chain)
```

### Learning Objectives

This example teaches:
1. ✅ Domain-specific operation modeling
2. ✅ Hierarchical naming in a business domain
3. ✅ Mixing parallel and sequential operations
4. ✅ Operation composition (trainer battles use Pokemon battles)
5. ✅ Complex data relationships
6. ✅ Type-based game mechanics (element matchups)

### Use Cases

- Learning Pulpo Core with a game domain
- Reference for complex state management
- Example of operation composition
- Template for competitive games and simulations

---

## Comparison Table

| Aspect | Todo List | E-commerce | Pokemon |
|--------|-----------|-----------|---------|
| **Complexity** | Beginner | Advanced | Intermediate |
| **Models** | 2 | 4 | 5 |
| **Operations** | 8 | 12 | 7 |
| **Relationships** | Simple | Nested models, references | Complex data relationships |
| **Parallelization** | Basic (CRUD ops) | Advanced (checkout + payments) | Mixed (battles + evolution) |
| **Domains** | Single | Multiple (orders, payments) | Gaming domain |
| **Use Case** | Learning | Reference implementation | Game mechanics |
| **Tarball Size** | 4.9K | 7.4K | 5.5K |

---

## Testing Examples

Both examples include comprehensive tests:

```bash
# Run Phase 3 tests (example testing)
python -m pytest tests/phase3/test_real_example.py -v

# Run specific example tests
python -m pytest tests/phase3/test_real_example.py::test_todo_models_discoverable -v
python -m pytest tests/phase3/test_real_example.py::test_ecommerce_models_discoverable -v
```

Tests verify:
- Models are discoverable by the framework
- Operations generate correctly
- Hierarchical naming is preserved
- Generated code is valid Python
- Parallel/sequential patterns work as expected

---

## Extending the Examples

### Add to Todo List

- **Email notifications** - Notify when todos are assigned
- **Recurring todos** - Auto-create todos on a schedule
- **Subtasks** - Break todos into smaller items
- **Attachments** - Add files to todos
- **Collaboration** - Assign todos to other users

### Add to E-commerce

- **Inventory webhooks** - Alert when stock runs low
- **Returns/Refunds** - Create return workflow
- **Analytics** - Track sales metrics
- **Promotions** - Apply discounts and coupons
- **Notifications** - Email/SMS on order status
- **Fulfillment tracking** - Real-time warehouse updates

---

## File Structure

### Todo List
```
todo-app/
├── models/
│   ├── __init__.py
│   ├── user.py         # User account model
│   └── todo.py         # Todo item model
├── operations/
│   ├── __init__.py
│   ├── crud.py         # Create, read, update, delete (parallel)
│   ├── workflow.py     # Status transitions (sequential)
│   └── sync.py         # Archive and maintenance
└── README.md           # Comprehensive documentation
```

### E-commerce
```
ecommerce-app/
├── models/
│   ├── __init__.py
│   ├── product.py      # Product catalog
│   ├── customer.py     # Customer accounts with addresses
│   ├── order.py        # Orders with nested items
│   └── payment.py      # Payment processing
├── operations/
│   ├── __init__.py
│   ├── checkout.py     # Parallel validations
│   ├── fulfillment.py  # Sequential pipeline
│   ├── tracking.py     # Post-fulfillment
│   └── payments.py     # Payment processing
└── README.md           # Detailed enterprise patterns
```

### Pokemon
```
pokemon-app/
├── models/
│   ├── __init__.py
│   ├── pokemon.py      # Pokemon creature model
│   ├── trainer.py      # Trainer account model
│   ├── attack.py       # Attack/move model
│   ├── element.py      # Type matchup system
│   └── fight_result.py # Battle outcome tracking
├── operations/
│   ├── __init__.py
│   ├── pokemon_management.py  # Catch, train operations
│   ├── pokemon_battles.py      # Battle execution
│   └── pokemon_evolution.py    # Evolution mechanics
└── README.md           # Pokemon domain guide
```

---

## Running Tests

```bash
# Extract example
cd examples/
tar -xzf todo-app.tar.gz
cd todo-app

# Install dependencies
pip install -e ../../core
pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt"

# Run compilation
pulpo compile

# Verify generated code
python -m pytest . -v
```

---

## Next Steps

1. **Extract an example** to understand the structure
2. **Read the example README** for detailed documentation
3. **Explore the code** to see patterns in action
4. **Modify and extend** the example for your use case
5. **Generate and run** your own application

---

For more information on Pulpo Core concepts:
- **[Hierarchy & Orchestration](./ORCHESTRATION.md)** - Detailed OHG explanation
- **[Datamodel Decorator](./DATAMODEL_DECORATOR.md)** - Model registration
- **[Operation Decorator](./OPERATION_DECORATOR.md)** - Operation registration
- **[Architecture Overview](./ARCHITECTURE_OVERVIEW.md)** - System design
