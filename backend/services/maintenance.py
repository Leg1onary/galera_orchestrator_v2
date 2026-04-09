"""
Maintenance service — Rolling restart of a Galera cluster.

Per ТЗ раздел 14:
  Rolling restart steps:
    1. For each node (sequentially):
       a. Enter maintenance mode (SET GLOBAL read_only=ON)
       b. systemctl restart mariadb
       c. Wait until wsrep_local_state_comment = 'Synced'
       d. Exit maintenance mode (SET GLOBAL read_only=OFF)
    2. Broadcast operation_progress after each node
    3. Cancel: stops after completing the current node step

All blocking SSH/DB work runs in asyncio.to_thread().
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from database import engine
from services.ssh_client import SSHClient, SSHError
from services.db_client import DBClient, DBError
from services.ws_manager import ws_manager
from services.operations import (
    create_operation,
    set_operation_status,
    is_cancel_requested,
)
from services.recovery import (
    _broadcast_progress,
    _broadcast_finished,
    _wait_node_synced,
    _load_cluster_nodes,
    _MARIADB_SERVICE,
    RecoveryError,
)
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Seconds between each poll when waiting for SYNCED after restart
_RESTART_SYNCED_TIMEOUT_SEC = 300


# ── Public API ─────────────────────────────────────────────────────────────────

async def start_rolling_restart(cluster_id: int, created_by: str) -> int:
    """
    Create a 'rolling_restart' operation and launch the async task.
    Returns the new operation id.
    """
    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="rolling_restart",
        created_by=created_by,
    )
    asyncio.create_task(
        _run_rolling_restart(cluster_id, op_id),
        name=f"rolling-restart-{cluster_id}",
    )
    return op_id


# ── Rolling restart task ───────────────────────────────────────────────────────────

async def _run_rolling_restart(cluster_id: int, op_id: int) -> None:
    """
    Sequentially restart each enabled node:
      enter-maintenance → restart → wait-synced → exit-maintenance

    Cancel: checked before each node. If cancel_requested, finishes
    current node's maintenance exit (to avoid leaving node read-only),
    then stops.
    """
    await asyncio.to_thread(set_operation_status, op_id, "running")

    try:
        nodes = await asyncio.to_thread(_load_cluster_nodes, cluster_id)
        if not nodes:
            raise RecoveryError("No enabled nodes found for this cluster")

        total = len(nodes)
        await _broadcast_progress(
            cluster_id, op_id, "start",
            f"Rolling restart started for {total} nodes",
            detail={"total_nodes": total},
        )

        for i, node in enumerate(nodes, 1):
            # Cancel check BEFORE starting next node (safe cancel point)
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                await _broadcast_progress(
                    cluster_id, op_id, "cancel",
                    f"Rolling restart cancelled before node {node['name']} ({i}/{total})",
                )
                await _broadcast_finished(cluster_id, op_id, success=False, message="Cancelled by user")
                return

            await _broadcast_progress(
                cluster_id, op_id, "node_restart",
                f"[{i}/{total}] {node['name']}: entering maintenance mode...",
                detail={"node_id": node["id"], "node_name": node["name"], "step": "enter_maintenance"},
            )

            # a. Enter maintenance только если нода не была в maintenance
            entered_maintenance = False
            if not node.get("maintenance"):
                try:
                    await asyncio.to_thread(_set_read_only, node, on=True)
                    await asyncio.to_thread(_set_node_maintenance_flag, node["id"], True)
                    entered_maintenance = True
                except (DBError, SSHError) as exc:
                    logger.warning("[%s] Enter maintenance failed: %s (continuing)", node["name"], exc)
            else:
                logger.info("[%s] Already in maintenance, skipping enter", node["name"])
                entered_maintenance = True  # считаем что вошли (для exit в конце)

            # b. Restart
            await _broadcast_progress(
                cluster_id, op_id, "node_restart",
                f"[{i}/{total}] {node['name']}: restarting MariaDB...",
                detail={"node_id": node["id"], "node_name": node["name"], "step": "restart"},
            )
            try:
                await asyncio.to_thread(_restart_mariadb, node)
            except SSHError as exc:
                raise RecoveryError(
                    f"Failed to restart MariaDB on {node['name']}: {exc}"
                ) from exc

            # c. Wait for SYNCED
            await _broadcast_progress(
                cluster_id, op_id, "node_restart",
                f"[{i}/{total}] {node['name']}: waiting for SYNCED...",
                detail={"node_id": node["id"], "node_name": node["name"], "step": "wait_synced"},
            )
            synced = await _wait_node_synced(
                node, op_id, cluster_id,
                timeout_sec=_RESTART_SYNCED_TIMEOUT_SEC,
            )

            # d. Exit maintenance (always, even if cancel_requested)
            try:
                await asyncio.to_thread(_set_read_only, node, on=False)
                await asyncio.to_thread(_set_node_maintenance_flag, node["id"], False)
            except (DBError, SSHError) as exc:
                logger.warning("[%s] Exit maintenance failed: %s", node["name"], exc)

            if not synced:
                if await asyncio.to_thread(is_cancel_requested, op_id):
                    await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                    await _broadcast_finished(cluster_id, op_id, success=False, message="Cancelled during wait")
                    return
                raise RecoveryError(
                    f"{node['name']} did not reach SYNCED within {_RESTART_SYNCED_TIMEOUT_SEC}s"
                )

            await _broadcast_progress(
                cluster_id, op_id, "node_restart",
                f"[{i}/{total}] {node['name']}: SYNCED ✓",
                detail={"node_id": node["id"], "node_name": node["name"], "step": "done"},
            )

        await asyncio.to_thread(set_operation_status, op_id, "success")
        await _broadcast_finished(
            cluster_id, op_id, success=True,
            message=f"Rolling restart complete — {total} nodes restarted",
        )
        logger.info("Rolling restart op %d completed for cluster %d", op_id, cluster_id)

    except RecoveryError as exc:
        logger.error("Rolling restart op %d failed: %s", op_id, exc)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await _broadcast_finished(cluster_id, op_id, success=False, message=str(exc))
    except asyncio.CancelledError:
        await asyncio.to_thread(set_operation_status, op_id, "cancelled")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in rolling restart op %d", op_id)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await _broadcast_finished(cluster_id, op_id, success=False, message=f"Internal error: {exc}")


# ── Node-level SSH/DB helpers ─────────────────────────────────────────────────────────

def _restart_mariadb(node: dict) -> None:
    """SSH: systemctl restart mariadb."""
    with SSHClient(
        host=node["host"],
        port=int(node.get("ssh_port") or 22),
        username=node.get("ssh_user") or "root",
    ) as ssh:
        out, err = ssh.execute(f"systemctl restart {_MARIADB_SERVICE}")
        if err and "failed" in err.lower():
            raise SSHError(f"systemctl restart mariadb failed: {err[:200]}")


def _set_read_only(node: dict, *, on: bool) -> None:
    """
    SET GLOBAL read_only = ON|OFF via pymysql.
    Uses db_user/db_password from node dict.
    """
    value = "ON" if on else "OFF"
    with DBClient(
        host=node["host"],
        port=int(node.get("port") or 3306),
        user=node.get("db_user") or "root",
        encrypted_password=node.get("db_password") or "",
    ) as db:
        db.execute(f"SET GLOBAL read_only = {value}")


def _set_node_maintenance_flag(node_id: int, value: bool) -> None:
    """Update nodes.maintenance column in SQLite."""
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE nodes SET maintenance = :val WHERE id = :id"),
            {"val": 1 if value else 0, "id": node_id},
        )
