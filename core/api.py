"""FastAPI application using auto-generated routes.

This demonstrates the generated API code in action.
"""

# Import generated routes
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to path so we can import from .run_cache
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, cleanup on shutdown."""
    # Startup
    print("🚀 Starting API server...")

    # Connect to MongoDB (support both Docker and local)
    import os

    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "jobhunter")

    client = AsyncIOMotorClient(mongodb_url)
    database = client[mongodb_database]

    # Initialize Beanie with models
    # Note: No core models - use generated API for user models
    await init_beanie(
        database=database,
        document_models=[],
    )
    print("✓ Connected to MongoDB")
    print("✓ Initialized Beanie")

    yield

    # Shutdown
    print("🛑 Shutting down API server...")
    client.close()


# Create FastAPI app
app = FastAPI(
    title="JobHunter API",
    description="Auto-generated API from @datamodel decorators",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jobhunter-api",
        "version": "0.1.0",
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "JobHunter API - Auto-generated from @datamodel decorators",
        "docs": "/docs",
        "health": "/health",
        "models": "See generated API routes",
        "endpoints": {
            "generated_routes": "/api/v1/*",
            "operations": "/operations/*",
        },
    }


# Import and include generated routes
try:
    # Add .run_cache to sys.path so we can import generated_api
    run_cache_path = Path(__file__).parent.parent.parent / ".run_cache"

    if not run_cache_path.exists():
        raise FileNotFoundError(f"Generated API directory not found at: {run_cache_path}")

    if not (run_cache_path / "generated_api.py").exists():
        raise FileNotFoundError(
            f"Generated API file not found at: {run_cache_path / 'generated_api.py'}"
        )

    # Add .run_cache to path and import
    sys.path.insert(0, str(run_cache_path))
    import generated_api

    # Include all auto-generated CRUD routes
    app.include_router(generated_api.setup_routes())
    print("✓ Loaded auto-generated routes from .run_cache/generated_api.py")

except (ImportError, FileNotFoundError) as e:
    print("⚠️  Warning: Generated routes not found!")
    print(f"   Error: {e}")
    print("   Run: make compile")
    print("")
    print("   Routes will not be available until you run code generation.")


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("JobHunter API - Auto-Generated Routes Demo")
    print("=" * 80)
    print("")
    print("Starting server...")
    print("")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["core", ".run_cache"],
    )
