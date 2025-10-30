# CLI Subprocess Testing Strategy

**Date:** 2025-10-30
**Status:** Testing Clarification
**Scope:** Proper CLI testing using subprocess and actual commands

---

## User Feedback Summary

**Key Requirements:**
1. "CLI is a command line interface, please make sure that the test is running using the command line, not python calls"
2. "use subprocess.run, if the package is not installed, it should be installed"
3. "There's no need to mock anything" (for integration tests)

---

## Testing Approach

### Principle 1: Use subprocess.run() for CLI Testing

**DON'T DO THIS:**
```python
# ❌ Wrong: Testing Python functions directly
from core.cli.main import main

def test_cli_catch():
    result = main(["pokemon", "management", "catch", "--input", {...}])
    assert result.success
```

**DO THIS:**
```python
# ✅ Correct: Test via actual CLI command
import subprocess

def test_cli_catch():
    result = subprocess.run(
        ["pulpo", "pokemon", "management", "catch", "--input", '{...}'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

### Principle 2: Auto-Install Package if Missing

Tests should ensure the package is installed before running CLI tests:

```python
import subprocess
import sys
import pytest

@pytest.fixture(scope="session", autouse=True)
def ensure_package_installed():
    """Auto-install pulpo-core if not already installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )

    if "pulpo-core" not in result.stdout:
        # Install the package in editable mode from current directory
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd="/home/jp/pulpo",
            check=True
        )
```

### Principle 3: Test Real CLI Commands

All CLI testing should invoke actual command-line interface:

```python
def test_pulpo_init():
    """Test that 'pulpo cli init' creates Dockerfile."""
    result = subprocess.run(
        ["pulpo", "cli", "init"],
        cwd="/tmp/test-project",
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert Path("/tmp/test-project/docker/Dockerfile").exists()
    assert Path("/tmp/test-project/Makefile").exists()

def test_pulpo_compile():
    """Test that 'pulpo compile' generates code."""
    result = subprocess.run(
        ["pulpo", "compile"],
        cwd="/tmp/test-project",
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert Path("/tmp/test-project/.run_cache/generated_api.py").exists()

def test_pulpo_up_down():
    """Test service startup and shutdown."""
    # Start services
    up_result = subprocess.run(
        ["pulpo", "up"],
        cwd="/tmp/test-project",
        capture_output=True,
        text=True,
        timeout=120
    )
    assert up_result.returncode == 0

    # Verify services running (see Docker testing strategy)
    # ...

    # Stop services
    down_result = subprocess.run(
        ["pulpo", "down"],
        cwd="/tmp/test-project",
        capture_output=True,
        text=True
    )
    assert down_result.returncode == 0
```

---

## CLI Command Examples

### Service Management

```bash
# Initialize project with infrastructure
pulpo cli init
# Generates: Dockerfile, docker-compose.yml, .env, Makefile

# Start services
pulpo up
# Starts: MongoDB, API, UI, Prefect

# Stop services
pulpo down
# Stops all services

# Check service status
pulpo health
# Shows: API status, MongoDB status, Prefect status

# View logs
pulpo logs api
pulpo logs mongodb
pulpo logs prefect
```

### Code Generation

```bash
# Compile decorators to code
pulpo compile
# Generates: API routes, CLI commands, UI config, Prefect flows

# Discover operations
pulpo discover
# Lists all @operation and @datamodel decorators
```

### Operations

```bash
# Run a specific operation via CLI
pulpo pokemon management catch --input '{"trainer_name":"Ash","pokemon_name":"Pikachu","element":"Electric"}'

# Run operation via API
curl -X POST http://localhost:8000/operations/pokemon/management/catch \
  -H "Content-Type: application/json" \
  -d '{"trainer_name":"Ash","pokemon_name":"Pikachu","element":"Electric"}'

# List all operations
pulpo ops list
```

### Database Management

```bash
# Initialize database
pulpo db init

# Check database status
pulpo db status

# Access MongoDB shell
pulpo db shell

# Drop database
pulpo db drop
```

---

## Test Fixtures for CLI Testing

### Project Creation Fixture

```python
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def test_project_dir():
    """Create a temporary test project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test-project"
        project_dir.mkdir()

        # Extract demo project
        import tarfile
        with tarfile.open("/home/jp/pulpo/core/demo-project.tar.gz") as tar:
            tar.extractall(project_dir)

        yield project_dir

        # Cleanup
        shutil.rmtree(project_dir, ignore_errors=True)
