from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import init_db
from routers import (
    auth_router,
    clusters_router,
    contours_router,
    diagnostics_router,
    maintenance_router,
    nodes_router,
    recovery_router,
    settings_router,
    ws_router,
)
from services.poller import start_poller, stop_poller

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_poller()
    logger.info("Galera Orchestrator v2 started")
    yield
    stop_poller()
    logger.info("Galera Orchestrator v2 stopped")


app = FastAPI(
    title="Galera Orchestrator v2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Rate limiter (slowapi) ────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (dev only) ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(auth_router,        prefix="/api")
app.include_router(diagnostics_router, prefix="/api")
app.include_router(recovery_router,    prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(clusters_router,    prefix="/api")
app.include_router(nodes_router,       prefix="/api")
app.include_router(contours_router,    prefix="/api")
app.include_router(settings_router,    prefix="/api")
app.include_router(ws_router)

# ── Static assets ─────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# ── SPA fallback ──────────────────────────────────────────────────────────────

_SPA_EXCLUDED_PREFIXES = (
    "/api/",
    "/ws/",
    "/assets/",
    "/docs",
    "/redoc",
    "/openapi.json",
)

INDEX_HTML = STATIC_DIR / "index.html"


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str, request: Request):
    path = request.url.path

    for prefix in _SPA_EXCLUDED_PREFIXES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return JSONResponse(
                status_code=404,
                content={"detail": f"Not found: {path}", "path": path},
            )

    if not INDEX_HTML.is_file():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend not built. Run `npm run build` in /frontend.",
                "hint": "In development use `npm run dev` and Vite proxy.",
            },
        )

    return FileResponse(
        path=str(INDEX_HTML),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
