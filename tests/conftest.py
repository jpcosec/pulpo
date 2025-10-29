"""Pytest configuration and shared fixtures for framework tests.

This module provides generic fixtures for testing the JobHunter Core Framework:
- Database setup/teardown for testing
- Async test support
- Mock database client

Application-specific test fixtures should be defined in application tests.
"""

import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

# Add parent directory to path so tests can import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Async event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures - Generic for any models


@pytest_asyncio.fixture
async def mock_db(request: pytest.FixtureRequest) -> AsyncGenerator[AsyncMongoMockClient, None]:
    """Provide mock MongoDB client for testing.

    To use with specific models, pass document_models as a fixture parameter.
    Default: empty database (no models initialized).

    Example usage in tests:
        @pytest.mark.asyncio
        async def test_something(mock_db):
            # mock_db is ready to use
            pass
    """
    client = AsyncMongoMockClient()
    db = client.get_database("test_core_framework")

    # Get document models from test marker if specified
    # Otherwise, initialize with empty database
    marker = request.node.get_closest_marker("models")
    models = marker.args[0] if marker else []

    if models:
        await init_beanie(
            database=db,
            document_models=models,
        )

    yield client

    # Cleanup
    await client.drop_database("test_core_framework")
    client.close()


@pytest_asyncio.fixture
async def clean_db(mock_db: AsyncMongoMockClient) -> AsyncGenerator[None, None]:
    """Provide clean database for each test."""
    yield

    # Cleanup after test
    db = mock_db.get_database("test_core_framework")
    for collection_name in await db.list_collection_names():
        await db.drop_collection(collection_name)
