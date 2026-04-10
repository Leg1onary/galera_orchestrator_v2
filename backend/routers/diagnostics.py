# backend/routers/diagnostics.py
#
# Phase 4 — Diagnostics backend
# Endpoints (ТЗ раздел 15):
#   POST /api/clusters/{cluster_id}/diagnostics/check-all
#   GET  /api/clusters/{cluster_id}/diagnostics/config-diff
#   GET  /api/clusters/{cluster_id}/diagnostics/variables
#   POST /api/clusters/{cluster_id}/diagnostics/resources
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/test-connection
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/log
#
# innodb-status живёт в routers/nodes.py — здесь не дублируется.
# Таймауты (ТЗ 15.11): SSH connect=5s, DB connect=3s, SSH exec=10s.

from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

# FIX BLOCKER: убран get_connection() — используем engine (SQLAlchemy Core)
from database import engine
from dependencies import require_auth
from services.db_client import DBClient, DBError
from services.event_log import write_event
from services.ssh_client import SSHClient, SSHError

router = APIRouter(
    prefix="/clusters/{cluster_id}",
    tags=["diagnostics"],
    dependencies=[Depends(require_auth)],
)


# ── Internal DB helpers ───────────────────────────────────────────────────────

def _assert_cluster_exists(cluster_id: int) -> dict:
    # FIX BLOCKER: get_connection() → engine.connect()
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
                 """),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _get_enabled_arbitrators(cluster_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT id, name, host, ssh_port, ssh_user
                 FROM arbitrators
                 WHERE cluster_id = :cid AND enabled = 1
                 """),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _get_arbitrator_or_404(cluster_id: int, arb_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                 SELECT id, name, host, ssh_port, ssh_user
                 FROM arbitrators
                 WHERE id = :aid AND cluster_id = :cid
                 """),
            {"aid": arb_id, "cid": cluster_id},
        ).mappings().fetchone()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Arbitrator {arb_id} not found in cluster {cluster_id}",
        )
    return dict(row)


def _get_node_for_cluster(node_id: int, cluster_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                 SELECT id, name, host, port, ssh_port, ssh_user, db_user, db_password
                 FROM nodes
                 WHERE id = :nid AND cluster_id = :cid AND enabled = 1
                 """),
            {"nid": node_id, "cid": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


# ── SSH / DB probe helpers — called inside asyncio.to_thread() ────────────────

def _probe_node_ssh(node: dict) -> dict:
    """SSH connectivity + latency for one node."""
    # FIX MAJOR: node["ssh_port"] может быть None
    # FIX MAJOR: used as context manager (with) для гарантии close()
    t0 = time.monotonic()
    try:
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as client:
            # FIX BLOCKER: client.exec() → client.execute()
            client.execute("echo ok")
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {"ssh_ok": True, "ssh_latency_ms": latency_ms, "ssh_error": None}
    except SSHError as exc:
        return {"ssh_ok": False, "ssh_latency_ms": None, "ssh_error": str(exc)}
    except Exception as exc:
        return {"ssh_ok": False, "ssh_latency_ms": None, "ssh_error": str(exc)}


def _probe_node_db(node: dict) -> dict:
    """DB connectivity + latency for one node."""
    if not node.get("db_user") or not node.get("db_password"):
        return {"db_ok": None, "db_latency_ms": None, "db_error": "No credentials"}
    t0 = time.monotonic()
    try:
        # FIX MAJOR: используем context manager
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            client.query("SELECT 1")
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {"db_ok": True, "db_latency_ms": latency_ms, "db_error": None}
    except DBError as exc:
        return {"db_ok": False, "db_latency_ms": None, "db_error": str(exc)}
    except Exception as exc:
        return {"db_ok": False, "db_latency_ms": None, "db_error": str(exc)}


def _probe_arbitrator(arb: dict) -> dict:
    """SSH + garbd process check for one arbitrator."""
    t0 = time.monotonic()
    try:
        # FIX MAJOR: context manager + FIX BLOCKER: execute() вместо exec()
        with SSHClient(
                host=arb["host"],
                port=int(arb.get("ssh_port") or 22),
                username=arb.get("ssh_user") or "root",
        ) as client:
            stdout, _ = client.execute(
                "pgrep -x garbd > /dev/null 2>&1 && echo running || echo stopped"
            )
        latency_ms = round((time.monotonic() - t0) * 1000)
        garbd_running = stdout.strip() == "running"
        return {
            "ssh_ok":         True,
            "garbd_running":  garbd_running,
            "latency_ssh_ms": latency_ms,
            "error":          None,
        }
    except SSHError as exc:
        return {
            "ssh_ok":         False,
            "garbd_running":  False,
            "latency_ssh_ms": None,
            "error":          str(exc),
        }
    except Exception as exc:
        return {
            "ssh_ok":         False,
            "garbd_running":  False,
            "latency_ssh_ms": None,
            "error":          str(exc),
        }


def _fetch_wsrep_variables(node: dict) -> dict[str, str] | None:
    """SHOW GLOBAL VARIABLES WHERE Variable_name LIKE 'wsrep%' for one node."""
    if not node.get("db_user") or not node.get("db_password"):
        return None
    try:
        # FIX MAJOR: context manager
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            rows = client.query(
                "SHOW GLOBAL VARIABLES WHERE Variable_name LIKE 'wsrep%'"
            )
        return {r["Variable_name"]: r["Value"] for r in rows}
    except Exception:
        return None


def _fetch_all_variables(node: dict) -> list[dict] | None:
    """SHOW GLOBAL VARIABLES for one node."""
    if not node.get("db_user") or not node.get("db_password"):
        return None
    try:
        # FIX MAJOR: context manager
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL VARIABLES")
        return rows
    except Exception:
        return None


def _fetch_resources(node: dict) -> dict:
    """SSH resource probes: CPU load, RAM, disk, uptime. Per ТЗ 15.6."""
    result: dict[str, Any] = {
        "node_id":      node["id"],
        "node_name":    node["name"],
        "host":         node["host"],
        "cpu_load":     None,
        "ram":          None,
        "disk":         None,
        "uptime_since": None,
        "error":        None,
    }
    try:
        # FIX MAJOR: context manager + FIX BLOCKER: execute() вместо exec()
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as client:
            # CPU — /proc/loadavg: "0.52 0.58 0.59 1/432 12345"
            stdout, _ = client.execute("cat /proc/loadavg")
            parts = stdout.strip().split()
            if len(parts) >= 3:
                result["cpu_load"] = {
                    "load1":  float(parts[0]),
                    "load5":  float(parts[1]),
                    "load15": float(parts[2]),
                }

            # RAM — free -b
            stdout, _ = client.execute("free -b")
            for line in stdout.splitlines():
                if line.startswith("Mem:"):
                    cols = line.split()
                    result["ram"] = {
                        "total_bytes":     int(cols[1]),
                        "used_bytes":      int(cols[2]),
                        "free_bytes":      int(cols[3]),
                        "available_bytes": int(cols[6]) if len(cols) > 6 else None,
                    }
                    break

            # Disk — df -B1 /
            stdout, _ = client.execute("df -B1 /")
            lines = [
                l for l in stdout.splitlines()
                if l and not l.startswith("Filesystem")
            ]
            if lines:
                cols = lines[-1].split()
                result["disk"] = {
                    "total_bytes":     int(cols[1]),
                    "used_bytes":      int(cols[2]),
                    "available_bytes": int(cols[3]),
                    "use_percent":     cols[4].rstrip("%"),
                }

            # Uptime since
            stdout, _ = client.execute("uptime -s")
            result["uptime_since"] = stdout.strip() or None

    except SSHError as exc:
        result["error"] = str(exc)
    except Exception as exc:
        result["error"] = str(exc)

    return result


def _fetch_arbitrator_log(arb: dict, lines: int) -> dict:
    """journalctl -u garbd -n N with fallback to tail. Per ТЗ 15.8."""
    try:
        # FIX MAJOR: context manager + FIX BLOCKER: execute() вместо exec()
        with SSHClient(
                host=arb["host"],
                port=int(arb.get("ssh_port") or 22),
                username=arb.get("ssh_user") or "root",
        ) as client:
            stdout, _ = client.execute(
                f"journalctl -u garbd -n {lines} --no-pager 2>/dev/null"
            )
            log_lines = stdout.strip().splitlines() if stdout.strip() else []

            # Fallback: tail от стандартных путей (ТЗ 15.8)
            if not log_lines:
                stdout, _ = client.execute(
                    f"tail -n {lines} /var/log/garbd.log 2>/dev/null || "
                    f"tail -n {lines} /var/log/garbd/garbd.log 2>/dev/null || echo ''"
                )
                log_lines = stdout.strip().splitlines() if stdout.strip() else []

        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           log_lines,
            "error":           None,
        }
    except SSHError as exc:
        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           [],
            "error":           str(exc),
        }
    except Exception as exc:
        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           [],
            "error":           str(exc),
        }


