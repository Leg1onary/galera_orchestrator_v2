"""
Recovery service — Galera cluster bootstrap and node rejoin.

Per ТЗ раздел 13:
  Bootstrap wizard steps:
    1. scan       — Read grastate.dat from all nodes via SSH
    2. select     — Determine bootstrap candidate (highest seqno + safe_to_bootstrap)
    3. bootstrap  — Start donor node with wsrep_cluster_address=gcomm://
    4. rejoin     — Start remaining nodes one by one

  Rejoin: start a single offline node against an already-running cluster.

  Cancel: set cancel_requested on the active operation; the running step
          checks is_cancel_requested() after each phase and stops cleanly.

All blocking SSH work runs in asyncio.to_thread().
Progress is broadcast via WS operation_progress events.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from database import engine
from services.ssh_client import SSHClient, SSHError
from services.ws_manager import ws_manager
from services.event_log import write_event
from services.operations import (
    create_operation,
    set_operation_status,
    is_cancel_requested,
    assert_no_active_operation,
)
from sqlalchemy import text

from services.event_log import write_event

logger = logging.getLogger(__name__)

# Timeout waiting for a node to become SYNCED after bootstrap (seconds)
_SYNCED_WAIT_TIMEOUT_SEC = 300
_SYNCED_POLL_INTERVAL_SEC = 5

# systemctl service name for MariaDB on the managed nodes
_MARIADB_SERVICE = "mariadb"


# ── Public API ─────────────────────────────────────────────────────────────────

async def start_bootstrap(cluster_id: int, created_by: str) -> int:
    """
    Create a 'bootstrap' operation and launch the async wizard.
    Returns the new operation id.
    """
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="recovery_bootstrap",
        created_by=created_by,
    )
    asyncio.create_task(
        _run_bootstrap(cluster_id, op_id),
        name=f"bootstrap-{cluster_id}",
    )
    return op_id


async def start_rejoin(cluster_id: int, node_id: int, created_by: str) -> int:
    """
    Create a 'rejoin' operation for a single node and launch it.
    Returns the new operation id.
    """
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="recovery_rejoin",
        target_node_id=node_id,
        created_by=created_by,
    )
    asyncio.create_task(
        _run_rejoin(cluster_id, op_id, node_id),
        name=f"rejoin-{cluster_id}-{node_id}",
    )
    return op_id


# ── Bootstrap wizard ──────────────────────────────────────────────────────────────

async def _run_bootstrap(cluster_id: int, op_id: int) -> None:
    """Full bootstrap wizard: scan → select → bootstrap → rejoin."""
    await asyncio.to_thread(set_operation_status, op_id, "running")

    try:
        # ── Step 1: Scan ───────────────────────────────────────────────────────
        await _broadcast_progress(cluster_id, op_id, "scan", "Scanning nodes for grastate.dat...")

        nodes = await asyncio.to_thread(_load_cluster_nodes, cluster_id)
        if not nodes:
            raise RecoveryError("No enabled nodes found for this cluster")

        scan_results = await asyncio.to_thread(_scan_grastate, nodes)
        await _broadcast_progress(
            cluster_id, op_id, "scan",
            f"Scanned {len(scan_results)} nodes",
            detail=scan_results,
        )

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            await _broadcast_progress(cluster_id, op_id, "scan", "Cancelled after scan")
            return

        # ── Step 2: Select bootstrap candidate ─────────────────────────────────
        donor = _select_bootstrap_candidate(scan_results)
        if donor is None:
            raise RecoveryError(
                "Cannot determine bootstrap candidate: no node with safe_to_bootstrap=1 "
                "or positive seqno found. Manual intervention required."
            )

        await _broadcast_progress(
            cluster_id, op_id, "select",
            f"Bootstrap candidate: {donor['name']} (seqno={donor['seqno']})",
            detail={"donor_node_id": donor["id"], "donor_name": donor["name"], "seqno": donor["seqno"]},
        )

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            await _broadcast_progress(cluster_id, op_id, "select", "Cancelled before bootstrap")
            return

        # ── Step 3: Bootstrap donor ─────────────────────────────────────────────
        await _broadcast_progress(
            cluster_id, op_id, "bootstrap",
            f"Starting {donor['name']} as bootstrap node (gcomm://)...",
        )
        await asyncio.to_thread(_start_bootstrap_node, donor)
        await _broadcast_progress(
            cluster_id, op_id, "bootstrap",
            f"{donor['name']} bootstrap start issued, waiting for SYNCED...",
        )

        # Wait for donor to reach SYNCED
        synced = await _wait_node_synced(donor, op_id, cluster_id)
        if not synced:
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                return
            raise RecoveryError(
                f"Bootstrap node {donor['name']} did not reach SYNCED "
                f"within {_SYNCED_WAIT_TIMEOUT_SEC}s"
            )

        await _broadcast_progress(
            cluster_id, op_id, "bootstrap",
            f"{donor['name']} is SYNCED — cluster is live",
        )

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            return

        # ── Step 4: Rejoin remaining nodes ───────────────────────────────────────
        remaining = [n for n in nodes if n["id"] != donor["id"]]
        for i, node in enumerate(remaining, 1):
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                await _broadcast_progress(
                    cluster_id, op_id, "rejoin",
                    f"Cancelled before rejoining {node['name']}",
                )
                return

            await _broadcast_progress(
                cluster_id, op_id, "rejoin",
                f"Rejoining {node['name']} ({i}/{len(remaining)})...",
                detail={"node_id": node["id"], "node_name": node["name"]},
            )
            try:
                await asyncio.to_thread(_start_node_normal, node)
            except RecoveryError as exc:
                logger.warning("Failed to rejoin %s: %s (continuing)", node["name"], exc)
                await _broadcast_progress(
                    cluster_id, op_id, "rejoin",
                    f"WARNING: {node['name']} rejoin failed: {exc} (continuing with remaining nodes)",
                )

        await asyncio.to_thread(set_operation_status, op_id, "success")
        await asyncio.to_thread(
            write_event,
            level="INFO",
            source="recovery",
            message=f"Bootstrap operation {op_id} completed successfully",
            cluster_id=cluster_id,
            operation_id=op_id,
        )
        await _broadcast_finished(cluster_id, op_id, success=True, message="Bootstrap complete")
        logger.info("Bootstrap operation %d completed successfully", op_id)

    except RecoveryError as exc:
        logger.error("Bootstrap operation %d failed: %s", op_id, exc)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await asyncio.to_thread(
            write_event,
            level="ERROR",
            source="recovery",
            message=f"Bootstrap operation {op_id} failed: {exc}",
            cluster_id=cluster_id,
            operation_id=op_id,
        )
        await _broadcast_finished(cluster_id, op_id, success=False, message=str(exc))
    except asyncio.CancelledError:
        await asyncio.to_thread(set_operation_status, op_id, "cancelled")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in bootstrap op %d", op_id)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await asyncio.to_thread(
            write_event,
            level="ERROR",
            source="recovery",
            message=f"Bootstrap operation {op_id} failed: {exc}",
            cluster_id=cluster_id,
            operation_id=op_id,
        )
        await _broadcast_finished(cluster_id, op_id, success=False, message=f"Internal error: {exc}")


# ── Rejoin single node ───────────────────────────────────────────────────────────────

async def _run_rejoin(cluster_id: int, op_id: int, node_id: int) -> None:
    """Start a single offline node against the running cluster."""
    await asyncio.to_thread(set_operation_status, op_id, "running")

    try:
        node = await asyncio.to_thread(_load_node, node_id)
        if node is None:
            raise RecoveryError(f"Node {node_id} not found")

        await _broadcast_progress(
            cluster_id, op_id, "rejoin",
            f"Starting normal join for {node['name']}...",
        )

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            return

        await asyncio.to_thread(_start_node_normal, node)
        await _broadcast_progress(
            cluster_id, op_id, "rejoin",
            f"{node['name']} join started, waiting for SYNCED...",
        )

        synced = await _wait_node_synced(node, op_id, cluster_id)
        if not synced:
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                return
            raise RecoveryError(
                f"{node['name']} did not reach SYNCED within {_SYNCED_WAIT_TIMEOUT_SEC}s"
            )

        await asyncio.to_thread(set_operation_status, op_id, "success")
        await asyncio.to_thread(
            write_event,
            level="INFO",
            source="recovery",
            message=f"Rejoin operation {op_id}: {node['name']} rejoined successfully",
            cluster_id=cluster_id,
            operation_id=op_id,
        )
        await _broadcast_finished(cluster_id, op_id, success=True, message=f"{node['name']} rejoined successfully")

    except RecoveryError as exc:
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await asyncio.to_thread(
            write_event,
            level="ERROR",
            source="recovery",
            message=f"Rejoin operation {op_id} failed: {exc}",
            cluster_id=cluster_id,
            operation_id=op_id,
        )
        await _broadcast_finished(cluster_id, op_id, success=False, message=str(exc))
    except asyncio.CancelledError:
        await asyncio.to_thread(set_operation_status, op_id, "cancelled")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in rejoin op %d", op_id)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await _broadcast_finished(cluster_id, op_id, success=False, message=f"Internal error: {exc}")


# ── SSH helpers (all blocking, called via to_thread) ─────────────────────────────

def _scan_grastate(nodes: list[dict]) -> list[dict]:
    results = []
    for node in nodes:
        result = {
            "id":                node["id"],
            "name":              node["name"],
            "host":              node["host"],
            "safe_to_bootstrap": False,
            "seqno":             -1,
            "error":             None,
        }
        try:
            with SSHClient(
                    host=node["host"],
                    port=int(node.get("ssh_port") or 22),
                    username=node.get("ssh_user") or "root",
            ) as ssh:
                content, err = ssh.execute("cat /var/lib/mysql/grastate.dat")
                if err and not content:
                    raise SSHError(f"cat grastate.dat error: {err[:200]}")
                result["safe_to_bootstrap"] = _parse_grastate_bool(content, "safe_to_bootstrap")
                result["seqno"] = _parse_grastate_int(content, "seqno")
        except SSHError as exc:
            result["error"] = str(exc)
            logger.warning("Cannot read grastate.dat from %s: %s", node["name"], exc)

        results.append(result)
    return results


def _parse_grastate_bool(content: str, key: str) -> bool:
    """
    Parse a boolean field from grastate.dat content.
    Lines look like: safe_to_bootstrap: 1
    """
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(key + ":"):
            value = line.split(":", 1)[1].strip()
            return value == "1"
    return False


def _parse_grastate_int(content: str, key: str) -> int:
    """Parse an integer field from grastate.dat content."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(key + ":"):
            value = line.split(":", 1)[1].strip()
            try:
                return int(value)
            except ValueError:
                return -1
    return -1


