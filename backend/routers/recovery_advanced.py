"""
Recovery Advanced Router — improvements batch v2.

New endpoints:
  GET  /api/clusters/{cluster_id}/recovery/grastate          — #3 grastate.dat inspector
  POST /api/clusters/{cluster_id}/recovery/snapshot          — #7 pre-flight node state snapshot
  GET  /api/clusters/{cluster_id}/recovery/ist-sst-info      — #8 IST vs SST helper
  POST /api/clusters/{cluster_id}/recovery/split-brain       — #6 Split-Brain Recovery wizard
  GET  /api/clusters/{cluster_id}/recovery/split-brain/status — poll split-brain op
  POST /api/clusters/{cluster_id}/recovery/full-cluster      — #9 Full Cluster Recovery
"""
from __future__ import annotations

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.event_log import write_event
from services.ssh_client import SSHClient, SSHError
from services.db_client import DBClient, DBError
from services.operations import (
    assert_no_active_operation,
    create_operation,
    get_active_operation,
    set_operation_status,
    is_cancel_requested,
)
from services.ws_manager import ws_manager
from services.recovery import _scan_grastate, _load_cluster_nodes, _broadcast_progress, _broadcast_finished, RecoveryError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clusters",
    tags=["recovery-advanced"],
    dependencies=[Depends(require_auth)],
)

# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_cluster_or_404(cluster_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name FROM clusters WHERE id = :cid"),
            {"cid": cluster_id},
        ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return dict(row)


