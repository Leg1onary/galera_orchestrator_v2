"""
Maintenance router — Phase 3.

Per ТЗ раздел 14:
  GET  /api/clusters/{cluster_id}/maintenance/status
  GET  /api/clusters/{cluster_id}/maintenance/nodes
  POST /api/clusters/{cluster_id}/maintenance/rolling-restart
  POST /api/clusters/{cluster_id}/maintenance/cancel
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sqlalchemy import text
from database import engine
from services.poller import live_node_states

from dependencies import require_auth
from services.event_log import write_event
from services.maintenance import start_rolling_restart
from services.operations import (
    assert_no_active_operation,
    get_active_operation,
    request_cancel,
)
from services.ws_manager import ws_manager

# FIX MAJOR: auth перенесён в router-level dependency
router = APIRouter(
    prefix="/clusters",
    tags=["maintenance"],
    dependencies=[Depends(require_auth)],
)


# ── Request body ──────────────────────────────────────────────────────────────

class RollingRestartBody(BaseModel):
    node_order: Optional[list[int]] = Field(
        default=None,
        description="Ordered list of node IDs to restart. If omitted, uses DB order.",
    )
    wait_timeout_sec: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Seconds to wait for each node to reach SYNCED state.",
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/{cluster_id}/maintenance/status")
async def maintenance_status(cluster_id: int) -> dict:
    """
    Return the active maintenance operation for this cluster, or null.
    ТЗ 14.1, 9.1
    """
    op = await asyncio.to_thread(get_active_operation, cluster_id)

    if op and op["type"] != "rolling_restart":
        op = None

    return {"active_operation": op}


@router.get("/{cluster_id}/maintenance/nodes")
async def maintenance_nodes(cluster_id: int) -> list[dict]:
    """
    Ноды кластера с maintenance-полями + live state для Maintenance страницы.
    Возвращает только enabled=True ноды.
    """
    def _fetch() -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                     SELECT id, name, host, port, maintenance, enabled
                     FROM nodes
                     WHERE cluster_id = :cid AND enabled = 1
                     ORDER BY name
                     """),
                {"cid": cluster_id},
            ).mappings().fetchall()
        return [dict(r) for r in rows]

    nodes = await asyncio.to_thread(_fetch)

    result = []
    for n in nodes:
        live = live_node_states.get(cluster_id, {}).get(n["id"])
        result.append({
            "id":          n["id"],
            "name":        n["name"],
            "host":        n["host"],
            "port":        n["port"],
            "maintenance": bool(n["maintenance"]),
            "enabled":     bool(n["enabled"]),
            "wsrep_local_state_comment": live.wsrep_local_state_comment if live else None,
            "readonly":                  live.readonly                  if live else None,
            "maintenance_drift":         live.maintenance_drift         if live else None,
            "wsrep_desync":              live.wsrep_desync              if live else False,
            "ssh_ok":                    live.ssh_ok                    if live else None,
            "db_ok":                     live.db_ok                     if live else None,
            "last_check_ts":             live.last_check_ts.isoformat() if live and live.last_check_ts else None,
        })
    return result


@router.post("/{cluster_id}/maintenance/rolling-restart", status_code=202)
async def rolling_restart(
        cluster_id: int,
        body: RollingRestartBody = RollingRestartBody(),
        username: str = Depends(require_auth),
) -> dict:
    """
    Start a rolling restart of all enabled nodes in the cluster.

    - 409 if any operation is already active
    - 202 Accepted: operation created, progress via WS
    ТЗ 14.8, 14.6, 19.1
    """
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await start_rolling_restart(
        cluster_id,
        created_by=username,
        node_order=body.node_order,
        wait_timeout_sec=body.wait_timeout_sec,
    )

    write_event(
        level="INFO",
        source="maintenance",
        cluster_id=cluster_id,
        operation_id=op_id,
        message=f"Rolling restart started by '{username}' for cluster {cluster_id}",
    )

    return {
        "accepted":     True,
        "operation_id": op_id,
        "message":      "Rolling restart started. Subscribe to WS for progress.",
    }


@router.post("/{cluster_id}/maintenance/cancel")
async def maintenance_cancel(
        cluster_id: int,
        username: str = Depends(require_auth),
) -> dict:
    """
    Request cancellation of the active maintenance operation.
    ТЗ 14.1
    """
    op = await asyncio.to_thread(request_cancel, cluster_id)

    write_event(
        level="INFO",
        source="maintenance",
        cluster_id=cluster_id,
        operation_id=op["id"],
        message=f"Cancel requested by '{username}' for rolling restart op id={op['id']}",
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
        "message": (
            "Cancel requested. "
            "Current node will finish its maintenance-exit step before stopping."
        ),
    }
