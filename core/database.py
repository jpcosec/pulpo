"""Database connection utilities for JobHunter AI.

This module provides database initialization and connection management for MongoDB.
"""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from core.utils.config import get_settings

# Global database instance
_database_client: AsyncIOMotorClient | None = None


async def init_database():
    """Initialize Beanie with all registered models.

    This function should be called at application startup to:
    1. Connect to MongoDB
    2. Initialize Beanie ODM
    3. Register all Document models
    4. Create indexes

    Returns:
        Database instance
    """
    global _database_client

    settings = get_settings()

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db_name = settings.mongodb_database

    _database_client = client
    database = client[db_name]

    # Initialize Beanie with models from user projects only
    # Core layer does not define any models
    await init_beanie(
        database=database,
        document_models=[],
    )

    return database


def get_database():
    """Get the database instance.

    Returns:
        Database instance (Motor database)

    Note: This is a synchronous function that returns the database handle.
          You must call init_database() first (async).
    """
    if _database_client is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    settings = get_settings()
    return _database_client[settings.mongodb_database]


def get_database_client():
    """Get the database client instance.

    Returns:
        AsyncIOMotorClient instance

    Note: This is a synchronous function that returns the client handle.
          You must call init_database() first (async).
    """
    if _database_client is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return _database_client


async def close_database():
    """Close database connection."""
    global _database_client
    if _database_client is not None:
        _database_client.close()
        _database_client = None
