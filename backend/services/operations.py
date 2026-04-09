"""
Cluster operations — state machine, lock semantics, and async execution helpers.

Per ТЗ раздел 10:
  - One active operation per cluster at a time (cluster-level lock)
  - Active = status IN ('pending', 'running', 'cancel_requested')
  - 409 Conflict if a new operation is requested while one is active
  - cancel_requested → waiting for current step → 'cancelled'
  - Async operations: node_action (start/stop/restart/rejoin-force)
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import text

from database import engine
from services.event_log import write_event

logger = logging.getLogger(__name__)

# Statuses considered "active" → block new operations on same cluster
_ACTIVE_STATUSES = ("pending", "running", "cancel_requested")


# ── Lock helpers ──────────────────────────────────────────────────────────────

def get_active_operation(cluster_id: int) -> dict | None:
    """Return the active operation for a cluster, or None."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, type, status, started_at, created_by, target_node_id, details_json
                FROM cluster_operations
                WHERE cluster_id = :cid
                  AND status IN ('pending', 'running', 'cancel_requested')
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"cid": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def assert_no_active_operation(cluster_id: int) -> None:
    """
    Raise 409 if there is already an active operation on this cluster.
    Call this before creating any new operation.
    """
    active = get_active_operation(cluster_id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "cluster_locked",
                "message": (
                    f"Cluster {cluster_id} has an active operation "
                    f"'{active['type']}' (id={active['id']}, status={active['status']}). "
                    "Cancel or wait for it to complete before starting a new one."
                ),
                "active_operation": {
                    "id": active["id"],
                    "type": active["type"],
                    "status": active["status"],
                },
            },
        )


def create_operation(
        *,
        cluster_id: int,
        op_type: str,
        target_node_id: int | None = None,
        details: dict | None = None,
        created_by: str = "api",
) -> int:
    """
    Insert a new cluster_operation row with status='pending'.
    Returns the new operation id.

    Does NOT acquire a lock — call assert_no_active_operation() first.
    """
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO cluster_operations
                (cluster_id, type, status, started_at, created_by, target_node_id, details_json)
                VALUES
                    (:cluster_id, :type, 'pending', :now, :created_by, :target_node_id, :details_json)
                """
            ),
            {
                "cluster_id":    cluster_id,
                "type":          op_type,
                "now":           datetime.now(timezone.utc).isoformat(),
                "created_by":    created_by,
                "target_node_id": target_node_id,
                "details_json":  json.dumps(details) if details else None,
            },
        )
        return result.lastrowid


def set_operation_status(
        op_id: int,
        new_status: str,
        error_message: str | None = None,
) -> None:
    """Update status (and finished_at if terminal) of a cluster_operation."""
    is_terminal = new_status in ("success", "failed", "cancelled")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE cluster_operations
                SET status       = :status,
                    finished_at  = CASE WHEN :terminal THEN :now ELSE finished_at END,
                    error_message= COALESCE(:error, error_message)
                WHERE id = :op_id
                """
            ),
            {
                "status":    new_status,
                "terminal":  1 if is_terminal else 0,
                "now":       datetime.now(timezone.utc).isoformat(),
                "error":     error_message,
                "op_id":     op_id,
            },
        )


def is_cancel_requested(op_id: int) -> bool:
    """Check if the operation has been asked to cancel."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status FROM cluster_operations WHERE id = :id"),
            {"id": op_id},
        ).fetchone()
    return row is not None and row[0] == "cancel_requested"


def request_cancel(cluster_id: int) -> dict:
    """
    Mark the active operation on a cluster as cancel_requested.
    Returns the updated operation dict.
    Raises 404 if no active operation exists.
    """
    active = get_active_operation(cluster_id)
    if not active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active operation to cancel on this cluster",
        )
    if active["status"] == "cancel_requested":
        return active  # idempotent

    set_operation_status(active["id"], "cancel_requested")
    active["status"] = "cancel_requested"
    return active


def get_operation(op_id: int) -> dict | None:
    """Load a single operation row by id."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM cluster_operations WHERE id = :id"),
            {"id": op_id},
        ).mappings().fetchone()
    return dict(row) if row else None