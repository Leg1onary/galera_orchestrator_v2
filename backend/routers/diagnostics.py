# backend/routers/diagnostics.py
#
# Phase 4 — Diagnostics backend
# Endpoints (ТЗ раздел 15):
#   POST /api/clusters/{cluster_id}/diagnostics/check-all
#   POST /api/clusters/{cluster_id}/diagnostics/resources
#   GET  /api/clusters/{cluster_id}/diagnostics/config-diff
#   GET  /api/clusters/{cluster_id}/diagnostics/variables
#   GET  /api/clusters/{cluster_id}/diagnostics/variables/all
#   GET  /api/clusters/{cluster_id}/diagnostics/galera-status
#   GET  /api/clusters/{cluster_id}/diagnostics/process-list
#   GET  /api/clusters/{cluster_id}/diagnostics/slow-queries
#     ?node_id=N  — filter by node
#     ?min_query_time=N  — minimum query time in seconds (default 0)
#     ?limit=N  — max rows per node (default 200, max 2000)
#   GET  /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status
#   GET  /api/clusters/{cluster_id}/nodes/{node_id}/error-log
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/test-connection
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/log
#   POST /api/clusters/{cluster_id}/diagnostics/nodes/{node_id}/slow-query-log/toggle

from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from config import settings
from database import engine
from dependencies import require_auth
from services.db_client import DBClient, DBError
from services.event_log import write_event
from services.ssh_client import SSHClient, SSHError

router = APIRouter(
    prefix="/clusters",
    tags=["diagnostics"],
    dependencies=[Depends(require_auth)],
)


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers (inline SQL, same pattern as other routers)
# ─────────────────────────────────────────────────────────────────────────────

def _assert_cluster_exists(cluster_id: int) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM clusters WHERE id = :cid"),
            {"cid": cluster_id},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")


def _get_active_nodes(cluster_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT n.*, d.name AS datacenter_name
                FROM nodes n
                LEFT JOIN datacenters d ON d.id = n.datacenter_id
                WHERE n.cluster_id = :cid AND n.enabled = 1
                ORDER BY n.name
            """),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _get_node_for_cluster(node_id: int, cluster_id: int) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT n.*, d.name AS datacenter_name
                FROM nodes n
                LEFT JOIN datacenters d ON d.id = n.datacenter_id
                WHERE n.id = :nid AND n.cluster_id = :cid AND n.enabled = 1
            """),
            {"nid": node_id, "cid": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def _get_arbitrator_by_id(arb_id: int, cluster_id: int) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM arbitrators WHERE id = :aid AND cluster_id = :cid"),
            {"aid": arb_id, "cid": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def _hms_to_sec(hms: str | None) -> float:
    """Convert HH:MM:SS.ffffff to total seconds (float)."""
    if not hms:
        return 0.0
    try:
        parts = hms.split(":")
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# POST /diagnostics/check-all
# ─────────────────────────────────────────────────────────────────────────────

def _check_node(node: dict) -> dict:
    checks: dict[str, Any] = {}
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW STATUS LIKE 'wsrep_cluster_status'")
            checks["wsrep_cluster_status"] = rows[0]["Value"] if rows else None

            rows = client.query("SHOW STATUS LIKE 'wsrep_local_state_comment'")
            checks["wsrep_local_state_comment"] = rows[0]["Value"] if rows else None

            rows = client.query("SHOW STATUS LIKE 'wsrep_cluster_size'")
            checks["wsrep_cluster_size"] = int(rows[0]["Value"]) if rows else None

            sl = client.query("SHOW SLAVE STATUS")
            checks["seconds_behind_master"] = sl[0].get("Seconds_Behind_Master") if sl else None

            mc = client.query("SHOW VARIABLES LIKE 'max_connections'")
            tc = client.query("SHOW STATUS LIKE 'Threads_connected'")
            checks["max_connections"] = int(mc[0]["Value"]) if mc else None
            checks["threads_connected"] = int(tc[0]["Value"]) if tc else None

    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)

    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "checks":    checks,
        "error":     error,
    }


@router.post("/{cluster_id}/diagnostics/check-all")
async def diagnostics_check_all(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_check_node, n) for n in nodes
    ])
    return list(results)


# ─────────────────────────────────────────────────────────────────────────────
# POST /diagnostics/resources  (SSH-based: CPU, RAM, disk)
# ─────────────────────────────────────────────────────────────────────────────

RES_CMDS = {
    "cpu_pct":   "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'",
    "ram_used":  "free -m | awk '/Mem:/{print $3}'",
    "ram_total": "free -m | awk '/Mem:/{print $2}'",
    "disk_used": "df -m / | awk 'NR==2{print $3}'",
    "disk_total":"df -m / | awk 'NR==2{print $2}'",
}


