# Pulpo Core - Makefile
# Framework for metadata-driven code generation and orchestration

.PHONY: help build up down restart logs clean rebuild status health shell api-shell db-shell test lint lint-models check-models format type-check test-unit compile preload warmup discover discover-models discover-operations setup-project init-project codegen demo ui-install ui-dev ui-build ui-test ui-lint test-integration test-e2e test-all test-coverage db-init db-seed db-backup db-restore prefect-server prefect-worker prefect-ui prefect-logs prefect-stop

# Core directory location
CORE_DIR := $(shell cd $(dir $(lastword $(MAKEFILE_LIST))) && pwd)

# Config file for discovery paths (defaults to project config in parent directory)
CONFIG_FILE ?= ..

# =============================================================================
# Default target: Show help
# =============================================================================
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         Pulpo Core - Code Generation & Orchestration           ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Project Setup:"
	@echo "  make init               - Initialize new project in pwd"
	@echo "  make init-project       - Alias for 'make init'"
	@echo "  make setup-project      - Init + discover"
	@echo "  make setup <action>     - Meta-command (see below)"
	@echo ""
	@echo "🔍 Discovery Commands (AST-based, no imports):"
	@echo "  make discover           - Show all models/operations"
	@echo "  make discover-models    - Show datamodels only"
	@echo "  make discover-operations- Show operations only"
	@echo ""
	@echo "🔨 Compilation & Building:"
	@echo "  make compile            - Generate code from @datamodel/@operation"
	@echo "  make build              - Build Docker images (default: latest)"
	@echo "  make build VERSION=v1.0 - Build with specific version"
	@echo "  make build-clean        - Clean build (no cache)"
	@echo ""
	@echo "🚀 Services:"
	@echo "  make up                 - Start all services"
	@echo "  make down               - Stop services"
	@echo "  make restart            - Restart services"
	@echo "  make api                - Run API locally (requires MongoDB)"
	@echo ""
	@echo "⚙️  Setup Meta-Command:"
	@echo "  make setup init         - Initialize project"
	@echo "  make setup discover     - Discover models/operations"
	@echo "  make setup compile      - Compile code"
	@echo "  make setup build        - Build images"
	@echo "  make setup up           - Start services"
	@echo "  make setup full         - All of the above"
	@echo ""
	@echo "📚 Demo:"
	@echo "  make demo               - Unpack Pokemon demo project"
	@echo ""
	@echo "🔍 Monitoring Commands:"
	@echo "  make logs        - Show logs from all services"
	@echo "  make status      - Show status of all containers"
	@echo "  make health      - Check health of API and database"
	@echo ""
	@echo "🛠️  Utility Commands:"
	@echo "  make shell       - Open shell in API container"
	@echo "  make api-shell   - Open shell in API container"
	@echo "  make db-shell    - Open MongoDB shell"
	@echo "  make clean       - Remove containers and volumes (⚠️  destructive)"
	@echo "  make clean-cache - Remove generated code (.run_cache/)"
	@echo "  make rebuild     - Rebuild images and restart"
	@echo ""
	@echo "🖥️  Frontend Commands:"
	@echo "  make ui-install  - Install frontend dependencies"
	@echo "  make ui-dev      - Start React dev server"
	@echo "  make ui-build    - Build React for production"
	@echo "  make ui-test     - Run frontend E2E tests"
	@echo "  make ui-lint     - Lint frontend code"
	@echo ""
	@echo "🔍 Code Quality Commands:"
	@echo "  make lint-models - Lint datamodels/operations (catch type mismatches, docs, etc)"
	@echo "  make lint        - Lint Python code with ruff"
	@echo "  make format      - Format code with ruff"
	@echo "  make type-check  - Run mypy type checker"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test        - Run E2E tests against running API"
	@echo "  make test-unit   - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e    - Run end-to-end tests"
	@echo "  make test-all    - Run all tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo ""
	@echo "✨ Code Quality Commands:"
	@echo "  make lint        - Check code quality with ruff"
	@echo "  make format      - Auto-format code with ruff"
	@echo "  make type-check  - Run mypy type checking"
	@echo ""
	@echo "🗄️  Database Commands:"
	@echo "  make db-start    - Start MongoDB in Docker"
	@echo "  make db-stop     - Stop MongoDB"
	@echo "  make db-status   - Check MongoDB status"
	@echo "  make db-logs     - View MongoDB logs"
	@echo "  make db-init     - Initialize database schema"
	@echo "  make db-seed     - Seed test data"
	@echo "  make db-backup   - Backup MongoDB data"
	@echo "  make db-restore  - Restore MongoDB from backup"
	@echo ""
	@echo "🔄 Workflow Commands (Prefect):"
	@echo "  make prefect-server - Start Prefect server"
	@echo "  make prefect-worker - Start Prefect worker"
	@echo "  make prefect-ui     - Open Prefect UI in browser"
	@echo "  make prefect-logs   - Show Prefect server logs"
	@echo "  make prefect-stop   - Stop Prefect services"
	@echo ""
	@echo "📚 Quick Start (Local Development):"
	@echo "  1. make start    - Start MongoDB + API in one command!"
	@echo "  2. Visit http://localhost:8000/docs"
	@echo ""
	@echo "📚 Quick Start (Docker):"
	@echo "  1. make compile  - Generate code from models/operations"
	@echo "  2. make build    - Build Docker images"
	@echo "  3. make up       - Start all services"
	@echo "  4. make health   - Check service status"
	@echo "  5. Visit http://localhost:8000/docs"
	@echo ""

