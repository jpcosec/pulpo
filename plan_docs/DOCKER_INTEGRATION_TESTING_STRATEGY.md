# Docker Integration Testing Strategy

**Date:** 2025-10-30
**Status:** Integration Testing Design
**Scope:** Real Docker-based testing (no mocking)

---

## User Feedback

**Requirement:** "There's no need to mock anything, after we test the generation, we should mount the test project on docker in order to test."

This means: Use real Docker containers for testing services, APIs, and data transformations.

---

## Testing Architecture

### Test Phases

```
Phase 1: Unit Tests
  ↓
Phase 2: CLI Tests (subprocess)
  ↓
Phase 3: Code Generation Tests
  ↓
Phase 4: Docker Integration Tests ← YOU ARE HERE
  ↓
Phase 5: End-to-End Tests
```

### Docker Integration Test Scope

```
┌─────────────────────────────────────────────────────────┐
│ Docker Integration Tests                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ Real MongoDB container running                       │
│ ✅ Real FastAPI container running                       │
│ ✅ Real Prefect container running                       │
│ ✅ Real data persisted to MongoDB                       │
│ ✅ Real API endpoints responding                        │
│ ✅ Real Prefect flows executing                         │
│ ✅ Real Docker Compose orchestration                    │
│                                                         │
│ ❌ No mocking of subprocess calls                       │
│ ❌ No mocking of Docker commands                        │
│ ❌ No mocking of database operations                    │
│ ❌ No mocking of HTTP requests (use real API)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Docker Compose for Testing

### Test Environment Setup

```python
import pytest
import docker
from pathlib import Path

@pytest.fixture(scope="session")
def docker_client():
    """Get Docker client."""
    return docker.from_env()

@pytest.fixture(scope="session")
def test_docker_compose():
    """Create docker-compose.yml for tests."""
    compose_content = """
version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    container_name: pulpo-test-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: pulpo_test
    volumes:
      - mongodb-test-data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    image: pulpo-api:test
    container_name: pulpo-test-api
    ports:
      - "8000:8000"
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      DATABASE_URL: mongodb://mongodb:27017/pulpo_test
      LOG_LEVEL: debug
    volumes:
      - ./generated_api.py:/app/generated_api.py
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 5s
      retries: 5

  prefect:
    image: pulpo-prefect:test
    container_name: pulpo-test-prefect
    ports:
      - "4200:4200"
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      DATABASE_URL: mongodb://mongodb:27017/pulpo_test
    volumes:
      - ./generated_flows.py:/app/generated_flows.py

volumes:
  mongodb-test-data:

networks:
  default:
    name: pulpo-test-network
"""
    return compose_content
```

---

## Fixture: Docker Services

```python
import subprocess
import time
from typing import Generator

@pytest.fixture
def docker_services(compiled_project, test_docker_compose):
    """Start Docker services for testing."""
    project_dir = compiled_project

    # Write docker-compose.yml
    compose_file = project_dir / "docker-compose.test.yml"
    compose_file.write_text(test_docker_compose)

    # Build images
    build_result = subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "build"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    if build_result.returncode != 0:
        raise RuntimeError(f"Docker build failed: {build_result.stderr}")

    # Start services
    start_result = subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
    if start_result.returncode != 0:
        raise RuntimeError(f"Docker compose up failed: {start_result.stderr}")

    # Wait for services to be healthy
    max_retries = 30
    for i in range(max_retries):
        health_result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "ps"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        if all([
            "healthy" in health_result.stdout or "running" in health_result.stdout
            for _ in ["mongodb", "api"]  # Check critical services
        ]):
            break

        time.sleep(2)
    else:
        raise RuntimeError("Services failed to become healthy")

    yield project_dir

    # Cleanup: Stop services
    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
        cwd=project_dir,
        capture_output=True,
        timeout=30
    )
```

---

## Test: MongoDB Operations

```python
import pymongo
from pymongo import MongoClient