def _select_bootstrap_candidate(scan_results: list[dict]) -> dict | None:
    """
    Select the best bootstrap candidate.

    Priority:
      1. Node with safe_to_bootstrap=1 AND highest seqno
      2. If no safe_to_bootstrap, node with highest seqno > 0 (risky, but best option)
      3. None — no viable candidate
    """
    reachable = [r for r in scan_results if r["error"] is None]
    if not reachable:
        return None

    # Prefer nodes explicitly marked safe_to_bootstrap
    safe_nodes = [r for r in reachable if r["safe_to_bootstrap"]]
    if safe_nodes:
        return max(safe_nodes, key=lambda r: r["seqno"])

    # Fallback: highest positive seqno
    positive = [r for r in reachable if r["seqno"] > 0]
    if positive:
        return max(positive, key=lambda r: r["seqno"])

    return None


def _start_bootstrap_node(node: dict) -> None:
    """
    Start MariaDB as a new cluster primary (bootstrap mode).
    Uses galera_new_cluster script which sets wsrep_cluster_address=gcomm://
    Per ТЗ раздел 13: use galera_new_cluster script.
    """
    with SSHClient(
        host=node["host"],
        port=int(node.get("ssh_port") or 22),
        username=node.get("ssh_user") or "root",
    ) as ssh:
        # Stop first in case it's partially running
        try:
            ssh.execute(f"systemctl stop {_MARIADB_SERVICE} 2>/dev/null || true")
        except SSHError:
            pass

        # galera_new_cluster starts MariaDB with gcomm://
        out, err = ssh.execute("galera_new_cluster")
        logger.info("galera_new_cluster on %s: stdout=%r stderr=%r", node["name"], out[:300], err[:300])

        if err and "error" in err.lower() and not out:
            raise RecoveryError(
                f"galera_new_cluster failed on {node['name']}: {err[:200]}"
            )


