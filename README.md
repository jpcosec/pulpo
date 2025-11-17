# Pulpo

A Python framework/library for building data-driven applications with automatic code generation and graph-based orchestration.

## Overview

**Pulpo** is a declarative framework that transforms your data models and business logic into fully-functional applications with auto-generated APIs, workflows, and frontend configurations.

### Key Features

1. **Declarative Models** - Define data structures using decorators (`@datamodel`)
2. **Operations Framework** - Define business logic operations with the `@operation` decorator
3. **Code Generation** - Automatically generates code artifacts from your definitions
4. **Graph-Based Architecture** - Uses directed graphs to validate and orchestrate operations
5. **Multi-Interface Support** - Includes CLI, frontend integration, and Prefect workflow support
6. **Example Projects** - Includes working examples (e-commerce, Pokemon app, todo app)

## Core Capabilities

### 1. Data Models
MongoDB/Beanie document models with metadata and relationship tracking

### 2. Business Operations
Declarative operations with typed inputs/outputs and automatic dependency detection

### 3. Data Flow Analysis
Automatic dependency detection and validation between operations

### 4. Orchestration
Prefect workflow generation and task composition

### 5. Code Generation
Auto-generates FastAPI routes, UI configs, and CLI commands

### 6. API Service
FastAPI server with CRUD endpoints for all models

### 7. Database Service
MongoDB connection and async ORM management

### 8. Prefect Workflows
Task scheduling and flow orchestration

### 9. Web UI
React/Refine frontend configuration generation

### 10. CLI Interface
Command-line access to all framework features

### 11. Validation & Linting
Type checking and anti-pattern detection

### 12. Configuration Management
YAML/environment-based settings and port allocation

### 13. Visualization
Mermaid graph generation for operation and model flows

### 14. Logging & Error Handling
Structured logging and exception hierarchy

### 15. Self-Awareness
Framework-level event tracking and diagnostics

## Architecture

Pulpo follows a **two-phase architecture**:

### Phase 1: Analysis (Code → Graph)
**Location**: `core/analysis/`

- **Decorators** (`@datamodel`, `@operation`) - Define your data models and operations
- **Registries** - Automatically capture all decorated classes
- **Discovery** - AST-based scanning or import-based detection
- **Graph Generation** - Build directed graphs of data flows
- **Dataflow Analysis** - Detect dependencies and validate flows
- **Validation & Linting** - Type checking and anti-pattern detection

### Phase 2: Generation (Graph → Code)
**Location**: `core/generation/`

#### `init` - Initial Setup:
- Generate CLI executable if it doesn't exist
- Create configuration files (`.pulpo.yml`)
- Generate graph visualizations

#### `compile` - Full Code Generation:
- **API** - FastAPI routes in `run_cache/generated_api.py`
- **UI** - React/Refine config in `run_cache/generated_frontend/`
- **Workflows** - Prefect flows in `run_cache/prefect_flows.py`
- **CLI** - Project-specific CLI commands
- **Docker** - Container configurations

### Services (Operate from `run_cache/`)
The 5 Docker services execute **generated code only**:
1. MongoDB (Database)
2. API Server (FastAPI)
3. UI (React/Refine)
4. Prefect Server
5. Prefect Worker

**Note**: `core/` is the framework/generator - it never runs in production.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pulpo.git
cd pulpo

# Install dependencies
pip install -e .

# Or with Poetry
poetry install
```

### Basic Usage

```python
from core.decorators import datamodel, operation
from pydantic import Field

# Define a data model
@datamodel
class Product:
    name: str = Field(description="Product name")
    price: float = Field(description="Product price")
    stock: int = Field(description="Available stock")

# Define an operation
@operation
async def create_product(name: str, price: float, stock: int) -> Product:
    """Create a new product"""
    product = Product(name=name, price=price, stock=stock)
    await product.save()
    return product
```

### Generate Code Artifacts

```bash
# Generate all artifacts (API, CLI, UI configs)
pulpo generate

# Start the API server
pulpo serve

# Run the CLI
pulpo --help
```

## Examples

Check the `examples/` directory for complete working applications:

- **E-Commerce App** - Product catalog, orders, payments, fulfillment
- **Pokemon App** - Pokemon management, battles, evolution system
- **Todo App** - Task management with users and workflows

## Documentation

For detailed documentation, see the `new docs/` directory:

- [Getting Started](new%20docs/01_Getting_Started.md)
- [Core Concepts](new%20docs/02_Core_Concepts.md)
- [Architecture](new%20docs/03_Architecture.md)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html
```

### Code Quality

```bash
# Format code
black core/ tests/

# Lint code
ruff check core/ tests/

# Type checking
mypy core/
```

## Requirements

- Python 3.11+
- MongoDB (for persistence)
- Prefect 3.0+ (for workflow orchestration)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

- Pulpo Team

## Repository Structure

```
pulpo/
├── core/                      # Framework code (never runs in production)
│   ├── analysis/              # Phase 1: Code → Graph
│   │   ├── decorators.py      # @datamodel, @operation
│   │   ├── registries.py      # ModelRegistry, OperationRegistry
│   │   ├── graphs/            # Graph generation & hierarchy
│   │   ├── dataflow/          # Dataflow analysis
│   │   └── validation/        # Linting & validation
│   ├── generation/            # Phase 2: Graph → Code
│   │   ├── codegen.py         # Main code generator
│   │   ├── init/              # Init phase (CLI, configs, graphs)
│   │   └── compile/           # Compile phase (API, UI, workflows)
│   ├── config/                # Configuration management
│   ├── cli/                   # Framework CLI
│   ├── utils/                 # Utilities (logging, exceptions)
│   └── selfawareness/         # Framework diagnostics
│
├── docs/                      # Documentation
├── examples/                  # Example projects (compressed .tar.gz)
├── templates/                 # Jinja2 templates for generation
├── scripts/                   # Helper scripts
├── tests/                     # Test suite
└── README.md                  # This file
```

### Generated Code (Not in Repository)
```
run_cache/                     # Generated at compile time
├── generated_api.py           # FastAPI routes
├── generated_frontend/        # React/Refine UI
├── prefect_flows.py           # Prefect workflows
├── cli/                       # Project CLI
└── graphs/                    # Mermaid visualizations
```

## Project Status

Version: 0.6.0 (Alpha)
