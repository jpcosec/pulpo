#!/usr/bin/env python3
"""Run the auto-generated API server on port 8001 without hot reload.

This script is useful for:
- Running tests against the API
- Avoiding reload issues during testing
- Running on an alternative port

Run with:
    python core/scripts/run_api_test_port.py
"""

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 Core Framework - Auto-Generated API (Test Mode, Port 8001)")
    print("=" * 80)
    print("")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🏥 Health Check:      http://localhost:8001/health")
    print("🔌 API Base URL:      http://localhost:8001/api/v1")
    print("")
    print("Note: Hot reload is disabled for testing stability")
    print("")

    uvicorn.run(
        "run_cache.generated_api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
