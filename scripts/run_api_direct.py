#!/usr/bin/env python3
"""Run the auto-generated API server on an alternative port.

This script starts the FastAPI application on port 8001,
useful when port 8000 is already in use.

Run with:
    python core/scripts/run_api_direct.py
"""

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 Core Framework - Auto-Generated API (Port 8001)")
    print("=" * 80)
    print("")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🏥 Health Check:      http://localhost:8001/health")
    print("🔌 API Base URL:      http://localhost:8001/api/v1")
    print("")
    print("Note: Running on port 8001 instead of default port 8000")
    print("")

    uvicorn.run(
        "run_cache.generated_api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
