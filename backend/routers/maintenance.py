"""
Maintenance router — Phase 3.

Per ТЗ раздел 14:
  GET  /api/clusters/{cluster_id}/maintenance/status
  POST /api/clusters/{cluster_id}/maintenance/rolling-restart
  POST /api/clusters/{cluster_id}/maintenance/cancel
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import require_auth
from services.operations import (
    assert_no_active_operation,
    get_active_operation,
    request_cancel,
)
from services.maintenance import start_rolling_restart

router = APIRouter(prefix="/clusters", tags=["maintenance"])


@router.get("/{cluster_id}/maintenance/status")
async def maintenance_status(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Return the active maintenance operation for this cluster, or null.
    """
    op = get_active_operation(cluster_id)
    if op and op["type"] != "rolling_restart":
        op = None
    return {"active_operation": op}


@router.post("/{cluster_id}/maintenance/rolling-restart", status_code=202)
async def rolling_restart(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Start a rolling restart of all enabled nodes in the cluster.

    - 409 if any operation is already active
    - 202 Accepted: operation created, progress via WS
    """
    assert_no_active_operation(cluster_id)
    op_id = await start_rolling_restart(cluster_id, created_by=username)
    return {
        "accepted": True,
        "operation_id": op_id,
        "message": "Rolling restart started. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/maintenance/cancel")
async def maintenance_cancel(
        cluster_id: int,
        username: str = Depends(require_auth),
):
    """
    Request cancellation of the active maintenance operation.

    - 404 if no active operation
    - Stops after the current node's maintenance-exit step (node won't be left read-only)
    """
    op = request_cancel(cluster_id)
    return {
        "cancelled": True,
        "operation_id": op["id"],
        "status": op["status"],
        "message": "Cancel requested. Current node will finish its maintenance-exit step before stopping.",
    }
