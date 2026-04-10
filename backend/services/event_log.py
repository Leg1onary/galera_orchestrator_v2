from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.engine import Connection

from models import event_logs

logger = logging.getLogger(__name__)


ALLOWED_LEVELS = frozenset({"INFO", "WARN", "ERROR"})
ALLOWED_SOURCES = frozenset({
    "system", "ui", "diagnostics", "ws",
    "ssh", "auth", "recovery", "maintenance",
})


def log_event(
        conn: Connection,
        *,
        level: str,
        source: str,
        message: str,
        node_id: Optional[int] = None,
        arbitrator_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
        operation_id: Optional[int] = None,
) -> None:
    if level not in ALLOWED_LEVELS:
        raise ValueError(f"Invalid event level: {level!r}. Must be one of {ALLOWED_LEVELS}")
    if source not in ALLOWED_SOURCES:
        raise ValueError(
            f"Invalid event source: {source!r}. Must be one of {ALLOWED_SOURCES}"
        )

    conn.execute(
        event_logs.insert().values(
            ts=datetime.now(tz=timezone.utc),
            level=level,
            source=source,
            message=message,
            node_id=node_id,
            arbitrator_id=arbitrator_id,
            cluster_id=cluster_id,
            operation_id=operation_id,
        )
    )


async def log_event_async(
        *,
        level: str,
        source: str,
        message: str,
        node_id: Optional[int] = None,
        arbitrator_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
        operation_id: Optional[int] = None,
) -> None:
    from database import engine

    def _write() -> None:
        with engine.begin() as conn:
            log_event(conn, level=level, source=source, message=message,
                      node_id=node_id, arbitrator_id=arbitrator_id,
                      cluster_id=cluster_id, operation_id=operation_id)
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write)
    except Exception:
        logger.exception("log_event_async failed silently: %s", message)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _write)


def write_event(
        *,
        message: str,
        source: str = "ui",
        level: str = "INFO",
        cluster_id: Optional[int] = None,
        node_id: Optional[int] = None,
        arbitrator_id: Optional[int] = None,
        operation_id: Optional[int] = None,
) -> None:
    """
    Convenience wrapper used by Phase 2 routers (nodes, settings, operations).
    Opens its own DB connection, no need to pass conn explicitly.
    Falls back silently on error to avoid breaking the calling request.
    """
    from database import engine

    if source not in ALLOWED_SOURCES:
        source = "system"

    try:
        with engine.begin() as conn:
            log_event(conn, level=level, source=source, message=message,
                      cluster_id=cluster_id, node_id=node_id,
                      arbitrator_id=arbitrator_id, operation_id=operation_id)
    except Exception:
        logger.exception("write_event failed silently: %s", message)
