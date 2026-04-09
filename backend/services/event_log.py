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
    """
    Insert an event into event_logs.

    Args:
        conn:           Active SQLAlchemy Core Connection (with open transaction).
        level:          'INFO' | 'WARN' | 'ERROR'
        source:         'system' | 'ui' | 'diagnostics' | 'ws' |
                        'ssh' | 'auth' | 'recovery' | 'maintenance'
        message:        Human-readable description.
        node_id:        Optional FK to nodes.id
        arbitrator_id:  Optional FK to arbitrators.id
        cluster_id:     Optional FK to clusters.id
        operation_id:   Optional FK to cluster_operations.id

    Raises:
        ValueError: if level or source is not in the allowed set.
    """
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
    """
    Async variant of log_event — opens its own DB connection.
    Used from the polling loop and WebSocket handlers where no
    Connection is passed in from a request context.

    Uses run_in_executor to avoid blocking the event loop on SQLite I/O.
    get_running_loop() is used instead of deprecated get_event_loop().
    """
    from database import get_connection  # avoid circular import at module level

    def _write() -> None:
        with get_connection() as conn:
            log_event(
                conn,
                level=level,
                source=source,
                message=message,
                node_id=node_id,
                arbitrator_id=arbitrator_id,
                cluster_id=cluster_id,
                operation_id=operation_id,
            )

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _write)
