"""
PathPilot Single-Process Entrypoint
Runs FastAPI with Uvicorn, serving both the REST API and the built React frontend.
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    load_dotenv(BASE_DIR / ".env")
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print("=" * 60)
    print("Starting PathPilot Single-Process Server")
    print(f"URL: http://{host}:{port}")
    print(f"API Docs: http://{host}:{port}/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)

