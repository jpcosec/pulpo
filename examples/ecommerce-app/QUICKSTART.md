# E-commerce Demo - Quick Start Guide

Get the E-commerce demo running in 5 minutes. This example demonstrates **advanced parallelization** and complex workflow orchestration.

## Prerequisites

- Python 3.11+
- Pulpo Core installed: `pip install pulpo-core`
- Docker (for MongoDB, optional - can use local MongoDB)

## Quick Start

### 1. Initialize Project
```bash
cd ecommerce-app
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
- Discovers all models (Product, Customer, Order, Payment) from `main` entrypoint
- Discovers all operations (checkout, fulfillment, payments, tracking) from `main` entrypoint
- Generates:
  - FastAPI routes in `.run_cache/generated_api.py`
  - React UI configuration in `.run_cache/generated_ui_config.ts`
  - Prefect workflows in `.run_cache/orchestration/` with **parallel execution**
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
cat .run_cache/registry.json | head -80
```

Should show:
- 4 models: Product, Customer, Order, Payment
- 12 operations across:
  - ecommerce.checkout.* - Start checkout, apply coupon
  - ecommerce.fulfillment.* - Process order, ship, handle returns
  - ecommerce.payments.* - Charge, refund, validate payment
  - ecommerce.tracking.* - Track order

#### Check API is Running
```bash
curl http://localhost:8000/docs
```

Should show OpenAPI documentation with all endpoints.

#### Create a Product (CRUD - Automatic)
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 1299.99,
    "stock": 50
  }'
```

Save the returned product ID.

#### Create a Customer (CRUD - Automatic)
```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "address": "123 Main St"
  }'
```

Save the returned customer ID.

#### Create an Order (CRUD - Automatic)
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "{customer_id}",
    "items": [
      {
        "product_id": "{product_id}",
        "quantity": 1,
        "price": 1299.99
      }
    ],
    "total_amount": 1299.99,
    "status": "pending"
  }'
```

Save the returned order ID.

#### List Orders
```bash
curl http://localhost:8000/orders
```

#### Execute Checkout Flow (Parallel Operations)
```bash
# Start checkout process
curl -X POST http://localhost:8000/operations/ecommerce/checkout/start \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "customer_id": "{customer_id}"
  }'

# Apply coupon (runs in parallel with payment processing)
curl -X POST http://localhost:8000/operations/ecommerce/checkout/apply_coupon \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "coupon_code": "SAVE10"
  }'
```

#### Execute Payment Operations
```bash
# Charge payment (runs parallel with fulfillment)
curl -X POST http://localhost:8000/operations/ecommerce/payments/charge \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "amount": 1299.99,
    "payment_method": "credit_card"
  }'

# Validate payment method
curl -X POST http://localhost:8000/operations/ecommerce/payments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "4111111111111111",
    "expiry": "12/25",
    "cvv": "123"
  }'
```

#### Execute Fulfillment Operations
```bash
# Process order for shipment (happens in parallel)
curl -X POST http://localhost:8000/operations/ecommerce/fulfillment/process \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}"
  }'

# Ship order
curl -X POST http://localhost:8000/operations/ecommerce/fulfillment/ship \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "tracking_number": "TRK123456"
  }'
```

#### Track Order
```bash
curl -X POST http://localhost:8000/operations/ecommerce/tracking/track \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}"
  }'
```

#### View UI
Open http://localhost:3000 in your browser

#### View Prefect Flows
Open http://localhost:4200 in your browser to see:
- Flow runs with parallel task execution
- Performance improvements from parallelization
- Real-time flow execution tracking

#### View Graphs
```bash
./main graph   # Model relationships
./main flows   # Operation hierarchy with parallelization
```

### 5. Stop Services
```bash
./main down
```

## Project Structure

```
ecommerce-app/
├── main                    # Executable entrypoint (imports models + operations)
├── QUICKSTART.md          # This file
├── README.md              # Comprehensive documentation
├── models/
│   ├── product.py         # Product catalog
│   ├── customer.py        # Customer profile
│   ├── order.py           # Order with items
│   └── payment.py         # Payment records
└── operations/
    ├── checkout.py        # Start checkout, apply coupons
    ├── fulfillment.py     # Process, ship, returns
    ├── payments.py        # Charge, refund, validate
    └── tracking.py        # Order tracking
```

**CRUD endpoints** auto-generated for all models (no explicit operations needed).

## How It Works

1. **`main` file** imports all models and operations
   - Decorators register metadata in registries

2. **`./main compile`** generates code
   - FastAPI routes with auto-generated CRUD
   - Prefect workflows with **automatic parallelization**
   - React UI configuration

3. **`./main up`** starts all services
   - Services communicate via MongoDB
   - Prefect automatically parallelizes independent operations

4. **Workflow Orchestration**
   - Operations with hierarchical naming (e.g., `ecommerce.payments.charge`, `ecommerce.fulfillment.process`)
   - Prefect automatically detects independence
   - Runs in parallel when possible
   - **40% time savings** from parallelization (vs sequential)

## Key Features

### Auto-Generated CRUD
```bash
GET    /products
POST   /products
GET    /products/{id}
PUT    /products/{id}
DELETE /products/{id}

GET    /customers
POST   /customers
# ... and so on
```

### Parallel Operations
Prefect automatically parallelizes:
- `ecommerce.payments.charge` and `ecommerce.fulfillment.process`
- Both run simultaneously instead of sequentially
- Reduces total order processing time

### Hierarchical Naming
```
ecommerce (domain)
├── checkout (category)
├── payments (category - can parallelize with fulfillment)
├── fulfillment (category - can parallelize with payments)
└── tracking (category)
```

## CLI Commands Available

```bash
./main status              # Show project status
./main models              # List registered models
./main compile             # Generate artifacts
./main graph               # Generate relationship diagrams
./main flows               # Generate operation flows (shows parallelization)
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
```bash
./main compile
cat .run_cache/registry.json | python -m json.tool
```

Should show:
- **4 models**: Product, Customer, Order, Payment
- **12 operations** across checkout, payments, fulfillment, tracking

### View Prefect Flows
```
http://localhost:4200
```

Check "Flows" section to see:
- Parallelization visualization
- Task execution times
- Performance improvements

### Check Logs
```bash
./main logs
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

**"Parallelization not working"**

Check Prefect logs and flow runs at http://localhost:4200. Verify operations have independent names (not nested dependencies).

**"Models not discovered"**

```bash
./main compile
cat .run_cache/registry.json | grep "models" -A 50
```

Ensure `main` file imports all 4 models.

**"Port conflicts"**

```bash
lsof -i :8000
kill -9 <PID>
./main up
```

## Next Steps

1. **Understand parallelization**: Monitor Prefect flows at http://localhost:4200
2. **Use CRUD operations**: Create products, customers, orders
3. **Execute workflows**: Process orders from checkout to shipment
4. **Add more operations**: Extend with notifications, analytics, returns
5. **Optimize**: Use Prefect's parallelization for performance

---

**Questions?** Check README.md for comprehensive documentation about the e-commerce system and parallelization strategy.
