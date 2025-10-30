# E-commerce Order Management System

Complex e-commerce example demonstrating Pulpo Core's capabilities for parallel processing, sequential workflows, and system integration.

## Overview

This example shows how to build an order management system with:
- Multiple related models (Product, Order, Customer, Payment)
- Parallel checkout validations
- Sequential fulfillment pipeline
- Payment processing in parallel with fulfillment
- Cross-system coordination

## Project Structure

```
ecommerce-app/
├── models/
│   ├── product.py      # Product catalog
│   ├── customer.py     # Customer accounts
│   ├── order.py        # Order and order items
│   └── payment.py      # Payment records
└── operations/
    ├── checkout.py     # Parallel validations
    ├── fulfillment.py  # Sequential fulfillment
    ├── tracking.py     # Post-fulfillment
    └── payments.py     # Payment processing
```

## Data Models

### Product
```python
sku: str              # Unique product ID
name: str            # Product name
price: float         # Price in USD
inventory: int       # Current stock
```

### Customer
```python
email: str           # Email address
name: str           # Full name
addresses: list[Address]  # Shipping/billing addresses
```

### Address (nested in Customer)
```python
street: str         # Street address
city: str          # City
state: str         # State/Province
zip_code: str      # Postal code
```

### Order
```python
order_number: str          # Unique order ID
customer_id: str          # Customer
items: list[OrderItem]    # Products ordered
status: OrderStatus       # pending|processing|shipped|delivered|cancelled
total: float             # Order total amount
shipping_address_id: str # Shipping address
tracking_number: str     # Shipping tracking
```

### OrderItem (nested in Order)
```python
product_id: str    # Product ID
quantity: int      # How many
unit_price: float  # Price per unit
total_price: float # Total for this item
```

### Payment
```python
order_id: str          # Related order
amount: float         # Payment amount
status: PaymentStatus # pending|processing|completed|failed|refunded
transaction_id: str   # Payment processor ID
```

## Operations

### Checkout Phase (Parallel Execution)

All three checkout operations can run simultaneously since they have no dependencies:

```
┌─ orders.checkout.validate_items ──┐
├─ orders.checkout.validate_payment ├──→ (fulfillment starts)
├─ orders.checkout.calculate_shipping
└─────────────────────────────────────┘
```

**Operations:**
- `orders.checkout.validate_items` - Verify inventory
- `orders.checkout.validate_payment` - Validate payment method
- `orders.checkout.calculate_shipping` - Calculate shipping cost

**Benefit:** All validations happen concurrently instead of sequentially.

```bash
# These can run in parallel
pulpo orders checkout validate_items --input '{"order_id": "ORD-123", "items": [...]}'
pulpo orders checkout validate_payment --input '{"order_id": "ORD-123", "payment_method": "credit_card"}'
pulpo orders checkout calculate_shipping --input '{"order_id": "ORD-123", "address_zip": "90210"}'
```

### Fulfillment Phase (Sequential Pipeline)

Fulfillment operations must run in order since each depends on the previous:

```
orders.fulfillment.reserve_items
        ↓
orders.fulfillment.pick_items
        ↓
orders.fulfillment.pack_items
        ↓
orders.fulfillment.ship_items
        ↓
orders.tracking.update_customer
```

**Operations:**
- `orders.fulfillment.reserve_items` - Hold inventory
- `orders.fulfillment.pick_items` - Get from warehouse
- `orders.fulfillment.pack_items` - Prepare for shipping
- `orders.fulfillment.ship_items` - Hand off to carrier
- `orders.tracking.update_customer` - Notify customer

### Payment Phase (Parallel to Fulfillment)

Payment processing happens concurrently with fulfillment:

```
payments.processing.charge
        ↓
payments.processing.confirm
        ↓
payments.reconciliation.verify
```

**Operations:**
- `payments.processing.charge` - Charge payment method
- `payments.processing.confirm` - Confirm charge settled
- `payments.reconciliation.verify` - Verify in accounting

## Operation Hierarchy Graph (OHG)

Shows the complete flow with parallelization:

```
orders (domain)
├── checkout (can parallelize)
│   ├── validate_items      ──┐
│   ├── validate_payment     ├──→ fulfillment starts
│   └── calculate_shipping   ──┘
├── fulfillment (sequential)
│   ├── reserve_items
│   ├── pick_items
│   ├── pack_items
│   ├── ship_items
│   └── tracking (post-ship)
│       └── update_customer

payments (domain, parallel to fulfillment)
└── processing (sequential)
    ├── charge       ──→ confirm ──→ verify
    └── reconciliation
        └── verify
```

## Execution Flow

### Traditional (Sequential)
```
Total Time: validate_items + validate_payment + calculate_shipping
          + reserve + pick + pack + ship + charge + confirm + verify
         ≈ 10 seconds if each operation takes 1 second
```

### With Parallelization
```
Parallel checkout:    validate_items, validate_payment, calculate_shipping
                     (3 operations simultaneously) ≈ 1 second

Sequential fulfillment: reserve → pick → pack → ship → update
                       (5 operations sequentially) ≈ 5 seconds

Parallel payments:     charge → confirm → verify
                       (3 operations, with confirm waiting for charge)
                       (can happen during fulfillment) ≈ 3 seconds

Total Time: max(checkout) + max(fulfillment, payments)
          ≈ 1 + 5 = 6 seconds instead of 10 seconds
          (40% time savings!)
```