# ── POST /diagnostics/check-all ──────────────────────────────────────────────

@router.post("/diagnostics/check-all")
async def check_all(cluster_id: int) -> dict:
    """ТЗ 15.3: параллельные SSH+DB проверки всех нод и арбитраторов."""
    _assert_cluster_exists(cluster_id)

    nodes        = _get_enabled_nodes(cluster_id)
    arbitrators  = _get_enabled_arbitrators(cluster_id)

    node_ssh_tasks = [asyncio.to_thread(_probe_node_ssh, node) for node in nodes]
    node_db_tasks  = [asyncio.to_thread(_probe_node_db,  node) for node in nodes]
    arb_tasks      = [asyncio.to_thread(_probe_arbitrator, arb) for arb in arbitrators]

    all_results = await asyncio.gather(
        *node_ssh_tasks, *node_db_tasks, *arb_tasks,
        return_exceptions=True,
    )

    n           = len(nodes)
    ssh_results = all_results[:n]
    db_results  = all_results[n: n * 2]
    arb_results = all_results[n * 2:]

    node_checks = []
    for node, ssh_r, db_r in zip(nodes, ssh_results, db_results):
        if isinstance(ssh_r, Exception):
            ssh_r = {"ssh_ok": False, "ssh_latency_ms": None, "ssh_error": str(ssh_r)}
        if isinstance(db_r, Exception):
            db_r  = {"db_ok": False, "db_latency_ms": None, "db_error": str(db_r)}
        node_checks.append({
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "role":      "node",
            **ssh_r,
            **db_r,
        })

    arb_checks = []
    for arb, arb_r in zip(arbitrators, arb_results):
        if isinstance(arb_r, Exception):
            arb_r = {
                "ssh_ok":         False,
                "garbd_running":  False,
                "latency_ssh_ms": None,
                "error":          str(arb_r),
            }
        arb_checks.append({
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "role":            "arbitrator",
            "db_ok":           None,
            "db_latency_ms":   None,
            **arb_r,
        })

    failed_nodes = [r for r in node_checks if not r.get("ssh_ok")]
    # ТЗ 2.6: уровни INFO / WARN / ERROR
    level = "WARN" if failed_nodes else "INFO"
    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        source="diagnostics",
        level=level,
        message=(
            f"check-all: {len(node_checks)} nodes, {len(arb_checks)} arbitrators checked. "
            f"SSH failures: {len(failed_nodes)}"
        ),
    )

    return {"nodes": node_checks, "arbitrators": arb_checks}