# =============================================================================
# Setup & Build
# =============================================================================
build: codegen
	@echo "🔨 Building Docker images (with cache for speed)..."
	@CONFIG_FILE_PATH="$(CONFIG_FILE)/.env"; \
	if [ -f "$$CONFIG_FILE_PATH" ]; then \
		if [ -n "$(VERSION)" ]; then \
			echo "   📝 Updating IMAGE_VERSION to $(VERSION) in $$CONFIG_FILE_PATH..."; \
			sed -i '' 's/^IMAGE_VERSION=.*/IMAGE_VERSION=$(VERSION)/' "$$CONFIG_FILE_PATH" || sed -i 's/^IMAGE_VERSION=.*/IMAGE_VERSION=$(VERSION)/' "$$CONFIG_FILE_PATH"; \
		fi; \
		echo "   📋 Current IMAGE_VERSION: $$(grep IMAGE_VERSION $$CONFIG_FILE_PATH)"; \
	fi
	@DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f $(CORE_DIR)/docker/docker-compose.yml build

build-clean: codegen
	@echo "🔨 Building Docker images (clean build, no cache)..."
	@CONFIG_FILE_PATH="$(CONFIG_FILE)/.env"; \
	if [ -f "$$CONFIG_FILE_PATH" ]; then \
		if [ -n "$(VERSION)" ]; then \
			echo "   📝 Updating IMAGE_VERSION to $(VERSION) in $$CONFIG_FILE_PATH..."; \
			sed -i '' 's/^IMAGE_VERSION=.*/IMAGE_VERSION=$(VERSION)/' "$$CONFIG_FILE_PATH" || sed -i 's/^IMAGE_VERSION=.*/IMAGE_VERSION=$(VERSION)/' "$$CONFIG_FILE_PATH"; \
		fi; \
		echo "   📋 Current IMAGE_VERSION: $$(grep IMAGE_VERSION $$CONFIG_FILE_PATH)"; \
	fi
	@DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f $(CORE_DIR)/docker/docker-compose.yml build --no-cache

rebuild: clean build up
	@echo "✅ Rebuild complete!"

# =============================================================================
# Compile/Pre-warming (speeds up startup)
# =============================================================================
compile: codegen warmup

codegen:
	@echo "🔨 Generating code from @datamodel/@operation decorators..."
	@echo ""
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH CONFIG_FILE=$(CONFIG_FILE) python3 -m core.codegen
	@echo ""

warmup:
	@echo "🔥 Pre-warming Python modules..."
	@echo ""
	@echo "1️⃣  Compiling Python bytecode..."
	@python3 -m compileall -q core/ 2>/dev/null || true
	@echo "   ✅ Bytecode compiled"
	@echo ""
	@echo "2️⃣  Pre-loading modules..."
	@python3 -c "import sys; sys.path.insert(0, '.'); from core.database.models import *; from core.core.registries import *; print('   ✅ Core modules loaded')" 2>/dev/null || echo "   ⚠️  Some modules failed to load (may need MongoDB running)"
	@echo ""
	@echo "3️⃣  Validating configuration..."
	@python3 -c "from core.utils.config import get_settings; s = get_settings(); print(f'   ✅ Config loaded: {s.mongodb_database}')" || echo "   ⚠️  Config validation failed"
	@echo ""
	@echo "✅ Pre-warming complete!"
	@echo "   Next: run 'make up' to start services"
	@echo ""