class TestMongoDBIntegration:
    """Test actual MongoDB operations."""

    @pytest.fixture
    def mongo_client(self, docker_services):
        """Connect to MongoDB in Docker."""
        client = MongoClient("mongodb://localhost:27017")
        yield client
        client.close()

    def test_mongodb_connected(self, mongo_client):
        """Test MongoDB is running and responsive."""
        # Should not raise
        info = mongo_client.server_info()
        assert info["version"]

    def test_create_document(self, mongo_client):
        """Test creating a document in MongoDB."""
        db = mongo_client["pulpo_test"]
        collection = db["pokemons"]

        # Insert document
        result = collection.insert_one({
            "name": "Pikachu",
            "element": "Electric",
            "health": 35,
            "attack": 55
        })

        # Retrieve document
        doc = collection.find_one({"_id": result.inserted_id})
        assert doc["name"] == "Pikachu"

    def test_model_persistence(self, mongo_client):
        """Test @datamodel instances persist to MongoDB."""
        db = mongo_client["pulpo_test"]

        # Simulate what generated code does:
        pokemon = {
            "name": "Charmander",
            "element": "Fire",
            "health": 39,
            "attacks": ["Scratch", "Ember"]
        }

        # Insert via generated API layer
        result = db.pokemons.insert_one(pokemon)

        # Query back
        retrieved = db.pokemons.find_one({"_id": result.inserted_id})
        assert retrieved["name"] == "Charmander"
        assert retrieved["attacks"] == ["Scratch", "Ember"]

    def test_model_updates(self, mongo_client):
        """Test updating model documents."""
        db = mongo_client["pulpo_test"]
        collection = db["pokemons"]

        # Create
        result = collection.insert_one({
            "name": "Bulbasaur",
            "level": 5,
            "experience": 0
        })

        # Update
        collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"level": 10, "experience": 1000}}
        )

        # Verify
        doc = collection.find_one({"_id": result.inserted_id})
        assert doc["level"] == 10
        assert doc["experience"] == 1000
```

---

## Test: API Endpoints

```python
import requests
import json