def _fetch_resources_ssh(node: dict) -> dict:
    results: dict[str, Any] = {}
    error: str | None = None
    try:
        with SSHClient(
            host=node["host"],
            user=node["ssh_user"],
            key_path=settings.SSH_KEY_PATH,
            port=int(node.get("ssh_port") or 22),
        ) as ssh:
            for key, cmd in RES_CMDS.items():
                out = ssh.execute(cmd).strip()
                try:
                    results[key] = float(out)
                except ValueError:
                    results[key] = None
    except SSHError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "resources": results,
        "error":     error,
    }


@router.post("/{cluster_id}/diagnostics/resources")
async def diagnostics_resources(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_resources_ssh, n) for n in nodes
    ])
    return list(results)


# ─────────────────────────────────────────────────────────────────────────────
# GET /diagnostics/config-diff
# ─────────────────────────────────────────────────────────────────────────────

VAR_NAMES_FOR_DIFF = [
    "innodb_buffer_pool_size", "innodb_log_file_size", "max_connections",
    "query_cache_size", "query_cache_type", "slow_query_log",
    "long_query_time", "wsrep_provider_options", "wsrep_slave_threads",
    "wsrep_sync_wait", "binlog_format", "character_set_server",
    "collation_server", "tx_isolation", "max_allowed_packet",
]


def _fetch_vars_for_diff(node: dict) -> dict:
    values: dict[str, str] = {}
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL VARIABLES")
            row_map = {r["Variable_name"]: r["Value"] for r in rows}
            for name in VAR_NAMES_FOR_DIFF:
                values[name] = row_map.get(name, "N/A")
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "variables": values,
        "error":     error,
    }


@router.get("/{cluster_id}/diagnostics/config-diff")
async def diagnostics_config_diff(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    node_data = await asyncio.gather(*[
        asyncio.to_thread(_fetch_vars_for_diff, n) for n in nodes
    ])

    diffs: dict[str, dict] = {}
    for var in VAR_NAMES_FOR_DIFF:
        vals = {nd["node_name"]: nd["variables"].get(var) for nd in node_data if not nd["error"]}
        if len(set(vals.values())) > 1:
            diffs[var] = vals

    return {
        "nodes": [{"node_id": nd["node_id"], "node_name": nd["node_name"]} for nd in node_data],
        "diffs": diffs,
        "node_errors": [
            {"node_id": nd["node_id"], "node_name": nd["node_name"], "error": nd["error"]}
            for nd in node_data if nd["error"]
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /diagnostics/variables  &  /diagnostics/variables/all
# ─────────────────────────────────────────────────────────────────────────────

KEY_VARS = [
    "innodb_buffer_pool_size", "innodb_log_file_size", "max_connections",
    "slow_query_log", "long_query_time", "wsrep_slave_threads",
    "wsrep_sync_wait", "binlog_format", "query_cache_size",
]


def _fetch_node_variables(node: dict, only_key: bool) -> dict:
    values: list[dict] = []
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL VARIABLES")
            for r in rows:
                if only_key and r["Variable_name"] not in KEY_VARS:
                    continue
                values.append({"name": r["Variable_name"], "value": r["Value"]})
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "variables": values,
        "error":     error,
    }


@router.get("/{cluster_id}/diagnostics/variables")
async def diagnostics_variables(
        cluster_id: int,
        node_id: Optional[int] = Query(None),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    if node_id:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_node_variables, n, True) for n in nodes
    ])
    return list(results)


@router.get("/{cluster_id}/diagnostics/variables/all")
async def diagnostics_variables_all(
        cluster_id: int,
        node_id: Optional[int] = Query(None),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    if node_id:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_node_variables, n, False) for n in nodes
    ])
    return list(results)


# ─────────────────────────────────────────────────────────────────────────────
# GET /diagnostics/galera-status
# ─────────────────────────────────────────────────────────────────────────────

WSREP_STATUS_VARS = [
    "wsrep_cluster_status", "wsrep_cluster_size", "wsrep_local_state_comment",
    "wsrep_local_recv_queue_avg", "wsrep_local_send_queue_avg",
    "wsrep_flow_control_paused", "wsrep_cert_deps_distance",
    "wsrep_apply_oooe", "wsrep_commit_oooe",
    "wsrep_received_bytes", "wsrep_replicated_bytes",
    "wsrep_connected", "wsrep_ready",
]


def _fetch_galera_status(node: dict) -> dict:
    values: dict[str, str] = {}
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW STATUS LIKE 'wsrep_%'")
            row_map = {r["Variable_name"]: r["Value"] for r in rows}
            for name in WSREP_STATUS_VARS:
                values[name] = row_map.get(name, "N/A")
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "status":    values,
        "error":     error,
    }


