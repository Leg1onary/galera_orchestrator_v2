import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Абсолютные импорты — backend запускается как flat-пакет из /backend/,
# поэтому config.py и database.py находятся в sys.path напрямую.
from config import settings
from database import engine, init_db
from routers import auth as auth_router

logger = logging.getLogger(__name__)

# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Galera Orchestrator v2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup() -> None:
    """
    Synchronous startup hook.

    init_db() uses SQLAlchemy Core with a synchronous engine — no await needed.
    Calling it here guarantees tables + seed data exist before the first request.
    """
    init_db()


# ── API routers ───────────────────────────────────────────────────────────────
# Все роутеры регистрируются ДО static mount и SPA fallback.

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])

# Phase 1+ routers (добавлять здесь по мере реализации):
# from routers import clusters, nodes, settings, recovery, maintenance, diagnostics, ws
# app.include_router(clusters.router, prefix="/api", tags=["clusters"])


# ── Static assets ─────────────────────────────────────────────────────────────
# Монтируем /assets (хэшированные JS/CSS бандлы Vite) без html=True.
# html=True вызывает SPA-fallback внутри Starlette и ломает /api/* — см. фикс выше.

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="assets",
        )

# ── SPA fallback ──────────────────────────────────────────────────────────────
# Catch-all ДОЛЖЕН быть последним маршрутом.
# Исключаем все non-SPA префиксы явно.

_SPA_EXCLUDED_PREFIXES = (
    "/api/",
    "/ws/",
    "/docs",
    "/redoc",
    "/openapi.json",
)

INDEX_HTML = STATIC_DIR / "index.html"


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def spa_fallback(request: Request, full_path: str) -> Response:
    """
    SPA fallback — отдаёт index.html для всех маршрутов Vue Router.
    Не перехватывает /api/*, /ws/*, /docs, /redoc, /openapi.json.
    """
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