## Generated Artifacts

Running `pulpo compile` generates:

### API Endpoints (CRUD for models)
```
GET    /products              # List products
POST   /products              # Create product
GET    /products/{id}         # Get product
PUT    /products/{id}         # Update product
DELETE /products/{id}         # Delete product

# Similar for customers, orders, payments

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

### CLI Commands
```
pulpo orders checkout validate_items
pulpo orders checkout validate_payment
pulpo orders checkout calculate_shipping
pulpo orders fulfillment reserve_items
pulpo orders fulfillment pick_items
pulpo orders fulfillment pack_items
pulpo orders fulfillment ship_items
pulpo orders tracking update_customer
pulpo payments processing charge
pulpo payments processing confirm
pulpo payments reconciliation verify
```

### Prefect Workflows
Generated async Prefect flows that use `asyncio.gather()` for parallel operations:

```python
@flow(name="orders")
async def orders_flow(order_data: dict):
    # Parallel checkout validations
    validate_results = await asyncio.gather(
        validate_items(order_data),
        validate_payment(order_data),
        calculate_shipping(order_data)
    )

    # Sequential fulfillment
    await reserve_items(order_data)
    await pick_items(order_data)
    await pack_items(order_data)
    await ship_items(order_data)
    await update_customer(order_data)

    return validate_results
```

## Running the Example

### 1. Extract
```bash
tar -xzf ecommerce-app.tar.gz
cd ecommerce-app
```

### 2. Install Pulpo
```bash
pip install pulpo-core
```

### 3. Initialize
```bash
pulpo cli init
```

Creates configuration files and Makefile.

### 4. Compile
```bash
pulpo compile
```

Generates all artifacts (API, CLI, UI, Prefect flows).

### 5. Start Services
```bash
pulpo up
```

Starts MongoDB, FastAPI, React UI, Prefect.

### 6. Use the API

Create an order:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-20251030-001",
    "customer_id": "cust_123",
    "items": [{
      "product_id": "prod_456",
      "quantity": 2,
      "unit_price": 19.99
    }],
    "total": 39.98,
    "shipping_address_id": "addr_789"
  }'
```

Run checkout operations (in parallel):
```bash
# These can execute simultaneously
pulpo orders checkout validate_items --input '{"order_id": "ORD-20251030-001", ...}'
pulpo orders checkout validate_payment --input '{"order_id": "ORD-20251030-001", ...}'
pulpo orders checkout calculate_shipping --input '{"order_id": "ORD-20251030-001", ...}'
```

Run fulfillment (sequential):
```bash
pulpo orders fulfillment reserve_items --input '{"order_id": "ORD-20251030-001"}'
# After completion:
pulpo orders fulfillment pick_items --input '{"order_id": "ORD-20251030-001"}'
# Continue through the pipeline...
```

### 7. Monitor in UI
Open http://localhost:3000 to see orders, customers, and real-time operation execution.

### 8. Stop Services
```bash
pulpo down
```

## Key Architectural Concepts

### 1. Parallelization for Performance
Checkout validations don't depend on each other, so they run in parallel using `asyncio.gather()`:
```python
results = await asyncio.gather(validate_items(), validate_payment(), calculate_shipping())
```

### 2. Sequential Dependencies
Fulfillment steps depend on previous steps and must run sequentially:
```python
await reserve_items()
await pick_items()
await pack_items()
await ship_items()
```

### 3. Independent Pipelines
Payments can process simultaneously with fulfillment (different domains):
```python
# In same flow but independent branches
payment_task = asyncio.create_task(payment_workflow())
fulfill_task = asyncio.create_task(fulfillment_workflow())
await asyncio.gather(payment_task, fulfill_task)
```

### 4. Model Relationships
Models reference each other appropriately:
- Order → Customer (owner)
- Order → Products (items)
- Payment → Order (transaction for)
- Address → Customer (belongs to)

### 5. Async Operations
All operations are async, enabling true parallelization:
```python
@operation(name="orders.checkout.validate_items", ...)
async def validate_items(...) -> ValidateItemsOutput:
    # Can await external APIs, database calls, etc.
    return result
```

## Extension Ideas

### Add Authentication
- User login/registration
- Permission checks (can only see own orders)

### Add Inventory Management
- Webhook when stock runs low
- Automatic reordering

### Add Notifications
- Email on order status changes
- SMS tracking updates

### Add Returns/Refunds
- Create return workflow
- Process refunds
- Update inventory

### Add Analytics
- Track order metrics
- Analyze fulfillment performance
- Payment success rates

## Testing

Run Phase 3 tests:
```bash
python -m pytest tests/phase3/test_real_example.py -v
```

Tests verify:
- E-commerce models are discoverable
- Operations generate correctly
- Parallel checkout works
- Sequential fulfillment works
- Generated code is valid

## Performance Metrics

With this example, you can measure:
- Parallel checkout time (should be ~1/3 of sequential)
- Fulfillment pipeline throughput
- End-to-end order processing time
- Concurrent order capacity

---

**Pulpo Core v0.6.0** - Framework for building full-stack applications with metadata-driven code generation