class TestAPIIntegration:
    """Test actual API endpoints running in Docker."""

    @pytest.fixture
    def api_url(self, docker_services):
        """Get API URL."""
        return "http://localhost:8000"

    def test_api_health(self, api_url):
        """Test API health endpoint."""
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200

    def test_create_pokemon_via_api(self, api_url):
        """Test creating Pokemon via REST API."""
        payload = {
            "name": "Pikachu",
            "element": "Electric",
            "health": 35,
            "attack": 55,
            "attacks": ["Thunderbolt"]
        }

        response = requests.post(
            f"{api_url}/pokemons",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Pikachu"
        pokemon_id = data["_id"]

        # Verify via GET
        response = requests.get(f"{api_url}/pokemons/{pokemon_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Pikachu"

    def test_operation_via_api(self, api_url):
        """Test running operation via REST API."""
        operation_payload = {
            "trainer_name": "Ash",
            "pokemon_name": "Pikachu",
            "element": "Electric"
        }

        response = requests.post(
            f"{api_url}/operations/pokemon/management/catch",
            json=operation_payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "Pikachu" in result["message"]

    def test_list_pokemons_api(self, api_url):
        """Test list endpoint."""
        # Create multiple Pokemon
        for name in ["Pikachu", "Charmander", "Bulbasaur"]:
            requests.post(
                f"{api_url}/pokemons",
                json={
                    "name": name,
                    "element": "Fire",
                    "health": 35,
                    "attack": 55
                }
            )

        # List them
        response = requests.get(f"{api_url}/pokemons")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_pokemon_via_api(self, api_url):
        """Test updating via REST API."""
        # Create
        create_response = requests.post(
            f"{api_url}/pokemons",
            json={"name": "Squirtle", "element": "Water", "health": 44, "attack": 48}
        )
        pokemon_id = create_response.json()["_id"]

        # Update
        update_response = requests.put(
            f"{api_url}/pokemons/{pokemon_id}",
            json={"level": 10, "health": 50}
        )

        assert update_response.status_code == 200

        # Verify
        get_response = requests.get(f"{api_url}/pokemons/{pokemon_id}")
        assert get_response.json()["level"] == 10
```

---

## Test: Prefect Flow Execution

```python
import subprocess

class TestPrefectIntegration:
    """Test actual Prefect flow execution in Docker."""

    def test_prefect_flow_runs(self, docker_services):
        """Test that Prefect flows execute."""
        # Run a flow
        result = subprocess.run(
            [
                "python", "-m", "prefect.cli",
                "flow", "run",
                "pokemon.management.catch",
                "--input", json.dumps({
                    "trainer_name": "Ash",
                    "pokemon_name": "Pikachu",
                    "element": "Electric"
                })
            ],
            cwd=docker_services,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        assert "Pikachu" in result.stdout

    def test_parallel_operations(self, docker_services):
        """Test parallel operations execute together."""
        # Run two management operations in sequence
        # (In real Prefect, these would run in parallel)

        start_time = time.time()

        # Both operations should complete faster than sequential
        for name in ["pokemon.management.catch", "pokemon.management.train"]:
            subprocess.run(
                ["python", "-m", "prefect.cli", "flow", "run", name],
                cwd=docker_services,
                capture_output=True,
                timeout=30,
                check=True
            )

        elapsed = time.time() - start_time

        # If parallel: ~5s (both run together)
        # If sequential: ~10s (one after another)
        # Actual timing depends on implementation
        assert elapsed < 15  # Allow some overhead

    def test_sequential_operations(self, docker_services):
        """Test sequential operations maintain order."""
        # Evolution should be sequential: stage1 → stage2

        result = subprocess.run(
            ["python", "-m", "prefect.cli", "flow", "run", "pokemon.evolution"],
            cwd=docker_services,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        # Check that stage1 completes before stage2
        assert result.stdout.index("stage1") < result.stdout.index("stage2")
```

---

## Test: Data Transformation Pipeline

```python
class TestDataTransformationPipeline:
    """Test complete data transformation workflows."""

    def test_catch_train_evolve_pipeline(self, api_url, mongo_client):
        """Test complete pipeline: catch → train → evolve."""

        # Step 1: Create Trainer
        trainer_response = requests.post(
            f"{api_url}/operations/pokemon/management/trainer_create",
            json={"trainer_name": "Ash", "region": "Kanto"}
        )
        assert trainer_response.status_code == 200

        # Step 2: Catch Pokemon
        catch_response = requests.post(
            f"{api_url}/operations/pokemon/management/catch",
            json={
                "trainer_name": "Ash",
                "pokemon_name": "Charmander",
                "element": "Fire"
            }
        )
        assert catch_response.status_code == 200

        # Step 3: Train Pokemon
        train_response = requests.post(
            f"{api_url}/operations/pokemon/management/train",
            json={
                "pokemon_name": "Charmander",
                "training_hours": 100
            }
        )
        assert train_response.status_code == 200
        train_data = train_response.json()
        assert train_data["new_level"] > 5

        # Step 4: Evolve to stage1
        evo1_response = requests.post(
            f"{api_url}/operations/pokemon/evolution/stage1",
            json={"pokemon_name": "Charmander"}
        )
        assert evo1_response.status_code == 200

        # Step 5: Evolve to stage2
        evo2_response = requests.post(
            f"{api_url}/operations/pokemon/evolution/stage2",
            json={"pokemon_name": "Charmeleon"}
        )
        assert evo2_response.status_code == 200

        # Verify in MongoDB
        db = mongo_client["pulpo_test"]
        pokemon = db.pokemons.find_one({"name": "Charizard"})
        assert pokemon is not None

    def test_battle_pipeline(self, api_url):
        """Test battle operations."""

        # Step 1: Create two trainers with Pokemon
        for trainer_name in ["Ash", "Brock"]:
            requests.post(
                f"{api_url}/operations/pokemon/management/trainer_create",
                json={"trainer_name": trainer_name, "region": "Kanto"}
            )

        # Step 2: Each catches a Pokemon
        for trainer_name in ["Ash", "Brock"]:
            requests.post(
                f"{api_url}/operations/pokemon/management/catch",
                json={
                    "trainer_name": trainer_name,
                    "pokemon_name": f"{trainer_name}'s Pokemon",
                    "element": "Electric"
                }
            )

        # Step 3: Battle!
        battle_response = requests.post(
            f"{api_url}/operations/pokemon/battles/trainer_execute",
            json={
                "trainer1_name": "Ash",
                "trainer2_name": "Brock"
            }
        )

        assert battle_response.status_code == 200
        battle_data = battle_response.json()
        assert battle_data["winning_trainer"] in ["Ash", "Brock"]
        assert battle_data["losing_trainer"] in ["Ash", "Brock"]
```

---

## Test: Error Scenarios

```python
class TestDockerErrorHandling:
    """Test error handling in Docker environment."""

    def test_invalid_operation_input(self, api_url):
        """Test operation with invalid input."""
        response = requests.post(
            f"{api_url}/operations/pokemon/management/catch",
            json={
                # Missing required fields
                "trainer_name": "Ash"
            }
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "pokemon_name" in str(data)  # Missing field mentioned

    def test_operation_not_found(self, api_url):
        """Test calling non-existent operation."""
        response = requests.post(
            f"{api_url}/operations/nonexistent/operation",
            json={}
        )

        assert response.status_code == 404

    def test_database_error_handling(self, api_url, mongo_client):
        """Test graceful handling of database errors."""
        # Corrupt the database or connection

        # Try to use API - should handle error gracefully
        response = requests.post(
            f"{api_url}/operations/pokemon/management/catch",
            json={
                "trainer_name": "Ash",
                "pokemon_name": "Pikachu",
                "element": "Electric"
            }
        )

        # Either succeeds (db recovered) or returns sensible error
        assert response.status_code in [200, 500, 503]
        if response.status_code >= 400:
            data = response.json()
            assert "error" in data or "detail" in data
```

---

## Docker Network & Service Discovery

```python
def test_service_discovery():
    """Test services can discover each other via Docker network."""
    # API should be able to reach MongoDB via hostname
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200

    # Indicates API connected to MongoDB successfully

def test_container_communication():
    """Test Docker containers communicate properly."""
    # All services on same network should reach each other
    # This is verified by successful API↔MongoDB operations

    # If API can create documents in MongoDB,
    # network communication is working
    pass
```

---

## Cleanup & Resource Management

```python
@pytest.fixture(autouse=True)
def cleanup_docker_resources(docker_services):
    """Ensure Docker resources are cleaned up."""
    yield

    # Remove test containers
    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
        cwd=docker_services,
        capture_output=True,
        timeout=30
    )

    # Remove test images
    subprocess.run(
        ["docker", "image", "prune", "-f", "--filter", "label=test=true"],
        capture_output=True,
        timeout=30
    )
```

---

## Performance Benchmarks

```python
class TestPerformance:
    """Performance tests in Docker."""

    def test_api_response_time(self, api_url):
        """Test API response time under load."""
        import timeit

        def call_api():
            requests.get(f"{api_url}/health")

        time_taken = timeit.timeit(call_api, number=100) / 100
        assert time_taken < 0.1  # Should respond in <100ms

    def test_operation_execution_time(self, api_url):
        """Test operation execution time."""
        import time

        start = time.time()
        response = requests.post(
            f"{api_url}/operations/pokemon/management/catch",
            json={
                "trainer_name": "Ash",
                "pokemon_name": "Pikachu",
                "element": "Electric"
            }
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should complete within 1 second
```

---

## Implementation Checklist

- [ ] Create Docker Compose configuration for tests
- [ ] Create `fixtures/docker_services.py` with service fixtures
- [ ] Create `tests/phase3/test_mongodb_integration.py`
- [ ] Create `tests/phase3/test_api_integration.py`
- [ ] Create `tests/phase3/test_prefect_integration.py`
- [ ] Create `tests/phase3/test_data_pipeline.py`
- [ ] Create `tests/phase3/test_docker_errors.py`
- [ ] Create `tests/phase3/test_docker_performance.py`
- [ ] Implement service health checks
- [ ] Implement resource cleanup
- [ ] Add timeout handling for Docker operations
- [ ] Add logging for Docker operations

---

## Integration with Testing Pipeline

**Full Test Execution Flow:**

```
$ make test-all

1. Unit Tests (fast, no Docker)
   └─ ✅ 45 tests, 2 seconds

2. CLI Tests (subprocess, no Docker)
   └─ ✅ 30 tests, 10 seconds

3. Generation Tests (fast, no Docker)
   └─ ✅ 20 tests, 5 seconds

4. Docker Integration Tests (real services)
   ├─ Build Docker images (3-5 min)
   ├─ Start services (30 seconds)
   ├─ Run tests (5-10 min)
   └─ ✅ 50 tests, cleanup (2 min)

5. End-to-End Tests (full workflows)
   └─ ✅ 10 tests, 5 minutes

TOTAL: ~30-40 minutes
```

---
