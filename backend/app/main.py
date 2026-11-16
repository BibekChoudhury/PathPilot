from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .db import init_db
from .routes import router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="PathPilot API",
    description="Student Recovery Agent for JEE Physics Micro-Skills",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def validate_browser_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if (request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}
            and origin and origin != f"{request.url.scheme}://{request.url.netloc}"):
        return JSONResponse(status_code=403, content={"detail": "Cross-origin request rejected"})
    return await call_next(request)


# Include API router
app.include_router(router)


# Optional Frontend Static Files mount for standalone deployment
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if (FRONTEND_DIST / "index.html").is_file() and (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't hijack API routes
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        return FileResponse(FRONTEND_DIST / "index.html")
