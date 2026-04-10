"""
Recovery router — Phase 3.

Per ТЗ раздел 13:
  GET  /api/clusters/{cluster_id}/recovery/status
  POST /api/clusters/{cluster_id}/recovery/bootstrap
  POST /api/clusters/{cluster_id}/recovery/rejoin
  POST /api/clusters/{cluster_id}/recovery/cancel
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import require_auth
from services.event_log import write_event
from services.operations import (
    assert_no_active_operation,
    get_active_operation,
    request_cancel,
)
from services.recovery import start_bootstrap, start_rejoin
from services.ws_manager import ws_manager
from datetime import datetime, timezone

# FIX MAJOR: auth перенесён в router-level dependency — не дублируем в каждом эндпоинте
router = APIRouter(
    prefix="/clusters",
    tags=["recovery"],
    dependencies=[Depends(require_auth)],
)


# ── Request schemas ────────────────────────────────────────────────────────────

class RejoinRequest(BaseModel):
    node_id: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/{cluster_id}/recovery/status")
async def recovery_status(cluster_id: int) -> dict:
    """
    Return the active recovery operation for this cluster, or null.
    Used by the UI wizard to poll current state.
    ТЗ 13.1
    """
    # FIX BLOCKER: синхронный вызов → to_thread
    op = await asyncio.to_thread(get_active_operation, cluster_id)

    # FIX MAJOR: ТЗ op_type = "recovery_bootstrap" / "recovery_rejoin"
    if op and op["type"] not in ("recovery_bootstrap", "recovery_rejoin"):
        op = None

    return {"active_operation": op}


@router.post("/{cluster_id}/recovery/bootstrap", status_code=202)
async def recovery_bootstrap(
        cluster_id: int,
        # FIX MINOR: username нужен для created_by — получаем через отдельный Depends
        username: str = Depends(require_auth),
) -> dict:
    """
    Start the 4-step bootstrap wizard for a fully-down cluster.

    - 409 if any operation is already active on this cluster
    - 202 Accepted: operation created, progress via WS operation_progress events
    ТЗ 13.4, 13.7, 19.1
    """
    # FIX BLOCKER: синхронный вызов → to_thread
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await start_bootstrap(cluster_id, created_by=username)

    write_event(
        level="INFO",
        source="recovery",
        cluster_id=cluster_id,
        operation_id=op_id,
        message=f"Bootstrap wizard started by '{username}' for cluster {cluster_id}",
    )

    return {
        "accepted":     True,
        "operation_id": op_id,
        "message":      "Bootstrap wizard started. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/recovery/rejoin", status_code=202)
async def recovery_rejoin(
        cluster_id: int,
        body: RejoinRequest,
        username: str = Depends(require_auth),
) -> dict:
    """
    Rejoin a single offline node into an already-running cluster.

    - 409 if any operation is already active
    - 202 Accepted: operation created
    ТЗ 13.5
    """
    # FIX BLOCKER: синхронный вызов → to_thread
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await start_rejoin(cluster_id, node_id=body.node_id, created_by=username)

    write_event(
        level="INFO",
        source="recovery",
        cluster_id=cluster_id,
        node_id=body.node_id,
        operation_id=op_id,
        message=(
            f"Rejoin started by '{username}' for node {body.node_id} "
            f"in cluster {cluster_id}"
        ),
    )

    return {
        "accepted":     True,
        "operation_id": op_id,
        "message": f"Rejoin started for node {body.node_id}. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/recovery/cancel")
async def recovery_cancel(cluster_id: int, username: str = Depends(require_auth)) -> dict:
    """
    Request cancellation of the active recovery operation.

    - 404 if no active operation
    - Idempotent: safe to call multiple times
    - Actual stop happens after the current step completes
    ТЗ 13.6
    """
    # FIX BLOCKER: синхронный вызов → to_thread
    op = await asyncio.to_thread(request_cancel, cluster_id)

    write_event(
        level="INFO",
        source="recovery",
        cluster_id=cluster_id,
        operation_id=op["id"],
        message=f"Cancel requested by '{username}' for operation id={op['id']}",
    )

    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_cancel_requested",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "operation_id": op["id"],
            "type":         op["type"],
        },
    })

    return {
        "cancelled":    True,
        "operation_id": op["id"],
        "status":       op["status"],
        "message":      "Cancel requested. Operation will stop after current step completes.",
    }