@router.get("/{cluster_id}/diagnostics/galera-status")
async def diagnostics_galera_status(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_galera_status, n) for n in nodes
    ])
    return list(results)


# ─────────────────────────────────────────────────────────────────────────────
# GET /diagnostics/process-list
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_process_list(node: dict) -> dict:
    rows: list[dict] = []
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            raw = client.query("SHOW FULL PROCESSLIST")
            rows = [
                {
                    "id":      r.get("Id"),
                    "user":    r.get("User"),
                    "host":    r.get("Host"),
                    "db":      r.get("db"),
                    "command": r.get("Command"),
                    "time":    r.get("Time"),
                    "state":   r.get("State"),
                    "info":    r.get("Info"),
                }
                for r in raw
            ]
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "processes": rows,
        "error":     error,
    }


@router.get("/{cluster_id}/diagnostics/process-list")
async def diagnostics_process_list(
        cluster_id: int,
        node_id: Optional[int] = Query(None),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    if node_id:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_process_list, n) for n in nodes
    ])
    return list(results)


# ─────────────────────────────────────────────────────────────────────────────
# GET /diagnostics/slow-queries
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_slow_queries(node: dict, min_query_time: float, limit: int) -> dict:
    rows: list[dict] = []
    error: str | None = None
    slow_log_enabled: bool | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            var_rows = client.query("SHOW GLOBAL VARIABLES LIKE 'slow_query_log'")
            if var_rows:
                slow_log_enabled = var_rows[0]["Value"].upper() == "ON"
            else:
                slow_log_enabled = False

            if slow_log_enabled:
                if min_query_time > 0:
                    sql = (
                        f"SELECT * FROM mysql.slow_log "
                        f"WHERE query_time >= SEC_TO_TIME({min_query_time}) "
                        f"ORDER BY start_time DESC "
                        f"LIMIT {limit}"
                    )
                else:
                    sql = (
                        f"SELECT * FROM mysql.slow_log "
                        f"ORDER BY start_time DESC "
                        f"LIMIT {limit}"
                    )
                raw = client.query(sql)
                rows = [
                    {
                        "start_time":    str(r.get("start_time", "")),
                        "user_host":     r.get("user_host", ""),
                        "query_time":    str(r.get("query_time", "")),
                        "lock_time":     str(r.get("lock_time", "")),
                        "rows_sent":     r.get("rows_sent"),
                        "rows_examined": r.get("rows_examined"),
                        "db":            r.get("db", ""),
                        "sql_text":      r.get("sql_text", ""),
                    }
                    for r in raw
                ]
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)

    return {
        "node_id":          node["id"],
        "node_name":        node["name"],
        "slow_log_enabled": slow_log_enabled,
        "rows":             rows,
        "error":            error,
    }


@router.get("/{cluster_id}/diagnostics/slow-queries")
async def diagnostics_slow_queries(
        cluster_id: int,
        node_id: Optional[int] = Query(None),
        min_query_time: float = Query(
            0.0,
            ge=0.0,
            le=86400.0,
            description="Minimum query time in seconds (e.g. 1.0). Default 0 = no filter.",
        ),
        limit: int = Query(
            200,
            ge=10,
            le=2000,
            description="Max rows returned per node. Default 200.",
        ),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_active_nodes(cluster_id)
    if node_id:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_slow_queries, n, min_query_time, limit) for n in nodes
    ])
    return list(results)


# ── POST /diagnostics/nodes/{node_id}/slow-query-log/toggle ──────────────────

def _toggle_slow_query_log(node: dict, enable: bool) -> dict:
    """Execute SET GLOBAL slow_query_log = ON/OFF on a single node."""
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "enabled":   None,
            "error":     "No DB credentials configured",
        }
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            value = "ON" if enable else "OFF"
            client.execute(f"SET GLOBAL slow_query_log = {value}")
            var_rows = client.query("SHOW GLOBAL VARIABLES LIKE 'slow_query_log'")
            actual = (var_rows[0]["Value"].upper() == "ON") if var_rows else enable
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "enabled":   actual,
            "error":     None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "enabled":   None,
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "enabled":   None,
            "error":     str(exc),
        }


@router.post("/{cluster_id}/diagnostics/nodes/{node_id}/slow-query-log/toggle")
async def toggle_slow_query_log(
        cluster_id: int,
        node_id: int,
        enable: bool = Query(..., description="true to enable, false to disable"),
) -> dict:
    """
    Dynamically toggle slow_query_log ON/OFF on a single node via SET GLOBAL.
    Note: runtime change only — does NOT persist across MariaDB restarts.
    """
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
        )

    result = await asyncio.to_thread(_toggle_slow_query_log, node, enable)

    level  = "INFO" if result["error"] is None else "WARN"
    action = "enabled" if enable else "disabled"
    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        node_id=node_id,
        source="diagnostics",
        level=level,
        message=(
            f"slow_query_log toggle: {action} on {node['name']}"
            + (f" — error: {result['error']}" if result["error"] else "")
        ),
    )

    return result


