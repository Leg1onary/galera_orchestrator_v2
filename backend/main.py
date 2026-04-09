import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from routers import (
    auth_router,
    clusters_router,
    diagnostics_router,
    maintenance_router,
    nodes_router,
    recovery_router,
    settings_router,
    ws_router,
)
from services.poller import start_poller, stop_poller

logger = logging.getLogger(__name__)

# ── Lifespan (replaces @app.on_event) ─────────────────────────────────────────
# Combines init_db() (sync) and poller start/stop (async) in one place.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    init_db()          # synchronous — creates tables + seeds contours/settings
    start_poller()     # schedules asyncio background task
    logger.info("Galera Orchestrator v2 started")

    yield  # application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    stop_poller()
    logger.info("Galera Orchestrator v2 stopped")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Galera Orchestrator v2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── API routers ───────────────────────────────────────────────────────────────

app.include_router(auth_router,        prefix="/api")
app.include_router(clusters_router)    # у него prefix="/api/clusters" уже внутри
app.include_router(nodes_router,       prefix="/api")
app.include_router(settings_router,    prefix="/api")
app.include_router(diagnostics_router, prefix="/api")
app.include_router(recovery_router,    prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(ws_router)

# Phase 2+ routers added here:
# from routers import clusters, nodes, settings_router, recovery, maintenance, diagnostics
# app.include_router(clusters.router, prefix="/api", tags=["clusters"])

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