# Pulpo Framework Test Suite

Comprehensive test suite for the Pulpo framework using todo-app as test fixtures.

## 📋 Overview

This test suite validates the Pulpo framework's core functionality:
- **Model discovery** - @datamodel decorator registration
- **Operation discovery** - @operation decorator registration
- **Registry system** - ModelRegistry and OperationRegistry
- **Graph building** - RegistryGraph construction from registries
- **Validation** - Graph validation (cycles, orphans, etc.)
- **Persistence** - Save/load graph functionality
- **Export** - Mermaid and DOT diagram generation

## 🏗️ Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── fixtures/                # Test data (extracted from todo-app patterns)
│   ├── sample_models.py    # Sample DataModel definitions
│   ├── sample_operations.py # Sample Operation definitions
│   └── expected_outputs/   # Expected generated code (future)
├── unit/                    # Unit tests for individual components
│   ├── test_decorators.py  # @datamodel and @operation tests
│   ├── test_registries.py  # ModelRegistry/OperationRegistry tests
│   └── test_graph_builder.py # Graph building tests
└── integration/             # Integration tests
    └── test_full_workflow.py # End-to-end workflow tests
```

## 🎯 Test Categories

### Unit Tests (`tests/unit/`)

Test individual framework components in isolation:

- **test_decorators.py** - Decorator functionality
  - `@datamodel` registration
  - `@operation` registration
  - Metadata extraction
  - Class/function preservation

- **test_registries.py** - Registry operations
  - Model registration and retrieval
  - Operation registration and retrieval
  - Category filtering
  - Registry independence

- **test_graph_builder.py** - Graph construction
  - Building graphs from registries
  - Node creation (DataModel, Task, Flow)
  - Edge creation (relationships)
  - Metadata preservation

### Integration Tests (`tests/integration/`)

Test complete workflows using real patterns:

- **test_full_workflow.py** - End-to-end testing
  - Import sample models/operations
  - Build graph from fixtures
  - Validate graph structure
  - Save/load persistence
  - Export to Mermaid/DOT
  - Complete pipeline validation

## 🚀 Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov mongomock-motor

# Or install from requirements
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run complete test suite
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run with detailed output
pytest -vv
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# Specific test file
pytest tests/unit/test_decorators.py

# Specific test class
pytest tests/unit/test_registries.py::TestModelRegistry

# Specific test function
pytest tests/unit/test_decorators.py::TestDatamodelDecorator::test_basic_datamodel_registration

# Tests matching pattern
pytest -k "registry"
```

### Filter by Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Tests requiring todo-app
pytest -m requires_todo_app
```

## 🔧 Fixtures

The test suite provides comprehensive fixtures via `conftest.py`:

### Path Fixtures

- `framework_root` - Path to Pulpo framework root
- `fixtures_dir` - Path to test fixtures directory
- `todo_app_path` - Extracted todo-app (session-scoped)
- `temp_project_dir` - Temporary project directory (test-scoped)

### Data Fixtures

- `mock_model_metadata` - Mock metadata for a simple model
- `mock_operation_metadata` - Mock metadata for a simple operation
- `sample_models_module` - Import path to sample models
- `sample_operations_module` - Import path to sample operations

### Sample Data Fixtures

- `sample_markdown_tasks` - Markdown with checkboxes
- `sample_json_tasks` - JSON task array
- `sample_code_with_todos` - Code with TODO/FIXME comments

### Database Fixtures

- `mock_db` - MongoDB mock for testing (async)
- `clean_db` - Clean database for each test

### Auto Fixtures

- `reset_registries` - Automatically clears registries before/after each test (ensures isolation)

## 📝 Writing Tests

### Basic Test Structure

```python
import pytest
from core.analysis.registries import ModelRegistry

@pytest.mark.unit
def test_my_feature():
    """Test description."""
    # Given: Setup
    ModelRegistry.register("Test", {"name": "Test"})

    # When: Action
    result = ModelRegistry.get("Test")

    # Then: Assertion
    assert result["name"] == "Test"
```

### Using Fixtures

```python
@pytest.mark.unit
def test_with_fixtures(mock_model_metadata, temp_project_dir):
    """Test using fixtures."""
    # mock_model_metadata is ready to use
    ModelRegistry.register("Model", mock_model_metadata)

    # temp_project_dir is a Path to temporary directory
    test_file = temp_project_dir / "test.json"
    test_file.write_text('{"test": true}')

    assert test_file.exists()
```

### Integration Test Example

```python
import importlib
import pytest
from core.analysis.graph_builder import build_graph_from_registries

@pytest.mark.integration
def test_full_workflow(sample_models_module, sample_operations_module):
    """Test complete workflow."""
    # Import fixtures (registers models/operations)
    importlib.import_module(sample_models_module)
    importlib.import_module(sample_operations_module)

    # Build graph
    graph = build_graph_from_registries("test-project")

    # Validate
    is_valid, errors, warnings = graph.validate()
    assert is_valid or len(errors) == 0
```

## 🎯 Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit              # Unit test
@pytest.mark.integration       # Integration test
@pytest.mark.slow              # Takes > 1 second
@pytest.mark.requires_todo_app # Needs todo-app fixture
```

## 🔍 Coverage

Check test coverage:

```bash
# Generate coverage report
pytest --cov=core --cov-report=html

# Open HTML report
open htmlcov/index.html

# Coverage with missing lines
pytest --cov=core --cov-report=term-missing
```

## 🎓 Best Practices

### Test Isolation

✅ **Do:**
- Tests clean up after themselves (automatic via `reset_registries`)
- Use temporary directories for file operations
- Each test is independent

❌ **Don't:**
- Rely on test execution order
- Modify shared state without cleanup
- Use absolute paths outside temp directories

### Separation of Concerns

✅ **Do:**
- Tests belong in framework (`pulpo/tests/`)
- Fixtures are copies of patterns (not imports from examples/)
- Test framework behavior, not project specifics

❌ **Don't:**
- Modify example projects during tests
- Import directly from examples/ (except via fixtures)
- Test project-specific logic in framework tests

### Descriptive Tests

✅ **Do:**
- Use descriptive test names: `test_register_model_stores_in_registry`
- Include docstrings explaining what is tested
- Follow Given/When/Then pattern in test body

❌ **Don't:**
- Generic names: `test_1`, `test_stuff`
- Missing documentation
- Complex test logic without comments

## 📊 Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest --cov=core --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 🐛 Debugging Tests

```bash
# Run with pdb on failure
pytest --pdb

# Stop after first failure
pytest -x

# Show print statements
pytest -s

# More verbose output
pytest -vv --showlocals

# Run last failed tests
pytest --lf

# Run failed tests first, then rest
pytest --ff
```

## 📖 Related Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Pulpo Architecture](../docs/03_Architecture.md)
- [Clean Code Refactoring](../REFACTORING_CLEAN_CODE.md)

## 🤝 Contributing

When adding new framework features:

1. **Write tests first** (TDD approach)
2. **Add fixtures** if new patterns needed
3. **Update this README** if new test categories added
4. **Ensure coverage** stays above 80%
5. **Run full suite** before committing

```bash
# Before committing
pytest --cov=core --cov-report=term-missing -v
```

## ✅ Current Coverage

```
Component                Coverage
core/analysis/decorators    95%
core/analysis/registries    100%
core/analysis/graph_builder 85%
core/generation/*           (pending)
```

*Run `pytest --cov` to see latest coverage report*