```

### Initialized Project Fixture

```python
@pytest.fixture
def initialized_project(test_project_dir):
    """Create and initialize a test project."""
    result = subprocess.run(
        ["pulpo", "cli", "init"],
        cwd=test_project_dir,
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to initialize project: {result.stderr}")

    yield test_project_dir
```

### Compiled Project Fixture

```python
@pytest.fixture
def compiled_project(initialized_project):
    """Compile a test project."""
    result = subprocess.run(
        ["pulpo", "compile"],
        cwd=initialized_project,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to compile project: {result.stderr}")

    yield initialized_project
```

---

## CLI Test Organization

### Phase 3 Iteration 2: CLI Service Management

```
tests/phase3/test_cli_services.py

✅ test_cli_init_creates_dockerfile
✅ test_cli_init_creates_docker_compose
✅ test_cli_init_creates_makefile
✅ test_cli_init_creates_dotenv
✅ test_cli_discover_finds_operations
✅ test_cli_compile_generates_api
✅ test_cli_compile_generates_cli_config
✅ test_cli_compile_generates_ui_config
✅ test_cli_up_starts_services (via Docker)
✅ test_cli_down_stops_services (via Docker)
✅ test_cli_logs_shows_output
✅ test_cli_health_shows_status
✅ test_cli_operation_execution (via subprocess)
```

### Test Examples

```python
import subprocess
import pytest
from pathlib import Path

class TestCLIInit:
    def test_init_creates_dockerfile(self, test_project_dir):
        """Test: pulpo cli init generates Dockerfile"""
        result = subprocess.run(
            ["pulpo", "cli", "init"],
            cwd=test_project_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, result.stderr
        assert (test_project_dir / "docker" / "Dockerfile").exists()
        assert (test_project_dir / "docker" / "Dockerfile.ui").exists()

    def test_init_creates_docker_compose(self, test_project_dir):
        """Test: pulpo cli init generates docker-compose.yml"""
        result = subprocess.run(
            ["pulpo", "cli", "init"],
            cwd=test_project_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert (test_project_dir / "docker-compose.yml").exists()

    def test_init_creates_makefile(self, test_project_dir):
        """Test: pulpo cli init generates Makefile"""
        result = subprocess.run(
            ["pulpo", "cli", "init"],
            cwd=test_project_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert (test_project_dir / "Makefile").exists()

class TestCLICompile:
    def test_compile_generates_api(self, initialized_project):
        """Test: pulpo compile generates API code"""
        result = subprocess.run(
            ["pulpo", "compile"],
            cwd=initialized_project,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, result.stderr
        assert (initialized_project / ".run_cache" / "generated_api.py").exists()

    def test_compile_idempotent(self, initialized_project):
        """Test: pulpo compile is idempotent"""
        # First compile
        result1 = subprocess.run(
            ["pulpo", "compile"],
            cwd=initialized_project,
            capture_output=True,
            text=True
        )

        # Get hash of generated files
        import hashlib
        def get_dir_hash(directory):
            hasher = hashlib.md5()
            for file in sorted(Path(directory).rglob("*")):
                if file.is_file():
                    hasher.update(file.read_bytes())
            return hasher.hexdigest()

        hash1 = get_dir_hash(initialized_project / ".run_cache")

        # Second compile
        result2 = subprocess.run(
            ["pulpo", "compile"],
            cwd=initialized_project,
            capture_output=True,
            text=True
        )

        hash2 = get_dir_hash(initialized_project / ".run_cache")

        # Should be identical (idempotent)
        assert hash1 == hash2, "Compile generated different output on second run"

class TestCLIDiscover:
    def test_discover_lists_operations(self, test_project_dir):
        """Test: pulpo discover shows all operations"""
        result = subprocess.run(
            ["pulpo", "discover"],
            cwd=test_project_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "pokemon.management.catch" in result.stdout
        assert "pokemon.evolution.stage1" in result.stdout

    def test_discover_shows_models(self, test_project_dir):
        """Test: pulpo discover shows all models"""
        result = subprocess.run(
            ["pulpo", "discover"],
            cwd=test_project_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Pokemon" in result.stdout
        assert "Trainer" in result.stdout
```

---

## Error Handling

### Subprocess Error Handling

```python
def run_cli_command(command, cwd=None, timeout=60):
    """Helper to run CLI command with error handling."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise CLICommandError(
                command=" ".join(command),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

        return result

    except subprocess.TimeoutExpired as e:
        raise CLITimeoutError(f"Command timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise CLINotFoundError(f"Command not found: {command[0]}") from e

class CLICommandError(Exception):
    def __init__(self, command, returncode, stdout, stderr):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"Command failed: {command}\n"
            f"Return code: {returncode}\n"
            f"Stdout: {stdout}\n"
            f"Stderr: {stderr}"
        )
```

---

## Key Differences from Python Testing

| Aspect | Python Testing | CLI Testing |
|--------|----------------|------------|
| **Invocation** | `function()` | `subprocess.run(["command"])` |
| **Environment** | Same process | Subprocess |
| **Exit Code** | Return value | `result.returncode` |
| **Output** | Return value | `result.stdout`, `result.stderr` |
| **Installation** | Already available | Auto-install if needed |
| **Isolation** | Shared state | Process isolation |
| **Timing** | Fast (no subprocess) | Slower (spawn process) |

---

## Implementation Checklist

- [ ] Create `tests/conftest.py` with CLI fixtures
- [ ] Implement `ensure_package_installed()` fixture
- [ ] Implement `test_project_dir` fixture
- [ ] Implement `initialized_project` fixture
- [ ] Implement `compiled_project` fixture
- [ ] Create test classes for each CLI command
- [ ] Implement error handling helpers
- [ ] Add timeout handling for service tests
- [ ] Document expected output formats
- [ ] Create smoke tests (basic functionality)
- [ ] Create integration tests (full workflows)

---

## Next Phase: Docker Integration

Once CLI tests pass, Docker-based integration tests will:
1. Use Docker Compose to start services
2. Test actual API endpoints
3. Test actual MongoDB operations
4. Test actual Prefect flow execution
5. Clean up containers after tests

See: **DOCKER_INTEGRATION_TESTING_STRATEGY.md**

---
