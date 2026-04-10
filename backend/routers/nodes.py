"""
Nodes router — Phase 2

Cluster-scoped per ТЗ. All routes under /api/clusters/{cluster_id}/...

Sync actions (immediate, no lock needed):
  set-readonly | set-readwrite | enter-maintenance | exit-maintenance

Async actions (cluster_operations, lock required):
  start | stop | restart | rejoin-force

GET  /api/clusters/{cluster_id}/nodes                          — список нод кластера
GET  /api/clusters/{cluster_id}/nodes/{node_id}               — конфиг + live state
PATCH /api/clusters/{cluster_id}/nodes/{node_id}              — enable/disable
GET  /api/clusters/{cluster_id}/nodes/{node_id}/test-connection
GET  /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status
POST /api/clusters/{cluster_id}/nodes/{node_id}/actions

GET  /api/clusters/{cluster_id}/operations/active
POST /api/clusters/{cluster_id}/operations/cancel
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.db_client import DBClient, DBError
from services.event_log import write_event
from services.operations import (
    assert_no_active_operation,
    create_operation,
    get_active_operation,
    is_cancel_requested,
    request_cancel,
    set_operation_status,
)
from services.poller import live_node_states
from services.ssh_client import SSHClient, SSHError
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

# FIX BLOCKER: убран /api из prefix — main.py уже монтирует с prefix="/api"
router = APIRouter(
    prefix="/clusters",
    tags=["nodes"],
    dependencies=[Depends(require_auth)],
)

# ── Constants ─────────────────────────────────────────────────────────────────

SYNC_ACTIONS  = frozenset({"set-readonly", "set-readwrite", "enter-maintenance", "exit-maintenance"})
ASYNC_ACTIONS = frozenset({"start", "stop", "restart", "rejoin-force"})
ALL_ACTIONS   = SYNC_ACTIONS | ASYNC_ACTIONS

# Per ТЗ раздел 15.11
SSH_CONNECT_TIMEOUT = 5
DB_CONNECT_TIMEOUT  = 3

# ── Schemas ───────────────────────────────────────────────────────────────────

class NodeActionRequest(BaseModel):
    action: str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ALL_ACTIONS:
            raise ValueError(
                f"Unknown action '{v}'. Valid: {sorted(ALL_ACTIONS)}"
            )
        return v


class NodePatchRequest(BaseModel):
    enabled:     bool | None = None
    maintenance: bool | None = None


# ── DB helpers ────────────────────────────────────────────────────────────────

def _fetch_node(cluster_id: int, node_id: int) -> dict:
    """Load node row. Raises 404 if not found or belongs to different cluster."""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                 SELECT n.*, d.name AS datacenter_name
                 FROM nodes n
                          LEFT JOIN datacenters d ON d.id = n.datacenter_id
                 WHERE n.id = :nid AND n.cluster_id = :cid
                 """),
            {"nid": node_id, "cid": cluster_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found in cluster {cluster_id}",
        )
    return dict(row)


def _assert_cluster_exists(cluster_id: int) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM clusters WHERE id = :cid"),
            {"cid": cluster_id},
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )


# ── GET /api/clusters/{cluster_id}/nodes ─────────────────────────────────────

