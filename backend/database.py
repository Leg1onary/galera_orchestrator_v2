import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import Connection, create_engine, text

from config import settings
from models import metadata

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
# check_same_thread=False required for SQLite when FastAPI uses a threadpool.
# Per ТЗ раздел 2: БД хранится в /data/orchestrator.db (Docker volume).
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set True for SQL debug logging
)


# ── Public entrypoint ─────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables and seed required initial data.

    Called once at application startup (synchronously, from @app.on_event).
    Safe to call multiple times — CREATE IF NOT EXISTS + INSERT OR IGNORE.

    Seeds:
      - contours: 'test', 'prod'  (per ТЗ раздел 2.1)
      - system_settings: single row with defaults  (per ТЗ раздел 2.7)
    """
    logger.info("Initialising database at %s", settings.DATABASE_URL)

    # Create all tables defined in models.py
    metadata.create_all(engine)
    logger.info("Tables created (or already exist)")

    with engine.begin() as conn:
        _seed_contours(conn)
        _seed_system_settings(conn)

    logger.info("Database initialisation complete")


# ── Connection dependency ─────────────────────────────────────────────────────

@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """
    Context manager for a single transactional connection.

    Usage in routers via FastAPI Depends:
        def some_endpoint(conn = Depends(get_connection)):
            ...

    engine.begin() opens a transaction that auto-commits on exit
    and auto-rolls back on exception.
    """
    with engine.begin() as conn:
        yield conn


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_contours(conn) -> None:
    """
    Seed the two canonical contours per ТЗ раздел 2.1.
    Uses INSERT OR IGNORE so re-runs are safe.
    """
    conn.execute(
        text("INSERT OR IGNORE INTO contours (name) VALUES (:name)"),
        [{"name": "test"}, {"name": "prod"}],
    )
    logger.debug("Contours seeded (INSERT OR IGNORE)")


def _seed_system_settings(conn) -> None:
    """
    Seed a single system_settings row with ТЗ defaults if the table is empty.

    Per ТЗ раздел 2.7:
      polling_interval_sec  = 5
      event_log_limit       = 200
      timezone              = 'UTC'
    """
    row = conn.execute(text("SELECT COUNT(*) FROM system_settings")).scalar()
    if row == 0:
        conn.execute(
            text(
                """
                INSERT INTO system_settings
                    (polling_interval_sec, event_log_limit, timezone, updated_at)
                VALUES
                    (:polling_interval_sec, :event_log_limit, :timezone, :updated_at)
                """
            ),
            {
                "polling_interval_sec": 5,
                "event_log_limit": 200,
                "timezone": "UTC",
                "updated_at": datetime.utcnow(),
            },
        )
        logger.debug("system_settings seeded with defaults")
    else:
        logger.debug("system_settings already has data, skipping seed")