def _get_enabled_nodes(cluster_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name, host, port, ssh_port, ssh_user, db_user, db_password
                FROM nodes
                WHERE cluster_id = :cid AND enabled = 1
                ORDER BY id
            """),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── #3 grastate.dat Inspector ────────────────────────────────────────────────

def _read_grastate_full(node: dict) -> dict:
    """Read and parse full grastate.dat from a node."""
    result = {
        "node_id": node["id"],
        "node_name": node["name"],
        "host": node["host"],
        "raw": None,
        "uuid": None,
        "seqno": None,
        "safe_to_bootstrap": None,
        "cert_index": None,
        "gvwstate_exists": False,
        "wsrep_recover_needed": False,
        "error": None,
    }
    try:
        with SSHClient(
            host=node["host"],
            port=int(node.get("ssh_port") or 22),
            username=node.get("ssh_user") or "root",
        ) as ssh:
            # Read grastate.dat
            content, err = ssh.execute("cat /var/lib/mysql/grastate.dat 2>/dev/null || echo '__NOT_FOUND__'")
            if "__NOT_FOUND__" in content or (err and not content.strip()):
                result["error"] = "grastate.dat not found — MySQL data directory may differ or MySQL is running"
                return result

            result["raw"] = content.strip()

            # Parse fields
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("uuid:"):
                    result["uuid"] = line.split(":", 1)[1].strip()
                elif line.startswith("seqno:"):
                    try:
                        result["seqno"] = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        result["seqno"] = -1
                elif line.startswith("safe_to_bootstrap:"):
                    result["safe_to_bootstrap"] = line.split(":", 1)[1].strip() == "1"
                elif line.startswith("cert_index:"):
                    result["cert_index"] = line.split(":", 1)[1].strip() or None

            # seqno = -1 means wsrep-recover is needed
            result["wsrep_recover_needed"] = result["seqno"] == -1

            # Check for gvwstate.dat (indicates node was part of a primary component)
            gvw_out, _ = ssh.execute("test -f /var/lib/mysql/gvwstate.dat && echo 'EXISTS' || echo 'ABSENT'")
            result["gvwstate_exists"] = "EXISTS" in gvw_out

    except SSHError as exc:
        result["error"] = str(exc)
    return result


@router.get("/{cluster_id}/recovery/grastate")
async def get_grastate(cluster_id: int) -> dict:
    """
    #3 grastate.dat Inspector.
    Reads grastate.dat from all enabled nodes and returns parsed fields.
    Highlights seqno=-1 (dirty crash), safe_to_bootstrap conflicts, max seqno node.
    """
    _get_cluster_or_404(cluster_id)
    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)

    if not nodes:
        return {"nodes": [], "analysis": {"max_seqno": None, "safe_bootstrap_count": 0, "warnings": []}}

    results = await asyncio.gather(
        *[asyncio.to_thread(_read_grastate_full, node) for node in nodes],
        return_exceptions=True,
    )

    node_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            node_results.append({
                "node_id": nodes[i]["id"],
                "node_name": nodes[i]["name"],
                "host": nodes[i]["host"],
                "error": str(r),
            })
        else:
            node_results.append(r)

    # Analysis
    reachable = [n for n in node_results if n.get("seqno") is not None]
    safe_nodes = [n for n in reachable if n.get("safe_to_bootstrap") is True]
    max_seqno = max((n["seqno"] for n in reachable if n.get("seqno", -1) >= 0), default=None)
    max_seqno_nodes = [n["node_name"] for n in reachable if n.get("seqno") == max_seqno] if max_seqno is not None else []

    warnings = []
    if len(safe_nodes) > 1:
        warnings.append({
            "level": "danger",
            "message": f"Multiple nodes have safe_to_bootstrap=1: {[n['node_name'] for n in safe_nodes]}. "
                       "Bootstrapping more than one will cause data loss!",
        })
    dirty_nodes = [n for n in reachable if n.get("seqno") == -1]
    if dirty_nodes:
        warnings.append({
            "level": "warn",
            "message": f"Nodes {[n['node_name'] for n in dirty_nodes]} have seqno=-1 (dirty crash). "
                       "Run 'mysqld --wsrep-recover' before bootstrapping.",
        })
    if not safe_nodes and reachable:
        warnings.append({
            "level": "warn",
            "message": "No node has safe_to_bootstrap=1. Recovery may require manual seqno comparison.",
        })

    return {
        "nodes": node_results,
        "analysis": {
            "max_seqno": max_seqno,
            "max_seqno_nodes": max_seqno_nodes,
            "safe_bootstrap_count": len(safe_nodes),
            "safe_bootstrap_nodes": [n["node_name"] for n in safe_nodes],
            "dirty_crash_count": len(dirty_nodes),
            "warnings": warnings,
        },
    }


# ── #7 Node State Snapshot (pre-flight dump) ─────────────────────────────────

def _collect_node_snapshot(node: dict) -> dict:
    """Collect point-in-time snapshot for pre-flight dump."""
    snap: dict[str, Any] = {
        "node_id": node["id"],
        "node_name": node["name"],
        "host": node["host"],
        "ssh_ok": False,
        "db_ok": False,
        "wsrep_status": None,
        "active_transactions": None,
        "top_processes": None,
        "disk_free_gb": None,
        "grastate": None,
        "error": None,
    }
    try:
        with SSHClient(
            host=node["host"],
            port=int(node.get("ssh_port") or 22),
            username=node.get("ssh_user") or "root",
        ) as ssh:
            snap["ssh_ok"] = True

            # grastate.dat
            gs_out, _ = ssh.execute("cat /var/lib/mysql/grastate.dat 2>/dev/null || echo ''")
            snap["grastate"] = gs_out.strip() or None

            # Disk free on /var/lib/mysql
            df_out, _ = ssh.execute("df -BG /var/lib/mysql 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G'")
            try:
                snap["disk_free_gb"] = float(df_out.strip())
            except ValueError:
                snap["disk_free_gb"] = None

            db_user = node.get("db_user") or "root"
            user_flag = f"-u{db_user}" if db_user else ""

            # SHOW STATUS wsrep
            ws_out, _ = ssh.execute(
                f"mysql -Nse \"SHOW GLOBAL STATUS WHERE Variable_name LIKE 'wsrep_%'\" {user_flag} 2>/dev/null"
            )
            if ws_out.strip():
                snap["db_ok"] = True
                wsrep: dict[str, str] = {}
                for line in ws_out.strip().splitlines():
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        wsrep[parts[0].strip()] = parts[1].strip()
                snap["wsrep_status"] = wsrep

            # Active transactions count
            trx_out, _ = ssh.execute(
                f"mysql -Nse \"SELECT COUNT(*) FROM information_schema.INNODB_TRX\" {user_flag} 2>/dev/null"
            )
            try:
                snap["active_transactions"] = int(trx_out.strip())
            except ValueError:
                snap["active_transactions"] = None

            # Top 5 processes by time
            ps_out, _ = ssh.execute(
                f"mysql -Nse \"SELECT ID, USER, COMMAND, TIME, STATE, INFO FROM information_schema.PROCESSLIST "
                f"WHERE COMMAND != 'Sleep' ORDER BY TIME DESC LIMIT 5\" {user_flag} 2>/dev/null"
            )
            if ps_out.strip():
                procs = []
                for line in ps_out.strip().splitlines():
                    cols = line.split("\t")
                    if len(cols) >= 5:
                        procs.append({
                            "id": cols[0], "user": cols[1], "command": cols[2],
                            "time": cols[3], "state": cols[4],
                            "info": cols[5][:100] if len(cols) > 5 else None,
                        })
                snap["top_processes"] = procs

    except SSHError as exc:
        snap["error"] = str(exc)
    return snap


@router.post("/{cluster_id}/recovery/snapshot")
async def take_snapshot(
    cluster_id: int,
    username: str = Depends(require_auth),
) -> dict:
    """
    #7 Pre-flight snapshot — collect point-in-time state from all nodes.
    Returns structured JSON dump with timestamp, safe to download.
    """
    _get_cluster_or_404(cluster_id)
    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)

    results = await asyncio.gather(
        *[asyncio.to_thread(_collect_node_snapshot, node) for node in nodes],
        return_exceptions=True,
    )

    node_snaps = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            node_snaps.append({
                "node_id": nodes[i]["id"],
                "node_name": nodes[i]["name"],
                "host": nodes[i]["host"],
                "error": str(r),
            })
        else:
            node_snaps.append(r)

    write_event(
        level="INFO",
        source="recovery",
        cluster_id=cluster_id,
        message=f"Pre-flight snapshot collected by '{username}' for cluster {cluster_id}",
    )

    return {
        "cluster_id": cluster_id,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "collected_by": username,
        "nodes": node_snaps,
    }


# ── #8 IST vs SST Decision Helper ────────────────────────────────────────────

def _get_ist_sst_info_for_node(node: dict) -> dict:
    """Collect IST/SST decision data for a single node."""
    info: dict[str, Any] = {
        "node_id": node["id"],
        "node_name": node["name"],
        "host": node["host"],
        "wsrep_local_state_comment": None,
        "wsrep_local_cached_downtime": None,
        "gcache_size_bytes": None,
        "gcache_file_size_bytes": None,
        "sst_method": None,
        "wsrep_provider_options": None,
        "ist_likely": None,
        "error": None,
    }
    try:
        db_client = DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node.get("db_user") or "root",
            encrypted_password=node.get("db_password") or "",
        )
        db_client.connect()
        try:
            # wsrep state and key status vars
            rows = db_client.query(
                "SHOW GLOBAL STATUS WHERE Variable_name IN ("
                "'wsrep_local_state_comment','wsrep_local_cached_downtime',"
                "'wsrep_flow_control_paused')"
            )
            status_map = {r.get("Variable_name", r.get("variable_name", "")).lower(): r.get("Value", r.get("value", "")) for r in rows}
            info["wsrep_local_state_comment"] = status_map.get("wsrep_local_state_comment")
            try:
                info["wsrep_local_cached_downtime"] = int(status_map.get("wsrep_local_cached_downtime", 0) or 0)
            except (ValueError, TypeError):
                info["wsrep_local_cached_downtime"] = None

            # Provider options (contains gcache.size)
            prov_rows = db_client.query(
                "SHOW GLOBAL VARIABLES LIKE 'wsrep_provider_options'"
            )
            if prov_rows:
                prov_val = prov_rows[0].get("Value") or prov_rows[0].get("value") or ""
                info["wsrep_provider_options"] = prov_val
                # Parse gcache.size from options string
                for part in prov_val.split(";"):
                    part = part.strip()
                    if "gcache.size" in part:
                        try:
                            val_str = part.split("=", 1)[1].strip()
                            # Convert M/G suffixes
                            if val_str.endswith("M"):
                                info["gcache_size_bytes"] = int(float(val_str[:-1]) * 1024 * 1024)
                            elif val_str.endswith("G"):
                                info["gcache_size_bytes"] = int(float(val_str[:-1]) * 1024 * 1024 * 1024)
                            else:
                                info["gcache_size_bytes"] = int(val_str)
                        except (ValueError, IndexError):
                            pass

            # SST method
            sst_rows = db_client.query("SHOW GLOBAL VARIABLES LIKE 'wsrep_sst_method'")
            if sst_rows:
                info["sst_method"] = sst_rows[0].get("Value") or sst_rows[0].get("value")

        finally:
            db_client.close()

        # Check gcache file size on disk via SSH
        try:
            with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
            ) as ssh:
                out, _ = ssh.execute(
                    "stat -c%s /var/lib/mysql/galera.cache 2>/dev/null || "
                    "stat -c%s /var/lib/mysql/gcache.page 2>/dev/null || echo ''"
                )
                try:
                    info["gcache_file_size_bytes"] = int(out.strip())
                except ValueError:
                    pass
        except SSHError:
            pass

        # Heuristic: IST is likely if wsrep_local_cached_downtime is low
        # and gcache is large enough. Simplified: if node was down < 10min (600s)
        # and gcache > 128MB → IST likely
        downtime = info["wsrep_local_cached_downtime"]
        gcache = info["gcache_size_bytes"] or 0
        if downtime is not None:
            info["ist_likely"] = downtime < 600 and gcache > 128 * 1024 * 1024
        else:
            info["ist_likely"] = None

    except DBError as exc:
        info["error"] = str(exc)

    return info


@router.get("/{cluster_id}/recovery/ist-sst-info")
async def get_ist_sst_info(cluster_id: int) -> dict:
    """
    #8 IST vs SST Decision Helper.
    For each online node: gcache size, wsrep_local_cached_downtime, sst_method.
    Returns per-node assessment of whether IST or SST will be used on next rejoin.
    """
    _get_cluster_or_404(cluster_id)
    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)

    results = await asyncio.gather(
        *[asyncio.to_thread(_get_ist_sst_info_for_node, node) for node in nodes],
        return_exceptions=True,
    )

    node_infos = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            node_infos.append({
                "node_id": nodes[i]["id"],
                "node_name": nodes[i]["name"],
                "host": nodes[i]["host"],
                "error": str(r),
            })
        else:
            node_infos.append(r)

    return {"nodes": node_infos}


# ── #6 Split-Brain Recovery Wizard ───────────────────────────────────────────

class SplitBrainRecoverRequest(BaseModel):
    trusted_node_id: int  # node to bootstrap from non-primary state


async def _run_split_brain_recovery(cluster_id: int, op_id: int, trusted_node_id: int) -> None:
    """
    Split-Brain recovery: set pc.bootstrap=YES on the trusted node,
    wait for it to become PRIMARY, then let other nodes rejoin.
    """
    await asyncio.to_thread(set_operation_status, op_id, "running")
    try:
        nodes = await asyncio.to_thread(_load_cluster_nodes, cluster_id)
        trusted = next((n for n in nodes if n["id"] == trusted_node_id), None)
        if trusted is None:
            raise RecoveryError(f"Trusted node {trusted_node_id} not found in cluster {cluster_id}")

        await _broadcast_progress(cluster_id, op_id, "bootstrap",
            f"Setting pc.bootstrap=YES on {trusted['name']}...")

        # Step 1: SET GLOBAL wsrep_provider_options='pc.bootstrap=YES'
        await asyncio.to_thread(_set_pc_bootstrap, trusted)

        await _broadcast_progress(cluster_id, op_id, "bootstrap",
            f"pc.bootstrap=YES issued on {trusted['name']}, waiting for PRIMARY state...")

        # Step 2: Wait for PRIMARY
        primary = await _wait_for_primary(trusted, op_id, cluster_id)
        if not primary:
            raise RecoveryError(
                f"{trusted['name']} did not reach PRIMARY component within 120s"
            )

        await _broadcast_progress(cluster_id, op_id, "rejoin",
            f"{trusted['name']} is PRIMARY — cluster is live again")

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            return

        # Step 3: Restart remaining nodes so they can rejoin
        remaining = [n for n in nodes if n["id"] != trusted_node_id]
        for i, node in enumerate(remaining, 1):
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                return

            await _broadcast_progress(cluster_id, op_id, "rejoin",
                f"Restarting {node['name']} ({i}/{len(remaining)})...",
                detail={"node_id": node["id"], "node_name": node["name"]})
            try:
                await asyncio.to_thread(_restart_node_mariadb, node)
            except RecoveryError as exc:
                await _broadcast_progress(cluster_id, op_id, "rejoin",
                    f"WARNING: {node['name']} restart failed: {exc} (continuing)")

        await asyncio.to_thread(set_operation_status, op_id, "success")
        write_event(level="INFO", source="recovery", cluster_id=cluster_id,
            operation_id=op_id,
            message=f"Split-Brain recovery op {op_id} completed on cluster {cluster_id}")
        await _broadcast_finished(cluster_id, op_id, success=True,
            message="Split-Brain recovery complete")

    except RecoveryError as exc:
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        write_event(level="ERROR", source="recovery", cluster_id=cluster_id,
            operation_id=op_id, message=f"Split-Brain recovery failed: {exc}")
        await _broadcast_finished(cluster_id, op_id, success=False, message=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in split-brain op %d", op_id)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await _broadcast_finished(cluster_id, op_id, success=False, message=f"Internal error: {exc}")


def _set_pc_bootstrap(node: dict) -> None:
    db = DBClient(
        host=node["host"],
        port=int(node.get("port") or 3306),
        user=node.get("db_user") or "root",
        encrypted_password=node.get("db_password") or "",
    )
    db.connect()
    try:
        db.execute("SET GLOBAL wsrep_provider_options='pc.bootstrap=YES'")
    finally:
        db.close()


async def _wait_for_primary(node: dict, op_id: int, cluster_id: int, timeout_sec: int = 120) -> bool:
    elapsed = 0
    while elapsed < timeout_sec:
        if await asyncio.to_thread(is_cancel_requested, op_id):
            return False
        try:
            state = await asyncio.to_thread(_get_wsrep_cluster_status, node)
            await _broadcast_progress(cluster_id, op_id, "waiting",
                f"{node['name']} wsrep_cluster_status: {state} ({elapsed}s)")
            if state == "Primary":
                return True
        except Exception:
            pass
        await asyncio.sleep(5)
        elapsed += 5
    return False


def _get_wsrep_cluster_status(node: dict) -> str:
    db = DBClient(
        host=node["host"],
        port=int(node.get("port") or 3306),
        user=node.get("db_user") or "root",
        encrypted_password=node.get("db_password") or "",
    )
    db.connect()
    try:
        rows = db.query("SHOW GLOBAL STATUS LIKE 'wsrep_cluster_status'")
        if rows:
            return rows[0].get("Value") or rows[0].get("value") or "unknown"
        return "unknown"
    finally:
        db.close()


def _restart_node_mariadb(node: dict) -> None:
    with SSHClient(
        host=node["host"],
        port=int(node.get("ssh_port") or 22),
        username=node.get("ssh_user") or "root",
    ) as ssh:
        out, err = ssh.execute("systemctl restart mariadb 2>&1 || true")
        logger.info("systemctl restart mariadb on %s: %r %r", node["name"], out[:200], err[:200])


@router.post("/{cluster_id}/recovery/split-brain", status_code=202)
async def start_split_brain_recovery(
    cluster_id: int,
    body: SplitBrainRecoverRequest,
    username: str = Depends(require_auth),
) -> dict:
    """
    #6 Split-Brain Recovery Wizard.
    Sets pc.bootstrap=YES on the trusted node, waits for PRIMARY,
    then restarts remaining nodes to rejoin.
    """
    _get_cluster_or_404(cluster_id)
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="recovery_split_brain",
        target_node_id=body.trusted_node_id,
        created_by=username,
    )

    asyncio.create_task(
        _run_split_brain_recovery(cluster_id, op_id, body.trusted_node_id),
        name=f"split-brain-{cluster_id}",
    )

    write_event(level="INFO", source="recovery", cluster_id=cluster_id,
        operation_id=op_id,
        message=f"Split-Brain recovery started by '{username}', trusted node {body.trusted_node_id}")

    return {
        "accepted": True,
        "operation_id": op_id,
        "message": "Split-Brain recovery started. Subscribe to WS for progress.",
    }


# ── #9 Full Cluster Recovery ─────────────────────────────────────────────────

class FullClusterRecoveryRequest(BaseModel):
    node_order: list[int]  # ordered list of node IDs: first = bootstrap donor, rest = rejoin sequence


async def _run_full_cluster_recovery(
    cluster_id: int,
    op_id: int,
    node_order: list[int],
) -> None:
    """
    Full Cluster Recovery: bootstrap first node, then sequentially rejoin remaining.
    """
    from services.recovery import (
        _start_bootstrap_node, _start_node_normal, _wait_node_synced,
        _SYNCED_WAIT_TIMEOUT_SEC,
    )

    await asyncio.to_thread(set_operation_status, op_id, "running")
    total = len(node_order)

    try:
        all_nodes = await asyncio.to_thread(_load_cluster_nodes, cluster_id)
        node_map = {n["id"]: n for n in all_nodes}

        donor_id = node_order[0]
        donor = node_map.get(donor_id)
        if donor is None:
            raise RecoveryError(f"Node {donor_id} not found in cluster {cluster_id}")

        # Step 1: Bootstrap donor
        await _broadcast_progress(cluster_id, op_id, "bootstrap",
            f"[1/{total}] Bootstrapping {donor['name']} (gcomm://)...",
            detail={"node_id": donor_id, "step_num": 1, "total": total})

        if await asyncio.to_thread(is_cancel_requested, op_id):
            await asyncio.to_thread(set_operation_status, op_id, "cancelled")
            return

        await asyncio.to_thread(_start_bootstrap_node, donor)

        await _broadcast_progress(cluster_id, op_id, "bootstrap",
            f"[1/{total}] {donor['name']} bootstrap started, waiting for SYNCED...")

        synced = await _wait_node_synced(donor, op_id, cluster_id)
        if not synced:
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                return
            raise RecoveryError(f"Bootstrap node {donor['name']} did not reach SYNCED within {_SYNCED_WAIT_TIMEOUT_SEC}s")

        await _broadcast_progress(cluster_id, op_id, "bootstrap",
            f"[1/{total}] {donor['name']} is SYNCED — cluster primary is live")

        # Step 2..N: Sequential rejoin
        remaining_ids = node_order[1:]
        for idx, node_id in enumerate(remaining_ids, 2):
            if await asyncio.to_thread(is_cancel_requested, op_id):
                await asyncio.to_thread(set_operation_status, op_id, "cancelled")
                return

            node = node_map.get(node_id)
            if node is None:
                await _broadcast_progress(cluster_id, op_id, "rejoin",
                    f"[{idx}/{total}] Node {node_id} not found — skipping",
                    detail={"node_id": node_id, "step_num": idx, "total": total})
                continue

            await _broadcast_progress(cluster_id, op_id, "rejoin",
                f"[{idx}/{total}] Joining {node['name']}...",
                detail={"node_id": node_id, "node_name": node["name"], "step_num": idx, "total": total})

            try:
                await asyncio.to_thread(_start_node_normal, node)
                await _broadcast_progress(cluster_id, op_id, "rejoin",
                    f"[{idx}/{total}] {node['name']} join started, waiting for SYNCED...")

                synced = await _wait_node_synced(node, op_id, cluster_id)
                if synced:
                    await _broadcast_progress(cluster_id, op_id, "rejoin",
                        f"[{idx}/{total}] {node['name']} is SYNCED",
                        detail={"node_id": node_id, "node_name": node["name"],
                                "step_num": idx, "total": total, "synced": True})
                else:
                    await _broadcast_progress(cluster_id, op_id, "rejoin",
                        f"[{idx}/{total}] WARNING: {node['name']} did not reach SYNCED — continuing",
                        detail={"node_id": node_id, "node_name": node["name"],
                                "step_num": idx, "total": total, "synced": False})
            except RecoveryError as exc:
                await _broadcast_progress(cluster_id, op_id, "rejoin",
                    f"[{idx}/{total}] WARNING: {node['name']} failed: {exc} — continuing")

        await asyncio.to_thread(set_operation_status, op_id, "success")
        write_event(level="INFO", source="recovery", cluster_id=cluster_id,
            operation_id=op_id,
            message=f"Full Cluster Recovery op {op_id} completed for cluster {cluster_id}")
        await _broadcast_finished(cluster_id, op_id, success=True,
            message=f"Full Cluster Recovery complete ({total} nodes)")

    except RecoveryError as exc:
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        write_event(level="ERROR", source="recovery", cluster_id=cluster_id,
            operation_id=op_id, message=f"Full Cluster Recovery failed: {exc}")
        await _broadcast_finished(cluster_id, op_id, success=False, message=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in full-cluster-recovery op %d", op_id)
        await asyncio.to_thread(set_operation_status, op_id, "failed", str(exc))
        await _broadcast_finished(cluster_id, op_id, success=False, message=f"Internal error: {exc}")


@router.post("/{cluster_id}/recovery/full-cluster", status_code=202)
async def start_full_cluster_recovery(
    cluster_id: int,
    body: FullClusterRecoveryRequest,
    username: str = Depends(require_auth),
) -> dict:
    """
    #9 Full Cluster Recovery.
    Bootstraps the first node in node_order, then sequentially rejoins the rest,
    waiting for SYNCED at each step before proceeding to the next.
    """
    _get_cluster_or_404(cluster_id)
    if not body.node_order:
        raise HTTPException(status_code=422, detail="node_order must not be empty")

    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="recovery_full_cluster",
        target_node_id=body.node_order[0],
        created_by=username,
    )

    asyncio.create_task(
        _run_full_cluster_recovery(cluster_id, op_id, body.node_order),
        name=f"full-cluster-recovery-{cluster_id}",
    )

    write_event(level="INFO", source="recovery", cluster_id=cluster_id,
        operation_id=op_id,
        message=f"Full Cluster Recovery started by '{username}', order={body.node_order}")

    return {
        "accepted": True,
        "operation_id": op_id,
        "message": "Full Cluster Recovery started. Subscribe to WS for progress.",
    }
