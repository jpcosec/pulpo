"""Pytest configuration and shared fixtures for framework tests.

This module provides generic fixtures for testing the Pulpo Core Framework:
- Database setup/teardown for testing
- Async test support
- Mock database client
- Test project fixtures (todo-app)
- Sample data fixtures
- Registry cleanup

Application-specific test fixtures should be defined in application tests.
"""

import asyncio
import sys
import shutil
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
# Database fixtures commented out until cryptography dependencies resolved
# Uncomment when running database/async tests
# import pytest_asyncio
# from beanie import init_beanie
# from mongomock_motor import AsyncMongoMockClient

# Add parent directory to path so tests can import core modules
FRAMEWORK_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(FRAMEWORK_ROOT))


# Async event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures - Commented out until dependencies resolved
# Uncomment when running async/database tests

# @pytest_asyncio.fixture
# async def mock_db(request: pytest.FixtureRequest) -> AsyncGenerator[AsyncMongoMockClient, None]:
#     """Provide mock MongoDB client for testing."""
#     client = AsyncMongoMockClient()
#     db = client.get_database("test_core_framework")
#     marker = request.node.get_closest_marker("models")
#     models = marker.args[0] if marker else []
#     if models:
#         await init_beanie(database=db, document_models=models)
#     yield client
#     await client.drop_database("test_core_framework")
#     client.close()

# @pytest_asyncio.fixture
# async def clean_db(mock_db: AsyncMongoMockClient) -> AsyncGenerator[None, None]:
#     """Provide clean database for each test."""
#     yield
#     db = mock_db.get_database("test_core_framework")
#     for collection_name in await db.list_collection_names():
#         await db.drop_collection(collection_name)


# New fixtures for Pulpo framework testing

@pytest.fixture(scope="session")
def framework_root() -> Path:
    """Get framework root directory."""
    return FRAMEWORK_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Get fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def todo_app_path(tmp_path_factory) -> Path:
    """Extract todo-app to temporary directory for testing.

    This fixture:
    1. Extracts examples/todo-app.tar.gz to temp location
    2. Returns path to extracted directory
    3. Cleans up after session
    """
    # Create temp directory for this session
    temp_dir = tmp_path_factory.mktemp("todo-app-test")

    # Extract todo-app
    import tarfile
    tar_path = FRAMEWORK_ROOT / "examples" / "todo-app.tar.gz"

    if tar_path.exists():
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(temp_dir)

        # Return path to extracted todo-app
        extracted_path = temp_dir / "todo-app"
        if extracted_path.exists():
            return extracted_path

    # If extraction failed, create empty dir
    empty_dir = temp_dir / "todo-app"
    empty_dir.mkdir(exist_ok=True)
    return empty_dir


@pytest.fixture
def temp_project_dir(tmp_path) -> AsyncGenerator[Path, None]:
    """Create temporary project directory for tests.

    Yields:
        Path to temporary project directory

    Cleanup:
        Removes directory after test
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    yield project_dir

    # Cleanup
    if project_dir.exists():
        shutil.rmtree(project_dir)


@pytest.fixture(autouse=True)
def reset_registries():
    """Reset model and operation registries before each test.

    This ensures test isolation - each test starts with clean registries.
    """
    from core.analysis.registries import ModelRegistry, OperationRegistry

    # Clear registries before test
    ModelRegistry.clear()
    OperationRegistry.clear()

    yield

    # Clear registries after test (cleanup)
    ModelRegistry.clear()
    OperationRegistry.clear()


@pytest.fixture
def sample_models_module() -> str:
    """Get import path to sample models fixture."""
    return "tests.fixtures.sample_models"


@pytest.fixture
def sample_operations_module() -> str:
    """Get import path to sample operations fixture."""
    return "tests.fixtures.sample_operations"


@pytest.fixture
def mock_model_metadata() -> dict:
    """Mock metadata for a simple model.

    Returns:
        Dict with model metadata structure
    """
    return {
        "name": "TestModel",
        "class_name": "TestModel",
        "module": "test.models",
        "description": "Test model for unit tests",
        "tags": ["test"],
        "fields": {
            "id": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
            "value": {"type": "int", "required": False, "default": 0}
        },
        "searchable_fields": ["name"],
        "readonly_fields": ["id"]
    }


@pytest.fixture
def mock_operation_metadata() -> dict:
    """Mock metadata for a simple operation.

    Returns:
        Dict with operation metadata structure
    """
    return {
        "name": "test.operation.simple",
        "full_name": "test.operation.simple",
        "function_name": "simple_operation",
        "module": "test.operations",
        "description": "Test operation",
        "category": "test",
        "inputs": {"type": "object"},
        "outputs": {"type": "object"},
        "models_in": ["TestModel"],
        "models_out": ["TestModel"],
        "async": True,
        "tags": ["test"]
    }


@pytest.fixture
def sample_markdown_tasks() -> str:
    """Sample Markdown with checkboxes for testing loaders."""
    return """
# My Tasks

- [ ] Buy groceries
- [x] Complete report
- [ ] Review pull request
- [x] Update documentation
- [ ] Fix bug in authentication
"""


@pytest.fixture
def sample_json_tasks() -> str:
    """Sample JSON tasks for testing loaders."""
    return """[
    {
        "title": "Task 1",
        "description": "First task",
        "importance_rate": 4,
        "status": "pending"
    },
    {
        "title": "Task 2",
        "description": "Second task",
        "importance_rate": 2,
        "status": "in_progress"
    }
]"""


@pytest.fixture
def sample_code_with_todos() -> str:
    """Sample code with TODO/FIXME comments."""
    return """
def process_data(data):
    # TODO: Add validation for input data
    result = []
    for item in data:
        # FIXME: This fails for empty items
        result.append(item.upper())
    return result

# TODO: Implement error handling
# FIXME: Memory leak in batch processing
"""


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring multiple components"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take more than 1 second"
    )
    config.addinivalue_line(
        "markers", "requires_todo_app: Tests that require todo-app fixture"
    )