def _start_node_normal(node: dict) -> None:
    """
    Start MariaDB normally (rejoining an existing cluster).
    """
    with SSHClient(
        host=node["host"],
        port=int(node.get("ssh_port") or 22),
        username=node.get("ssh_user") or "root",
    ) as ssh:
        out, err = ssh.execute(f"systemctl start {_MARIADB_SERVICE}")
        logger.info("systemctl start mariadb on %s: stdout=%r stderr=%r", node["name"], out[:300], err[:300])
        if err and "failed" in err.lower():
            raise RecoveryError(
                f"systemctl start mariadb failed on {node['name']}: {err[:200]}"
            )


async def _wait_node_synced(
        node: dict,
        op_id: int,
        cluster_id: int,
        timeout_sec: int = _SYNCED_WAIT_TIMEOUT_SEC,
) -> bool:
    """
    Poll wsrep_local_state_comment via SSH until SYNCED or timeout.
    Checks cancel_requested between polls.
    Returns True if SYNCED, False if timeout or cancelled.
    """
    elapsed = 0
    while elapsed < timeout_sec:
        if await asyncio.to_thread(is_cancel_requested, op_id):
            return False

        state = await asyncio.to_thread(_get_wsrep_state_via_ssh, node)
        await _broadcast_progress(
            cluster_id, op_id, "waiting",
            f"{node['name']} wsrep state: {state} ({elapsed}s elapsed)",
        )

        if state == "Synced":
            return True

        await asyncio.sleep(_SYNCED_POLL_INTERVAL_SEC)
        elapsed += _SYNCED_POLL_INTERVAL_SEC

    return False


