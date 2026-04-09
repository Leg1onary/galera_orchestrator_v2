from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.engine import Connection

from models import event_logs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# STUB — partially implemented
#
# log_event() is a thin wrapper that inserts into event_logs table.
# It is used throughout the application (auth, SSH actions, recovery, etc.)
#
# The function is synchronous (uses a passed Connection) because most
# callers already have a DB connection in scope.
#
# For async contexts (WebSocket, poller), Phase 1 will add an async variant
# that opens its own connection from the engine.
# ---------------------------------------------------------------------------


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
    allowed_levels = {"INFO", "WARN", "ERROR"}
    allowed_sources = {
        "system", "ui", "diagnostics", "ws",
        "ssh", "auth", "recovery", "maintenance",
    }

    if level not in allowed_levels:
        raise ValueError(f"Invalid event level: {level!r}. Must be one of {allowed_levels}")
    if source not in allowed_sources:
        raise ValueError(
            f"Invalid event source: {source!r}. Must be one of {allowed_sources}"
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

    STUB — implement in Phase 1 once poller is active.
    Uses run_in_executor to avoid blocking the event loop on SQLite I/O.
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

    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write)