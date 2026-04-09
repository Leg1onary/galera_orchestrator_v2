"""
Recovery router — Phase 3.

Per ТЗ раздел 13:
  GET  /api/clusters/{cluster_id}/recovery/status
  POST /api/clusters/{cluster_id}/recovery/bootstrap
  POST /api/clusters/{cluster_id}/recovery/rejoin
  POST /api/clusters/{cluster_id}/recovery/cancel
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import require_auth
from services.operations import (
    assert_no_active_operation,
    get_active_operation,
    request_cancel,
)
from services.recovery import start_bootstrap, start_rejoin

router = APIRouter(prefix="/clusters", tags=["recovery"])


# ── Request schemas ─────────────────────────────────────────────────────────────

class RejoinRequest(BaseModel):
    node_id: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/{cluster_id}/recovery/status")
async def recovery_status(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Return the active recovery operation for this cluster, or null.
    Used by the UI wizard to poll current state.
    """
    op = get_active_operation(cluster_id)
    # Filter: only return recovery-type operations here
    if op and op["type"] not in ("bootstrap", "rejoin"):
        op = None
    return {"active_operation": op}


@router.post("/{cluster_id}/recovery/bootstrap", status_code=202)
async def recovery_bootstrap(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Start the 4-step bootstrap wizard for a fully-down cluster.

    - 409 if any operation is already active on this cluster
    - 202 Accepted: operation created, progress via WS operation_progress events
    """
    assert_no_active_operation(cluster_id)
    op_id = await start_bootstrap(cluster_id, created_by=username)
    return {
        "accepted": True,
        "operation_id": op_id,
        "message": "Bootstrap wizard started. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/recovery/rejoin", status_code=202)
async def recovery_rejoin(
        cluster_id: int,
        body: RejoinRequest,
        username: str = Depends(require_auth),
):
    """
    Rejoin a single offline node into an already-running cluster.

    - 409 if any operation is already active
    - 202 Accepted: operation created
    """
    assert_no_active_operation(cluster_id)
    op_id = await start_rejoin(cluster_id, node_id=body.node_id, created_by=username)
    return {
        "accepted": True,
        "operation_id": op_id,
        "message": f"Rejoin started for node {body.node_id}. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/recovery/cancel")
async def recovery_cancel(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Request cancellation of the active recovery operation.

    - 404 if no active operation
    - Idempotent: safe to call multiple times
    - Actual stop happens after the current step completes
    """
    op = request_cancel(cluster_id)
    return {
        "cancelled": True,
        "operation_id": op["id"],
        "status": op["status"],
        "message": "Cancel requested. Operation will stop after current step completes.",
    }