@router.get("/{cluster_id}/nodes")
async def list_nodes(cluster_id: int) -> list[dict]:
    """
    GET /api/clusters/{cluster_id}/nodes — список нод кластера с live state.
    ТЗ 9.1, 11.1
    """
    _assert_cluster_exists(cluster_id)
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT n.*, d.name AS datacenter_name
                 FROM nodes n
                          LEFT JOIN datacenters d ON d.id = n.datacenter_id
                 WHERE n.cluster_id = :cid
                 ORDER BY n.name
                 """),
            {"cid": cluster_id},
        ).mappings().fetchall()

    result = []
    for n in rows:
        node = dict(n)
        live = live_node_states.get(cluster_id, {}).get(node["id"])
        result.append({
            "id":             node["id"],
            "name":           node["name"],
            "host":           node["host"],
            "port":           node["port"],
            "ssh_port":       node["ssh_port"],
            "ssh_user":       node["ssh_user"],
            "db_user":        node["db_user"],
            # db_password намеренно не возвращается
            "enabled":        bool(node["enabled"]),
            "maintenance":    bool(node["maintenance"]),
            "datacenter_id":  node["datacenter_id"],
            "datacenter_name": node["datacenter_name"],
            "cluster_id":     node["cluster_id"],
            "live":           live.to_dict() if live is not None else None,
        })
    return result


# ── GET /api/clusters/{cluster_id}/nodes/{node_id} ───────────────────────────

@router.get("/{cluster_id}/nodes/{node_id}")
async def get_node(cluster_id: int, node_id: int) -> dict:
    """Full config + live state for a single node. ТЗ 11.4"""
    node = _fetch_node(cluster_id, node_id)
    live = live_node_states.get(cluster_id, {}).get(node_id)
    return {
        "id":             node["id"],
        "name":           node["name"],
        "host":           node["host"],
        "port":           node["port"],
        "ssh_port":       node["ssh_port"],
        "ssh_user":       node["ssh_user"],
        "db_user":        node["db_user"],
        "enabled":        bool(node["enabled"]),
        "maintenance":    bool(node["maintenance"]),
        "datacenter_id":  node["datacenter_id"],
        "datacenter_name": node["datacenter_name"],
        "cluster_id":     node["cluster_id"],
        "live":           live.to_dict() if live is not None else None,
    }


# ── PATCH /api/clusters/{cluster_id}/nodes/{node_id} ─────────────────────────

@router.patch("/{cluster_id}/nodes/{node_id}")
async def patch_node(
        cluster_id: int,
        node_id: int,
        body: NodePatchRequest,
) -> dict:
    """
    PATCH enabled / maintenance flag на ноде.
    ТЗ 11.1, 11.6 — enable/disable через NodeDetailDrawer.
    """
    _fetch_node(cluster_id, node_id)  # проверка 404
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = node_id
    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE nodes SET {set_clause} WHERE id = :id"),
            updates,
        )
    return {"accepted": True, "node_id": node_id, **body.model_dump(exclude_none=True)}


# ── GET /api/clusters/{cluster_id}/nodes/{node_id}/test-connection ────────────

@router.get("/{cluster_id}/nodes/{node_id}/test-connection")
async def test_node_connection(cluster_id: int, node_id: int) -> dict:
    """
    Live SSH + DB connectivity and latency test.
    Does NOT use cached poller state — opens fresh connections.
    ТЗ 15.3, 15.11
    """
    node = _fetch_node(cluster_id, node_id)

    result: dict = {
        "node_id":        node_id,
        "ssh_ok":         False,
        "ssh_latency_ms": None,
        "db_ok":          False,
        "db_latency_ms":  None,
        "error":          None,
    }

    # SSH
    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    try:
        await asyncio.to_thread(ssh.connect)
        latency = await asyncio.to_thread(ssh.test_connection)
        result["ssh_ok"]         = True
        result["ssh_latency_ms"] = latency
    except SSHError as exc:
        result["error"] = f"SSH: {exc}"
        return result
    finally:
        await asyncio.to_thread(ssh.close)

    # DB
    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        db_latency = await asyncio.to_thread(db.test_connection)
        result["db_ok"]         = True
        result["db_latency_ms"] = db_latency
    except DBError as exc:
        result["error"] = f"DB: {exc}"
    finally:
        await asyncio.to_thread(db.close)

    return result


# ── GET /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status ──────────────

@router.get("/{cluster_id}/nodes/{node_id}/innodb-status")
async def get_innodb_status(cluster_id: int, node_id: int) -> dict:
    """
    Run SHOW ENGINE INNODB STATUS on the node.
    Parses full text + LATEST DETECTED DEADLOCK section.
    ТЗ 15.7
    """
    node = _fetch_node(cluster_id, node_id)

    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        rows = await asyncio.to_thread(db.query, "SHOW ENGINE INNODB STATUS")
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DB connection failed: {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)

    full_text = ""
    if rows:
        row = rows[0]
        normalised = {k.lower(): v for k, v in row.items()}
        full_text = normalised.get("status", "")

    deadlock_section = _extract_deadlock_section(full_text)

    return {
        "node_id":         node_id,
        "full_status":     full_text,
        "latest_deadlock": deadlock_section,
        "has_deadlock":    deadlock_section is not None,
    }


def _extract_deadlock_section(innodb_text: str) -> str | None:
    match = re.search(
        r"LATEST DETECTED DEADLOCK\n-+\n(.*?)(?=\n-{4,}|\Z)",
        innodb_text,
        re.DOTALL,
    )
    return match.group(1).strip() if match else None


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/actions ──────────────────

@router.post("/{cluster_id}/nodes/{node_id}/actions")
async def node_action(
        cluster_id: int,
        node_id: int,
        body: NodeActionRequest,
) -> dict:
    """
    Execute a node action.
    Sync actions execute immediately.
    Async actions create a cluster_operation and run in background.
    ТЗ 9.3, 11.6, 14.5
    """
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled — cannot execute actions on it",
        )

    action = body.action

    if action in SYNC_ACTIONS:
        return await _run_sync_action(cluster_id, node, action)
    else:
        return await _start_async_action(cluster_id, node, action)


# ── Sync action executor ──────────────────────────────────────────────────────

async def _run_sync_action(cluster_id: int, node: dict, action: str) -> dict:
    node_id = node["id"]

    if action == "set-readonly":
        await _db_exec(node, "SET GLOBAL read_only = ON")
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': SET GLOBAL read_only = ON",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "set-readwrite":
        await _db_exec(node, "SET GLOBAL read_only = OFF")
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': SET GLOBAL read_only = OFF",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "enter-maintenance":
        # FIX MAJOR: ТЗ 14.9 — сначала SET readonly=ON, потом maintenance=true
        await _db_exec(node, "SET GLOBAL read_only = ON")           # ← 1
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE nodes SET maintenance = 1 WHERE id = :id"),
                {"id": node_id},
            )                                                         # ← 2
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': entered maintenance mode",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "exit-maintenance":
        # FIX MAJOR: ТЗ 14.9 — сначала SET readonly=OFF, потом maintenance=false
        live = live_node_states.get(cluster_id, {}).get(node_id)
        if live and live.maintenance_drift:
            logger.warning(
                "exit-maintenance on node %d: maintenance_drift=True "
                "(read_only already OFF in MariaDB)", node_id,
            )
        await _db_exec(node, "SET GLOBAL read_only = OFF")           # ← 1
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE nodes SET maintenance = 0 WHERE id = :id"),
                {"id": node_id},
            )                                                         # ← 2
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': exited maintenance mode",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    raise HTTPException(status_code=500, detail=f"Unhandled sync action: {action}")


async def _db_exec(node: dict, sql: str) -> None:
    """Execute a single SQL statement on a node. Raises 502 on failure."""
    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        await asyncio.to_thread(db.execute, sql)
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DB command failed: {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)


# ── Async action launcher ─────────────────────────────────────────────────────

async def _start_async_action(cluster_id: int, node: dict, action: str) -> dict:
    """
    Create cluster_operation for start/stop/restart/rejoin-force.
    Returns immediately; execution runs in background.
    Raises 409 if cluster already has an active operation.
    ТЗ 19.1
    """
    # FIX BLOCKER: синхронные вызовы обёрнуты в to_thread
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="node_action",
        target_node_id=node["id"],
        details={"action": action, "node_name": node["name"]},
        created_by="api",
    )

    write_event(
        level="INFO",
        cluster_id=cluster_id,
        node_id=node["id"],
        source="ui",
        message=f"Node '{node['name']}': async action '{action}' queued (op_id={op_id})",
    )

    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_started",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "operation_id": op_id,
            "type":         "node_action",
            "action":       action,
            "node_id":      node["id"],
            "node_name":    node["name"],
        },
    })

    asyncio.create_task(
        _execute_node_action(cluster_id, node, action, op_id),
        name=f"node_action_{op_id}",
    )

    return {
        "accepted":     True,
        "action":       action,
        "node_id":      node["id"],
        "operation_id": op_id,
        "status":       "pending",
    }


async def _execute_node_action(
        cluster_id: int,
        node: dict,
        action: str,
        op_id: int,
) -> None:
    """Background task: execute SSH-based async node action."""
    node_id   = node["id"]
    node_name = node["name"]

    # FIX BLOCKER: все синхронные вызовы operations обёрнуты в to_thread
    await asyncio.to_thread(set_operation_status, op_id, "running")

    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_progress",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    {"operation_id": op_id, "message": f"Executing '{action}' on {node_name}"},
    })

    if await asyncio.to_thread(is_cancel_requested, op_id):
        await asyncio.to_thread(set_operation_status, op_id, "cancelled")
        await _broadcast_op_finished(cluster_id, op_id, "cancelled")
        return

    try:
        await asyncio.to_thread(_ssh_node_action, node, action)
    except SSHError as exc:
        error_msg = f"SSH error during '{action}' on '{node_name}': {exc}"
        logger.error(error_msg)
        write_event(level="ERROR", cluster_id=cluster_id, node_id=node_id,
                    source="ssh", message=error_msg)
        await asyncio.to_thread(set_operation_status, op_id, "failed", error_msg)
        await _broadcast_op_finished(cluster_id, op_id, "failed", error_msg)
        return
    except Exception as exc:
        error_msg = f"Unexpected error during '{action}' on '{node_name}': {exc}"
        logger.exception(error_msg)
        write_event(level="ERROR", cluster_id=cluster_id, node_id=node_id,
                    source="system", message=error_msg)
        await asyncio.to_thread(set_operation_status, op_id, "failed", error_msg)
        await _broadcast_op_finished(cluster_id, op_id, "failed", error_msg)
        return

    write_event(
        level="INFO", cluster_id=cluster_id, node_id=node_id,
        source="ui",
        message=f"Node '{node_name}': action '{action}' completed successfully",
    )
    await asyncio.to_thread(set_operation_status, op_id, "success")
    await _broadcast_op_finished(cluster_id, op_id, "success")


def _ssh_node_action(node: dict, action: str) -> None:
    """
    Blocking: execute SSH command for the given action.
    ТЗ 11.6:
      start        → systemctl start mariadb
      stop         → systemctl stop mariadb
      restart      → systemctl restart mariadb
      rejoin-force → stop + reset safe_to_bootstrap + start
    """
    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    ssh.connect()
    try:
        if action == "start":
            ssh.execute("systemctl start mariadb")
        elif action == "stop":
            ssh.execute("systemctl stop mariadb")
        elif action == "restart":
            ssh.execute("systemctl restart mariadb")
        elif action == "rejoin-force":
            ssh.execute("systemctl stop mariadb")
            ssh.execute(
                "sed -i 's/^safe_to_bootstrap:.*$/safe_to_bootstrap: 0/' "
                "/var/lib/mysql/grastate.dat"
            )
            ssh.execute("systemctl start mariadb")
        else:
            raise SSHError(f"Unknown async action: {action}")
    finally:
        ssh.close()


async def _broadcast_op_finished(
        cluster_id: int,
        op_id: int,
        final_status: str,
        error: str | None = None,
) -> None:
    payload: dict = {"operation_id": op_id, "status": final_status}
    if error:
        payload["error"] = error
    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_finished",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    payload,
    })


# ── GET /api/clusters/{cluster_id}/operations/active ─────────────────────────

@router.get("/{cluster_id}/operations/active")
async def get_active_op(cluster_id: int) -> dict:
    """Return the currently active operation for the cluster, or null."""
    _assert_cluster_exists(cluster_id)
    active = await asyncio.to_thread(get_active_operation, cluster_id)
    return {"operation": active}


# ── POST /api/clusters/{cluster_id}/operations/cancel ────────────────────────

@router.post("/{cluster_id}/operations/cancel")
async def cancel_operation(cluster_id: int) -> dict:
    """
    Request cancellation of active operation.
    Idempotent if already cancel_requested.
    Raises 404 if no active operation.
    ТЗ 19.1
    """
    _assert_cluster_exists(cluster_id)
    op = await asyncio.to_thread(request_cancel, cluster_id)
    write_event(
        level="INFO",
        cluster_id=cluster_id,
        source="ui",
        message=f"Cancel requested for operation id={op['id']} type={op['type']}",
    )
    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_cancel_requested",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    {"operation_id": op["id"]},
    })
    return {"accepted": True, "operation": op}