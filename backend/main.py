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
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
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
    version_router,
    ws_router,
)
from services.poller import start_poller, stop_poller

logger = logging.getLogger(__name__)


# ── Security Headers Middleware (SEC-005) ─────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to every HTTP response.
    WebSocket upgrade requests are excluded automatically —
    Starlette does not call this middleware for WS connections.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), usb=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_poller()
    logger.info("Galera Orchestrator v2 started")
    yield
    stop_poller()
    logger.info("Galera Orchestrator v2 stopped")


# ── FastAPI app (SEC-006: docs disabled in prod by default) ──────────────────
app = FastAPI(
    title="Galera Orchestrator v2",
    version="2.0.0",
    docs_url="/docs"     if settings.DOCS_ENABLED else None,
    redoc_url="/redoc"   if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
    lifespan=lifespan,
)

# ── Rate limiter (slowapi) ──────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security headers ──────────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── CORS (dev only) ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ─────────────────────────────────────────────────────────────
app.include_router(auth_router,        prefix="/api")
app.include_router(diagnostics_router, prefix="/api")
app.include_router(recovery_router,    prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(clusters_router,    prefix="/api")
app.include_router(nodes_router,       prefix="/api")
app.include_router(contours_router,    prefix="/api")
app.include_router(settings_router,    prefix="/api")
app.include_router(version_router,     prefix="/api")
app.include_router(ws_router)

# ── Static assets ───────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# ── SPA fallback ────────────────────────────────────────────────────────────────

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