def _get_wsrep_state_via_ssh(node: dict) -> str:
    try:
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as ssh:
            # Используем db_user если есть, иначе доверяем ~/.my.cnf
            db_user = node.get("db_user") or ""
            user_flag = f"-u{db_user}" if db_user else ""
            out, _ = ssh.execute(
                f"mysql -Nse \"SHOW GLOBAL STATUS LIKE 'wsrep_local_state_comment'\" {user_flag}"
            )
            parts = out.strip().split()
            return parts[1] if len(parts) >= 2 else (parts[0] if parts else "OFFLINE")
    except SSHError:
        return "OFFLINE"


# ── DB helpers ───────────────────────────────────────────────────────────────────

def _load_cluster_nodes(cluster_id: int) -> list[dict]:
    """Load all enabled nodes for a cluster from SQLite."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, host, port, ssh_port, ssh_user, db_user, db_password, maintenance
                FROM nodes
                WHERE cluster_id = :cid AND enabled = 1
                ORDER BY id
                """
            ),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _load_node(node_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, name, host, port, ssh_port, ssh_user, "
                "db_user, db_password, maintenance FROM nodes WHERE id = :id"
            ),
            {"id": node_id},
        ).mappings().fetchone()
    return dict(row) if row else None


# ── WS broadcast helpers ──────────────────────────────────────────────────────────

async def _broadcast_progress(
        cluster_id: int,
        op_id: int,
        step: str,
        message: str,
        detail: dict | None = None,
) -> None:
    """Broadcast operation_progress WS event. Per ТЗ раздел 5.1."""
    event = {
        "event":      "operation_progress",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "operation_id": op_id,
            "step":         step,
            "message":      message,
            "detail":       detail,
        },
    }
    await ws_manager.broadcast(cluster_id, event)


async def _broadcast_finished(
        cluster_id: int,
        op_id: int,
        success: bool,
        message: str,
) -> None:
    """Broadcast operation_finished WS event."""
    event = {
        "event":      "operation_finished",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "operation_id": op_id,
            "success":      success,
            "message":      message,
        },
    }
    await ws_manager.broadcast(cluster_id, event)


# ── Errors ─────────────────────────────────────────────────────────────────────

class RecoveryError(Exception):
    """Raised when a recovery step fails."""