# ── GET /nodes/{node_id}/error-log ────────────────────────────────────────────

def _fetch_error_log_ssh(node: dict, lines: int) -> dict:
    content: str | None = None
    error: str | None = None
    try:
        with SSHClient(
            host=node["host"],
            user=node["ssh_user"],
            key_path=settings.SSH_KEY_PATH,
            port=int(node.get("ssh_port") or 22),
        ) as ssh:
            cmd = (
                f"tail -n {lines} $(mysql -N -B -e \"SELECT @@log_error\" 2>/dev/null "
                "|| echo '/var/log/mysql/error.log')"
            )
            content = ssh.execute(cmd)
    except SSHError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "content":   content,
        "error":     error,
    }


@router.get("/{cluster_id}/nodes/{node_id}/error-log")
async def node_error_log(
        cluster_id: int,
        node_id: int,
        lines: int = Query(200, ge=10, le=2000),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found in cluster {cluster_id}")
    return await asyncio.to_thread(_fetch_error_log_ssh, node, lines)


# ── GET /nodes/{node_id}/innodb-status ────────────────────────────────────────

def _fetch_innodb_status(node: dict) -> dict:
    content: str | None = None
    error: str | None = None
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW ENGINE INNODB STATUS")
            if rows:
                content = rows[0].get("Status", "")
    except DBError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "content":   content,
        "error":     error,
    }


@router.get("/{cluster_id}/nodes/{node_id}/innodb-status")
async def node_innodb_status(cluster_id: int, node_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found in cluster {cluster_id}")
    return await asyncio.to_thread(_fetch_innodb_status, node)


# ── GET /arbitrators/{arb_id}/test-connection ─────────────────────────────────

def _test_arb_connection(arb: dict) -> dict:
    import time
    success = False
    latency_ms: float | None = None
    error: str | None = None
    try:
        t0 = time.perf_counter()
        with SSHClient(
            host=arb["host"],
            user=arb.get("ssh_user", "root"),
            key_path=settings.SSH_KEY_PATH,
            port=int(arb.get("ssh_port") or 22),
        ) as ssh:
            ssh.execute("echo ok")
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        success = True
    except SSHError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "arb_id":     arb["id"],
        "arb_name":   arb.get("name", arb["host"]),
        "success":    success,
        "latency_ms": latency_ms,
        "error":      error,
    }


@router.get("/{cluster_id}/arbitrators/{arb_id}/test-connection")
async def arb_test_connection(cluster_id: int, arb_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_by_id(arb_id, cluster_id)
    if not arb:
        raise HTTPException(status_code=404, detail=f"Arbitrator {arb_id} not found")
    return await asyncio.to_thread(_test_arb_connection, arb)


# ── GET /arbitrators/{arb_id}/log ─────────────────────────────────────────────

GARB_LOG_PATHS = [
    "/var/log/garbd.log",
    "/var/log/garb/garbd.log",
    "/var/log/garb.log",
    "/tmp/garbd.log",
]


def _fetch_arb_log_ssh(arb: dict, lines: int) -> dict:
    content: str | None = None
    error: str | None = None
    try:
        with SSHClient(
            host=arb["host"],
            user=arb.get("ssh_user", "root"),
            key_path=settings.SSH_KEY_PATH,
            port=int(arb.get("ssh_port") or 22),
        ) as ssh:
            for path in GARB_LOG_PATHS:
                test = ssh.execute(f"test -f {path} && echo yes || echo no").strip()
                if test == "yes":
                    content = ssh.execute(f"tail -n {lines} {path}")
                    break
            if content is None:
                content = ssh.execute(
                    f"journalctl -u garbd -n {lines} --no-pager 2>/dev/null || echo 'Log not found'"
                )
    except SSHError as exc:
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "arb_id":   arb["id"],
        "arb_name": arb.get("name", arb["host"]),
        "content":  content,
        "error":    error,
    }


@router.get("/{cluster_id}/arbitrators/{arb_id}/log")
async def arb_log(
        cluster_id: int,
        arb_id: int,
        lines: int = Query(200, ge=10, le=2000),
) -> dict:
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_by_id(arb_id, cluster_id)
    if not arb:
        raise HTTPException(status_code=404, detail=f"Arbitrator {arb_id} not found")
    return await asyncio.to_thread(_fetch_arb_log_ssh, arb, lines)