# ── GET /diagnostics/config-diff ─────────────────────────────────────────────

@router.get("/diagnostics/config-diff")
async def config_diff(cluster_id: int) -> dict:
    """ТЗ 15.4: SHOW GLOBAL VARIABLES LIKE 'wsrep%', diff по enabled нодам."""
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if not nodes:
        return {"variables": [], "nodes": [], "diff_found": False}

    tasks: list = [asyncio.to_thread(_fetch_wsrep_variables, node) for node in nodes]
    results: list[dict[str, str] | None] = await asyncio.gather(*tasks, return_exceptions=False)

    all_var_names: set[str] = set()
    for r in results:
        if r:
            all_var_names.update(r.keys())

    table = []
    for var_name in sorted(all_var_names):
        values = [
            {
                "node_id":    node["id"],
                "node_name":  node["name"],
                "value":      node_vars.get(var_name) if node_vars else None,
                "fetch_error": node_vars is None,
            }
            for node, node_vars in zip(nodes, results)
        ]
        distinct = {v["value"] for v in values if not v["fetch_error"]}
        table.append({
            "variable": var_name,
            "values":   values,
            "has_diff": len(distinct) > 1,
        })

    node_summary = [
        {
            "node_id":   n["id"],
            "node_name": n["name"],
            "host":      n["host"],
            "fetch_ok":  results[i] is not None,
        }
        for i, n in enumerate(nodes)
    ]

    return {
        "variables":  table,
        "nodes":      node_summary,
        "diff_found": any(row["has_diff"] for row in table),
    }