preload: warmup

# =============================================================================
# Project Initialization & Discovery
# =============================================================================
init-project: init
	@true

init:
	@echo "🎯 Initializing new Pulpo Core project in pwd..."
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH python3 $(CORE_DIR)/scripts/init_project.py $(PROJECT_NAME) 2>&1

setup-project:
	@echo "⚙️  Setting up project (init + discover)..."
	@make init
	@echo ""
	@make discover

discover:
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH CONFIG_FILE=$(CONFIG_FILE) python3 $(CORE_DIR)/scripts/discovery_file_scan.py

discover-models:
	@echo "ℹ️  Use 'make discover' to see all models and operations"
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH CONFIG_FILE=$(CONFIG_FILE) python3 $(CORE_DIR)/scripts/discovery_file_scan.py | grep -A 999 "Discovered Models"

discover-operations:
	@echo "ℹ️  Use 'make discover' to see all models and operations"
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH CONFIG_FILE=$(CONFIG_FILE) python3 $(CORE_DIR)/scripts/discovery_file_scan.py | grep -A 999 "Discovered Operations"

# =============================================================================
# Demo Project
# =============================================================================
demo:
	@echo "📦 Unpacking demo project..."
	@cd .. && tar -xzf core/core/demo-project.tar.gz
	@echo "✅ Demo project unpacked!"
	@echo ""
	@echo "⚙️  Generating configuration..."
	@cd ../test-project-demo && python3 -c "import yaml; config = {'project_name': 'test-project-demo', 'version': '1.0', 'port_base': 10010, 'ports': {'api': 10010, 'ui': 10011, 'mongodb': 10012, 'prefect_server': 10013, 'prefect_ui': 10014}, 'discovery': {'models_dirs': ['models'], 'operations_dirs': ['operations']}, 'docker': {'image_version': 'latest', 'base_image': 'test-project-demo'}}; open('.pulpo.yml', 'w').write(yaml.dump(config, default_flow_style=False))"
	@echo "✅ Configuration generated!"
	@echo ""
	@echo "📋 Demo project structure:"
	@echo "   test-project-demo/"
	@echo "   ├── .pulpo.yml          (Auto-generated configuration)"
	@echo "   ├── models/             (Data model definitions)"
	@echo "   └── operations/         (Operation implementations)"
	@echo ""
	@echo "🚀 Next steps:"
	@echo "   1. cd test-project-demo"
	@echo "   2. make compile        (generate code from models/operations)"
	@echo "   3. make api            (start API server)"
	@echo "   4. make ui-dev         (in another terminal, start UI)"
	@echo ""

# =============================================================================
# API Server (Local Development)
# =============================================================================
api: compile
	@echo "🚀 Starting API server (local development)..."
	@echo ""
	@echo "Checking MongoDB..."
	@docker exec jobhunter-mongodb mongosh --quiet --eval "db.runCommand('ping')" 2>/dev/null \
		|| (echo "   MongoDB not running, starting..." && make db-start)
	@echo ""
	@echo "📚 API Documentation: http://localhost:8000/docs"
	@echo "🏥 Health Check:      http://localhost:8000/health"
	@echo ""
	@python3 scripts/run_api.py

# =============================================================================
# Start/Stop Services
# =============================================================================
up: compile
	@echo "🚀 Starting services..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@make health


down:
	@echo "🛑 Stopping services..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml down
	@echo "✅ Services stopped!"

restart: down up
	@echo "✅ Services restarted!"

# =============================================================================
# Monitoring & Logs
# =============================================================================
logs:
	@echo "📋 Showing logs (Ctrl+C to exit)..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml logs -f

status:
	@echo "📊 Container Status:"
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml ps

