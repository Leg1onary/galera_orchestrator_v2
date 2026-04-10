import logging
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import Connection, create_engine, text

from config import settings
from models import metadata

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


# ── Public entrypoint ─────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables and seed required initial data.
    Safe to call multiple times — CREATE IF NOT EXISTS + INSERT OR IGNORE.
    """
    logger.info("Initialising database at %s", settings.DATABASE_URL)

    metadata.create_all(engine)
    logger.info("Tables created (or already exist)")

    with engine.begin() as conn:
        _migrate_system_settings(conn)
        _seed_contours(conn)
        _seed_system_settings(conn)

    logger.info("Database initialisation complete")


# ── Connection dependency ─────────────────────────────────────────────────────

def get_connection() -> Generator[Connection, None, None]:
    with engine.begin() as conn:
        try:
            yield conn
        except Exception:
            logger.exception("Database error inside request")
            raise


# ── Migrations (additive, safe to re-run) ────────────────────────────────────

def _migrate_system_settings(conn) -> None:
    """
    Добавляет колонки в system_settings если их нет.
    ALTER TABLE IF NOT EXISTS column — SQLite не поддерживает IF NOT EXISTS,
    поэтому проверяем через PRAGMA table_info.
    """
    existing = {
        row[1]
        for row in conn.execute(text("PRAGMA table_info(system_settings)")).fetchall()
    }

    pending = [
        (
            "rolling_restart_timeout_sec",
            "ALTER TABLE system_settings ADD COLUMN rolling_restart_timeout_sec INTEGER NOT NULL DEFAULT 300",
        ),
        # Сюда добавлять новые колонки по мере роста схемы:
        # ("new_column", "ALTER TABLE system_settings ADD COLUMN new_column TEXT"),
    ]

    for col_name, sql in pending:
        if col_name not in existing:
            conn.execute(text(sql))
            logger.info("Migration: added column system_settings.%s", col_name)


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_contours(conn) -> None:
    conn.execute(
        text("INSERT OR IGNORE INTO contours (name) VALUES (:name)"),
        [{"name": "test"}, {"name": "prod"}],
    )
    logger.debug("Contours seeded (INSERT OR IGNORE)")


def _seed_system_settings(conn) -> None:
    row = conn.execute(text("SELECT COUNT(*) FROM system_settings")).scalar()
    if row == 0:
        conn.execute(
            text(
                """
                INSERT INTO system_settings
                    (polling_interval_sec, event_log_limit, timezone,
                     rolling_restart_timeout_sec, updated_at)
                VALUES
                    (:polling_interval_sec, :event_log_limit, :timezone,
                     :rolling_restart_timeout_sec, :updated_at)
                """
            ),
            {
                "polling_interval_sec": 5,
                "event_log_limit": 200,
                "timezone": "UTC",
                "rolling_restart_timeout_sec": 300,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        logger.debug("system_settings seeded with defaults")
    else:
        logger.debug("system_settings already has data, skipping seed")