# ── GET /diagnostics/variables ────────────────────────────────────────────────

@router.get("/diagnostics/variables")
async def variables(
        cluster_id: int,
        node_id: int      = Query(...,    description="Target node id"),
        search: str | None = Query(None,  description="Filter by variable name substring"),
        wsrep_only: bool   = Query(False, description="Return only wsrep_* variables"),
) -> dict:
    """ТЗ 15.5: SHOW GLOBAL VARIABLES с фильтрацией."""
    _assert_cluster_exists(cluster_id)

    # FIX BLOCKER: get_connection() → engine helper
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in cluster {cluster_id}",
        )

    rows: list[dict] | None = await asyncio.to_thread(_fetch_all_variables, node)
    if rows is None:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to node {node['name']} ({node['host']}:{node['port']})",
        )

    if wsrep_only:
        rows = [r for r in rows if r["Variable_name"].startswith("wsrep")]
    if search:
        search_lower = search.lower()
        rows = [r for r in rows if search_lower in r["Variable_name"].lower()]

    return {
        "node_id":   node["id"],
        "node_name": node["name"],
        "host":      node["host"],
        "total":     len(rows),
        "variables": [{"name": r["Variable_name"], "value": r["Value"]} for r in rows],
    }


# ── POST /diagnostics/resources ──────────────────────────────────────────────

@router.post("/diagnostics/resources")
async def resources(cluster_id: int) -> dict:
    """ТЗ 15.6: SSH-ресурсы (CPU, RAM, Disk, Uptime) по всем enabled нодам."""
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if not nodes:
        return {"nodes": []}

    tasks   = [asyncio.to_thread(_fetch_resources, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    node_resources = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            node_resources.append({
                "node_id":      node["id"],
                "node_name":    node["name"],
                "host":         node["host"],
                "cpu_load":     None,
                "ram":          None,
                "disk":         None,
                "uptime_since": None,
                "error":        str(result),
            })
        else:
            node_resources.append(result)

    errors = [r for r in node_resources if r.get("error")]
    if errors:
        await asyncio.to_thread(
            write_event,
            cluster_id=cluster_id,
            source="diagnostics",
            level="WARN",
            message=(
                    f"resources check: SSH errors on {len(errors)} node(s): "
                    + ", ".join(r["node_name"] for r in errors)
            ),
        )

    return {"nodes": node_resources}


# ── GET /arbitrators/{arb_id}/test-connection ─────────────────────────────────

@router.get("/arbitrators/{arb_id}/test-connection")
async def arbitrator_test_connection(cluster_id: int, arb_id: int) -> dict:
    """ТЗ 15.3, 15.9: SSH + garbd process check для одного арбитратора."""
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_or_404(cluster_id, arb_id)

    result = await asyncio.to_thread(_probe_arbitrator, arb)

    level = "INFO" if result["ssh_ok"] else "WARN"
    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        arbitrator_id=arb_id,
        source="diagnostics",
        level=level,
        message=(
            f"test-connection arbitrator {arb['name']}: "
            f"ssh={'ok' if result['ssh_ok'] else 'fail'}, "
            f"garbd={'running' if result['garbd_running'] else 'stopped'}, "
            f"latency={result['latency_ssh_ms']}ms"
        ),
    )

    return {
        "arbitrator_id":   arb["id"],
        "arbitrator_name": arb["name"],
        "host":            arb["host"],
        **result,
    }


# ── GET /arbitrators/{arb_id}/log ─────────────────────────────────────────────

@router.get("/arbitrators/{arb_id}/log")
async def arbitrator_log(
        cluster_id: int,
        arb_id: int,
        lines: int = Query(default=50, ge=1, le=500, description="Number of log lines"),
) -> dict:
    """ТЗ 15.8: journalctl -u garbd -n N / fallback tail."""
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_or_404(cluster_id, arb_id)

    result = await asyncio.to_thread(_fetch_arbitrator_log, arb, lines)

    if result["error"]:
        await asyncio.to_thread(
            write_event,
            cluster_id=cluster_id,
            arbitrator_id=arb_id,
            source="diagnostics",
            level="WARN",
            message=f"arb log fetch failed for {arb['name']}: {result['error']}",
        )

    return result