health:
	@echo "🏥 Checking all module health..."
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 DATABASE"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@docker exec jobhunter-mongodb mongosh --quiet --eval "db.runCommand('ping')" 2>/dev/null \
		&& echo "  ✅ MongoDB: healthy (mongodb://localhost:27017)" \
		|| echo "  ❌ MongoDB: unhealthy or not running"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🔌 API"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@curl -sf http://localhost:8000/health -o /dev/null 2>/dev/null \
		&& (echo "  ✅ API: healthy" && \
		    echo "     📚 Docs:   http://localhost:8000/docs" && \
		    echo "     🏥 Health: http://localhost:8000/health" && \
		    echo "     🔌 API:    http://localhost:8000/api/v1" && \
		    curl -s http://localhost:8000/health | python3 -m json.tool | sed 's/^/     /') \
		|| echo "  ❌ API: unhealthy or not running"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🖥️  UI (Refine.dev)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@curl -sf http://localhost:3000 -o /dev/null 2>/dev/null \
		&& echo "  ✅ UI: healthy (http://localhost:3000)" \
		|| echo "  ❌ UI: unhealthy or not running"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🔄 ORCHESTRATION (Prefect)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@curl -sf http://localhost:4200/api/health -o /dev/null 2>/dev/null \
		&& echo "  ✅ Prefect Server: healthy (http://localhost:4200)" \
		|| echo "  ❌ Prefect Server: unhealthy or not running"
	@docker ps | grep -q jobhunter-prefect-worker \
		&& echo "  ✅ Prefect Worker: running" \
		|| echo "  ❌ Prefect Worker: not running"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🖲️  CLI"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@./jobhunter ops list 2>/dev/null | grep -q "Total operations" \
		&& echo "  ✅ CLI: working (./jobhunter)" \
		|| echo "  ❌ CLI: not working"
	@echo ""

# =============================================================================
# Shell Access
# =============================================================================
shell: api-shell

api-shell:
	@echo "🐚 Opening shell in API container..."
	docker exec -it jobhunter-api /bin/bash

db-shell:
	@echo "🐚 Opening MongoDB shell..."
	docker exec -it jobhunter-mongodb mongosh jobhunter

# =============================================================================
# Cleanup
# =============================================================================
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	@echo "⚠️  This will delete all data."
	@printf "   Continue? [y/N] "; \
	read REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		docker-compose -f $(CORE_DIR)/docker/docker-compose.yml down -v; \
		docker system prune -f; \
		rm -rf .run_cache/; \
		rm -rf cli/; \
		echo "✅ Cleanup complete!"; \
	else \
		echo "❌ Cleanup cancelled."; \
	fi

clean-cache:
	@echo "🧹 Cleaning generated code cache..."
	@rm -rf .run_cache/
	@echo "✅ Cache cleaned! Run 'make compile' to regenerate."

# =============================================================================
# Testing
# =============================================================================
test:
	@echo "🧪 Running E2E tests..."
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 5
	pytest tests/e2e/ -v
	@echo "✅ Tests complete!"

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v --cov=core --cov-report=term-missing
	@echo "✅ Unit tests complete!"

# =============================================================================
# Code Quality
# =============================================================================
lint:
	@echo "🔍 Running ruff linter..."
	ruff check core
	@echo "✅ Linting complete!"

lint-models:
	@echo "🔍 Linting datamodels and operations..."
	@PYTHONPATH=$(CORE_DIR):$$PYTHONPATH python3 -m core.cli lint check --level warning
	@echo "✅ Model linting complete!"

check-models: lint-models

format:
	@echo "✨ Formatting code with ruff..."
	ruff format core
	@echo "✅ Formatting complete!"

type-check:
	@echo "🔎 Running mypy type checker..."
	mypy core
	@echo "✅ Type checking complete!"

# Combined code quality check
quality: lint type-check
	@echo "✅ All quality checks passed!"

# =============================================================================
# Database Management
# =============================================================================
db-start:
	@echo "🗄️  Starting MongoDB..."
	@docker ps -a --format '{{.Names}}' | grep -q '^jobhunter-mongodb$$' && \
		(echo "   Container exists, starting..." && docker start jobhunter-mongodb) || \
		(echo "   Creating new container..." && \
		docker run -d \
			--name jobhunter-mongodb \
			-p 27017:27017 \
			-v jobhunter-mongo-data:/data/db \
			mongo:7.0)
	@echo "✅ MongoDB started!"
	@echo "   Connection: mongodb://localhost:27017"
	@echo "   Database: jobhunter"
	@sleep 2
	@make db-status

db-stop:
	@echo "🛑 Stopping MongoDB..."
	@docker stop jobhunter-mongodb 2>/dev/null || echo "   MongoDB not running"
	@echo "✅ MongoDB stopped"

db-status:
	@echo "📊 MongoDB Status:"
	@docker exec jobhunter-mongodb mongosh --quiet --eval "db.runCommand('ping')" 2>/dev/null \
		&& echo "   ✅ MongoDB: Running and healthy" \
		|| echo "   ❌ MongoDB: Not running (run 'make db-start')"

db-logs:
	@echo "📋 MongoDB Logs (Ctrl+C to exit)..."
	@docker logs -f jobhunter-mongodb

db-backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker exec jobhunter-mongodb mongodump --db jobhunter --out /tmp/backup
	docker cp jobhunter-mongodb:/tmp/backup ./backups/backup-$$(date +%Y%m%d-%H%M%S)
	@echo "✅ Backup created in ./backups/"

db-restore:
	@echo "📥 Restoring database from backup..."
	@read -p "Enter backup directory name: " BACKUP; \
	docker cp ./backups/$$BACKUP jobhunter-mongodb:/tmp/restore; \
	docker exec jobhunter-mongodb mongorestore --db jobhunter /tmp/restore/jobhunter
	@echo "✅ Database restored!"

# =============================================================================
# Frontend Commands
# =============================================================================
.PHONY: ui-install
ui-install: codegen ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	@if [ ! -d ".run_cache/generated_frontend" ]; then \
		echo "❌ Generated frontend not found. Run 'make codegen' first."; \
		exit 1; \
	fi
	cd .run_cache/generated_frontend && npm install --legacy-peer-deps
	@echo "✅ Frontend dependencies installed!"

.PHONY: ui-dev
ui-dev: codegen ## Start React dev server
	@echo "🚀 Starting React development server..."
	@if [ ! -d ".run_cache/generated_frontend" ]; then \
		echo "❌ Generated frontend not found. Run 'make codegen' first."; \
		exit 1; \
	fi
	cd .run_cache/generated_frontend && npm run dev

.PHONY: ui-build
ui-build: codegen ## Build React for production
	@echo "🔨 Building React for production..."
	@if [ ! -d ".run_cache/generated_frontend" ]; then \
		echo "❌ Generated frontend not found. Run 'make codegen' first."; \
		exit 1; \
	fi
	cd .run_cache/generated_frontend && npm run build
	@echo "✅ Frontend built!"

.PHONY: ui-test
ui-test: codegen ## Run frontend E2E tests
	@echo "🧪 Running frontend E2E tests..."
	@if [ ! -d ".run_cache/generated_frontend" ]; then \
		echo "❌ Generated frontend not found. Run 'make codegen' first."; \
		exit 1; \
	fi
	cd .run_cache/generated_frontend && npm run test:e2e
	@echo "✅ Frontend tests complete!"

.PHONY: ui-lint
ui-lint: codegen ## Lint frontend code
	@echo "🔍 Linting frontend code..."
	@if [ ! -d ".run_cache/generated_frontend" ]; then \
		echo "❌ Generated frontend not found. Run 'make codegen' first."; \
		exit 1; \
	fi
	cd .run_cache/generated_frontend && npm run lint
	@echo "✅ Frontend linting complete!"

# =============================================================================
# Enhanced Testing Commands
# =============================================================================
.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "🧪 Running integration tests..."
	docker exec jobhunter-api pytest tests/integration/ -v
	@echo "✅ Integration tests complete!"

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@echo "🧪 Running end-to-end tests..."
	docker exec jobhunter-api pytest tests/e2e/ -v
	@echo "✅ E2E tests complete!"

.PHONY: test-all
test-all: test-unit test-integration test-e2e ## Run all tests
	@echo "✅ All tests complete!"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	docker exec jobhunter-api pytest --cov=core --cov-report=term-missing --cov-report=html
	@echo "✅ Coverage report generated! Open htmlcov/index.html to view."

# =============================================================================
# Enhanced Code Quality Commands
# =============================================================================
# Note: lint, format, and type-check commands already exist above
# Adding enhanced versions that work with Docker

.PHONY: lint-docker
lint-docker: ## Run ruff and mypy in Docker
	@echo "🔍 Running linters in Docker..."
	docker exec jobhunter-api ruff check core
	docker exec jobhunter-api mypy core
	@echo "✅ Linting complete!"

.PHONY: format-docker
format-docker: ## Format code with ruff in Docker
	@echo "✨ Formatting code in Docker..."
	docker exec jobhunter-api ruff check core --fix
	docker exec jobhunter-api ruff format core
	@echo "✅ Formatting complete!"

# =============================================================================
# Enhanced Database Commands
# =============================================================================
.PHONY: db-init
db-init: ## Initialize database schema
	@echo "🗄️  Initializing database..."
	docker exec jobhunter-api python -c "from core.database.connection import init_database; import asyncio; asyncio.run(init_database())"
	@echo "✅ Database initialized!"

.PHONY: db-seed
db-seed: ## Seed test data
	@echo "🌱 Seeding database with test data..."
	docker exec jobhunter-api python -c "print('TODO: Create seed script')"
	@echo "⚠️  Note: Seed script needs to be created"

# db-backup and db-restore already exist above

# =============================================================================
# Prefect Workflow Commands
# =============================================================================
.PHONY: prefect-server
prefect-server: ## Start Prefect server
	@echo "🔄 Starting Prefect server..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml up -d prefect-server
	@echo ""
	@echo "✅ Prefect server started!"
	@echo "🌐 Prefect UI: http://localhost:4200"
	@echo ""

.PHONY: prefect-worker
prefect-worker: ## Start Prefect worker
	@echo "🔄 Starting Prefect worker..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml up -d prefect-worker
	@echo "✅ Prefect worker started!"

.PHONY: prefect-ui
prefect-ui: ## Open Prefect UI in browser
	@echo "🌐 Opening Prefect UI..."
	@which xdg-open > /dev/null && xdg-open http://localhost:4200 || \
	which open > /dev/null && open http://localhost:4200 || \
	echo "Please open http://localhost:4200 in your browser"

.PHONY: prefect-logs
prefect-logs: ## Show Prefect server logs
	@echo "📋 Showing Prefect logs (Ctrl+C to exit)..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml logs -f prefect-server

.PHONY: prefect-stop
prefect-stop: ## Stop Prefect services
	@echo "🛑 Stopping Prefect services..."
	docker-compose -f $(CORE_DIR)/docker/docker-compose.yml stop prefect-server prefect-worker
	@echo "✅ Prefect services stopped!"

# =============================================================================
# Quick Development Commands
# =============================================================================
start: api
	@echo "✅ Everything started! API is running."

stop-local: db-stop
	@echo "✅ Local development stopped!"

install: build up
	@echo "✅ Installation complete! Services are running."

stop: down

reload: restart

# init-docker: Full initialization for Docker deployment (deprecated, use 'make init' for projects)
# Kept for backward compatibility
init-docker-setup:
	@echo "🎬 Initializing JobHunter AI (Docker)..."
	@echo "1️⃣  Building Docker images..."
	@make build
	@echo ""
	@echo "2️⃣  Starting services..."
	@make up
	@echo ""
	@echo "3️⃣  Waiting for services to be ready..."
	@sleep 10
	@echo ""
	@make health
	@echo ""
	@echo "🎉 JobHunter AI is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  • Visit http://localhost:8000/docs to explore the API"
	@echo "  • Run 'make logs' to watch the logs"
	@echo "  • Run 'make test' to run tests"
	@echo ""

# =============================================================================
# Setup Meta-Command
# =============================================================================
.PHONY: setup

setup:
	@echo "⚙️  Setup command requires an action:"
	@echo ""
	@echo "Usage: make setup <action>"
	@echo ""
	@echo "Actions:"
	@echo "  make setup init       - Initialize new project"
	@echo "  make setup discover   - Discover models/operations"
	@echo "  make setup compile    - Compile code"
	@echo "  make setup build      - Build Docker images"
	@echo "  make setup up         - Start services"
	@echo "  make setup full       - Init + discover + compile + build + up"
	@echo ""

.PHONY: setup-init setup-discover setup-compile setup-build setup-up setup-full

setup-init:
	@make init

setup-discover:
	@make discover

setup-compile:
	@make compile

setup-build:
	@make build

setup-up:
	@make up

setup-full:
	@echo "🚀 Full setup: init + discover + compile + build + up"
	@make init
	@echo ""
	@make discover
	@echo ""
	@make compile
	@echo ""
	@make build
	@echo ""
	@make up
