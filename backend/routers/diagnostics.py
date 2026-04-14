# backend/routers/diagnostics.py
#
# Phase 4 — Diagnostics backend
# Endpoints (ТЗ раздел 15):
#   POST /api/clusters/{cluster_id}/diagnostics/check-all
#   GET  /api/clusters/{cluster_id}/diagnostics/config-diff
#   GET  /api/clusters/{cluster_id}/diagnostics/variables
#   GET  /api/clusters/{cluster_id}/diagnostics/variables/all
#   POST /api/clusters/{cluster_id}/diagnostics/resources
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/test-connection
#   GET  /api/clusters/{cluster_id}/arbitrators/{arb_id}/log
#
# Extra endpoints (frontend already implemented, backend was missing):
#   GET  /api/clusters/{cluster_id}/diagnostics/galera-status
#   GET  /api/clusters/{cluster_id}/diagnostics/process-list?node_id=N
#   GET  /api/clusters/{cluster_id}/diagnostics/slow-queries?node_id=N
#   GET  /api/clusters/{cluster_id}/nodes/{node_id}/error-log?lines=N
#
# Improvement #5:
#   POST /api/clusters/{cluster_id}/nodes/{node_id}/kill-process/{process_id}
#
# innodb-status lives in routers/nodes.py — not duplicated here.
# Timeouts (ТЗ 15.11): SSH connect=5s, DB connect=3s, SSH exec=10s.

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

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


# ── Internal DB helpers ─────────────────────────────────────────────────────────────

def _assert_cluster_exists(cluster_id: int) -> dict:
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


# ── SSH / DB probe helpers ───────────────────────────────────────────────────────────

def _probe_node_ssh(node: dict) -> dict:
    t0 = time.monotonic()
    try:
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as client:
            client.execute("echo ok")
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {"ssh_ok": True, "ssh_latency_ms": latency_ms, "ssh_error": None}
    except SSHError as exc:
        return {"ssh_ok": False, "ssh_latency_ms": None, "ssh_error": str(exc)}
    except Exception as exc:
        return {"ssh_ok": False, "ssh_latency_ms": None, "ssh_error": str(exc)}


def _probe_node_db(node: dict) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {"db_ok": None, "db_latency_ms": None, "db_error": "No credentials"}
    t0 = time.monotonic()
    try:
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
    t0 = time.monotonic()
    try:
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
    if not node.get("db_user") or not node.get("db_password"):
        return None
    try:
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
    if not node.get("db_user") or not node.get("db_password"):
        return None
    try:
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
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as client:
            stdout, _ = client.execute("cat /proc/loadavg")
            parts = stdout.strip().split()
            if len(parts) >= 3:
                result["cpu_load"] = {
                    "load1":  float(parts[0]),
                    "load5":  float(parts[1]),
                    "load15": float(parts[2]),
                }

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

            stdout, _ = client.execute("uptime -s")
            result["uptime_since"] = stdout.strip() or None

    except SSHError as exc:
        result["error"] = str(exc)
    except Exception as exc:
        result["error"] = str(exc)

    return result


# ── Journalctl noise filter ──────────────────────────────────────────────────────────
_JOURNALCTL_NOISE_PREFIXES = (
    "-- No entries --",
    "-- Logs begin",
    "-- Journal begins",
    "-- Boot ",
    "-- Reboot ",
)


def _filter_journalctl_noise(raw: str) -> list[str]:
    """Strip empty lines and journalctl meta-lines, return real log lines."""
    result = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in _JOURNALCTL_NOISE_PREFIXES):
            continue
        result.append(line)
    return result


# ── _fetch_arbitrator_log ────────────────────────────────────────────────────────────

_GARBD_SYSTEMD_UNITS = ("garbd", "garb", "garbd@")

_GARBD_LOG_FILES = (
    "/var/log/garbd.log",
    "/var/log/garbd/garbd.log",
    "/var/log/garb/garbd.log",
)


def _fetch_arbitrator_log(arb: dict, lines: int) -> dict:
    try:
        with SSHClient(
                host=arb["host"],
                port=int(arb.get("ssh_port") or 22),
                username=arb.get("ssh_user") or "root",
        ) as client:
            log_lines: list[str] = []
            source_used: str = "none"

            for unit in _GARBD_SYSTEMD_UNITS:
                stdout, _ = client.execute(
                    f"journalctl -u {unit} -n {lines} --no-pager 2>/dev/null"
                )
                candidate = _filter_journalctl_noise(stdout)
                if candidate:
                    log_lines = candidate
                    source_used = f"journalctl -u {unit}"
                    break

            if not log_lines:
                for path in _GARBD_LOG_FILES:
                    stdout, _ = client.execute(
                        f"test -f {path} && tail -n {lines} {path} 2>/dev/null || true"
                    )
                    candidate = [l for l in stdout.strip().splitlines() if l.strip()]
                    if candidate:
                        log_lines = candidate
                        source_used = f"tail {path}"
                        break

            if not log_lines:
                stdout, _ = client.execute(
                    f"journalctl -n {lines} --no-pager 2>/dev/null | grep -i garb || true"
                )
                candidate = [l for l in stdout.strip().splitlines() if l.strip()]
                if candidate:
                    log_lines = candidate
                    source_used = "journalctl grep garb"

        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           log_lines,
            "source":          source_used,
            "fetched_at":      datetime.now(timezone.utc).isoformat(),
            "error":           None,
        }
    except SSHError as exc:
        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           [],
            "source":          "none",
            "fetched_at":      datetime.now(timezone.utc).isoformat(),
            "error":           str(exc),
        }
    except Exception as exc:
        return {
            "arbitrator_id":   arb["id"],
            "arbitrator_name": arb["name"],
            "host":            arb["host"],
            "lines":           [],
            "source":          "none",
            "fetched_at":      datetime.now(timezone.utc).isoformat(),
            "error":           str(exc),
        }


# ── Error log helpers ────────────────────────────────────────────────────────────────

_ERROR_LOG_CANDIDATES = [
    ("journalctl", "journalctl -u mariadb -n {lines} --no-pager 2>/dev/null"),
    ("file",        "tail -n {lines} /var/log/mysql/error.log 2>/dev/null"),
    ("file",        "tail -n {lines} /var/log/mariadb/mariadb.log 2>/dev/null"),
    ("file",        "tail -n {lines} /var/log/mysqld.log 2>/dev/null"),
    ("file",        "find /var/lib/mysql -maxdepth 1 -name '*.err' 2>/dev/null | head -1 | xargs -r tail -n {lines}"),
]


def _fetch_error_log(node: dict, lines: int) -> dict:
    try:
        with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
        ) as client:
            log_lines: list[str] = []
            source_used: str = "none"

            for kind, cmd_tpl in _ERROR_LOG_CANDIDATES:
                cmd = cmd_tpl.format(lines=lines)
                stdout, _ = client.execute(cmd)

                if kind == "journalctl":
                    candidate = _filter_journalctl_noise(stdout)
                else:
                    candidate = [l for l in stdout.splitlines() if l.strip()]

                if candidate:
                    log_lines = candidate
                    source_used = cmd_tpl.split()[0] if kind == "journalctl" else cmd_tpl
                    break

        return {
            "node_id":     node["id"],
            "node_name":   node["name"],
            "lines":       log_lines,
            "source":      source_used,
            "fetched_at":  datetime.now(timezone.utc).isoformat(),
            "error":       None,
        }
    except SSHError as exc:
        return {
            "node_id":    node["id"],
            "node_name":  node["name"],
            "lines":      [],
            "source":     "none",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error":      str(exc),
        }
    except Exception as exc:
        return {
            "node_id":    node["id"],
            "node_name":  node["name"],
            "lines":      [],
            "source":     "none",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error":      str(exc),
        }


# ── POST /diagnostics/check-all ──────────────────────────────────────────────────────

@router.post("/diagnostics/check-all")
async def check_all(cluster_id: int) -> dict:
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


# ── GET /diagnostics/config-diff ─────────────────────────────────────────────────────

@router.get("/diagnostics/config-diff")
async def config_diff(cluster_id: int) -> dict:
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


# ── GET /diagnostics/variables ───────────────────────────────────────────────────────

@router.get("/diagnostics/variables")
async def variables(
        cluster_id: int,
        node_id: int      = Query(...,    description="Target node id"),
        search: str | None = Query(None,  description="Filter by variable name substring"),
        wsrep_only: bool   = Query(False, description="Return only wsrep_* variables"),
) -> dict:
    _assert_cluster_exists(cluster_id)

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


# ── GET /diagnostics/variables/all ───────────────────────────────────────────────────

@router.get("/diagnostics/variables/all")
async def variables_all(
        cluster_id: int,
        wsrep_only: bool = Query(False, description="Return only wsrep_* variables"),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if not nodes:
        return []

    tasks = [asyncio.to_thread(_fetch_all_variables, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception) or result is None:
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "host":      node["host"],
                "total":     0,
                "variables": [],
                "error":     str(result) if isinstance(result, Exception) else "No credentials or connection failed",
            })
        else:
            rows = result
            if wsrep_only:
                rows = [r for r in rows if r["Variable_name"].startswith("wsrep")]
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "host":      node["host"],
                "total":     len(rows),
                "variables": [{"name": r["Variable_name"], "value": r["Value"]} for r in rows],
                "error":     None,
            })

    return output


# ── POST /diagnostics/resources ──────────────────────────────────────────────────────

@router.post("/diagnostics/resources")
async def resources(cluster_id: int) -> dict:
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


# ── GET /diagnostics/galera-status ───────────────────────────────────────────────────

def _fetch_galera_status(node: dict) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "status":    {},
            "error":     "No DB credentials configured",
        }
    try:
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL STATUS LIKE 'wsrep%'")
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "status":    {r["Variable_name"]: r["Value"] for r in rows},
            "error":     None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "status":    {},
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "status":    {},
            "error":     str(exc),
        }


@router.get("/diagnostics/galera-status")
async def galera_status(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if not nodes:
        return []

    tasks   = [asyncio.to_thread(_fetch_galera_status, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "host":      node["host"],
                "status":    {},
                "error":     str(result),
            })
        else:
            output.append(result)

    return output


# ── GET /diagnostics/process-list ────────────────────────────────────────────────────

def _fetch_process_list(node: dict) -> list[dict]:
    if not node.get("db_user") or not node.get("db_password"):
        raise DBError("No DB credentials configured")
    with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
    ) as client:
        rows = client.query("SHOW FULL PROCESSLIST")
    return [
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
        for r in rows
    ]


@router.get("/diagnostics/process-list")
async def process_list(
        cluster_id: int,
        node_id: int | None = Query(None, description="Filter by node id; omit for all nodes"),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if node_id is not None:
        nodes = [n for n in nodes if n["id"] == node_id]
        if not nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
            )

    if not nodes:
        return []

    tasks   = [asyncio.to_thread(_fetch_process_list, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "error":     str(result),
                "processes": [],
            })
        else:
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "error":     None,
                "processes": result,
            })

    return output


# ── POST /nodes/{node_id}/kill-process/{process_id} ──────────────────────────────────
# Improvement #5: Kill a specific process by ID on a given node.

@router.post("/nodes/{node_id}/kill-process/{process_id}")
async def kill_process(
    cluster_id: int,
    node_id: int,
    process_id: int,
    _user: dict = Depends(require_auth),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if node is None:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
        )

    if not node.get("db_user") or not node.get("db_password"):
        raise HTTPException(status_code=422, detail="No DB credentials configured for this node")

    def _do_kill() -> None:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            # KILL accepts only a literal integer — no parameter binding possible.
            # process_id is validated as int by FastAPI path param type, safe to interpolate.
            client.execute(f"KILL {process_id}")

    try:
        await asyncio.to_thread(_do_kill)
    except DBError as exc:
        msg = str(exc)
        # 1094: Unknown thread id (process already gone — treat as success)
        if "1094" in msg:
            pass
        elif any(code in msg for code in ("1227", "1044", "1142", "Access denied")):
            raise HTTPException(status_code=403, detail=f"Insufficient privileges: {msg}")
        else:
            raise HTTPException(status_code=500, detail=msg)

    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        node_id=node_id,
        source="diagnostics",
        level="WARN",
        message=f"kill process {process_id} on node {node['name']} ({node['host']})",
    )

    return {"ok": True, "process_id": process_id, "node_name": node["name"]}


# ── GET /diagnostics/slow-queries ────────────────────────────────────────────────────

def _fetch_slow_queries(node: dict) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":          node["id"],
            "node_name":        node["name"],
            "slow_log_enabled": None,
            "rows":             [],
            "error":            "No DB credentials configured",
        }
    try:
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            var_rows = client.query(
                "SHOW GLOBAL VARIABLES LIKE 'slow_query_log'"
            )
            slow_log_on = (
                var_rows[0]["Value"].upper() == "ON"
                if var_rows else False
            )

            if not slow_log_on:
                return {
                    "node_id":          node["id"],
                    "node_name":        node["name"],
                    "slow_log_enabled": False,
                    "rows":             [],
                    "error":            None,
                }

            rows = client.query(
                """
                SELECT
                    DATE_FORMAT(start_time, '%Y-%m-%dT%H:%i:%S') AS start_time,
                    user_host,
                    TIME_FORMAT(query_time,  '%H:%i:%s') AS query_time,
                    TIME_FORMAT(lock_time,   '%H:%i:%s') AS lock_time,
                    rows_sent,
                    rows_examined,
                    db,
                    CONVERT(sql_text USING utf8mb4) AS sql_text
                FROM mysql.slow_log
                ORDER BY start_time DESC
                LIMIT 200
                """
            )
        return {
            "node_id":          node["id"],
            "node_name":        node["name"],
            "slow_log_enabled": True,
            "rows":             rows,
            "error":            None,
        }
    except DBError as exc:
        return {
            "node_id":          node["id"],
            "node_name":        node["name"],
            "slow_log_enabled": None,
            "rows":             [],
            "error":            str(exc),
        }
    except Exception as exc:
        return {
            "node_id":          node["id"],
            "node_name":        node["name"],
            "slow_log_enabled": None,
            "rows":             [],
            "error":            str(exc),
        }


@router.get("/diagnostics/slow-queries")
async def slow_queries(
        cluster_id: int,
        node_id: int | None = Query(None, description="Filter by node id; omit for all nodes"),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if node_id is not None:
        nodes = [n for n in nodes if n["id"] == node_id]
        if not nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
            )

    if not nodes:
        return []

    tasks   = [asyncio.to_thread(_fetch_slow_queries, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":          node["id"],
                "node_name":        node["name"],
                "slow_log_enabled": None,
                "rows":             [],
                "error":            str(result),
            })
        else:
            output.append(result)

    return output


# ── GET /nodes/{node_id}/error-log ───────────────────────────────────────────────────

@router.get("/nodes/{node_id}/error-log")
async def error_log(
        cluster_id: int,
        node_id: int,
        lines: int = Query(default=200, ge=10, le=1000, description="Number of log lines"),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
        )

    result = await asyncio.to_thread(_fetch_error_log, node, lines)

    if result["error"]:
        await asyncio.to_thread(
            write_event,
            cluster_id=cluster_id,
            node_id=node_id,
            source="diagnostics",
            level="WARN",
            message=f"error-log fetch failed for {node['name']}: {result['error']}",
        )

    return result


# ── GET /arbitrators/{arb_id}/test-connection ────────────────────────────────────────

@router.get("/arbitrators/{arb_id}/test-connection")
async def arbitrator_test_connection(cluster_id: int, arb_id: int) -> dict:
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


# ── GET /arbitrators/{arb_id}/log ────────────────────────────────────────────────────

@router.get("/arbitrators/{arb_id}/log")
async def arbitrator_log(
        cluster_id: int,
        arb_id: int,
        lines: int = Query(default=50, ge=1, le=500, description="Number of log lines"),
) -> dict:
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


# ── POST /nodes/{node_id}/set-slow-query-log ─────────────────────────────────────────

class _SetSlowQueryLogBody(BaseModel):
    enabled: bool


@router.post("/nodes/{node_id}/set-slow-query-log")
async def set_slow_query_log(
    cluster_id: int,
    node_id: int,
    body: _SetSlowQueryLogBody,
    _user: dict = Depends(require_auth),
) -> dict:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    node  = next((n for n in nodes if n["id"] == node_id), None)
    if node is None:
        raise HTTPException(404, f"Node {node_id} not found or disabled in cluster {cluster_id}")

    if not node.get("db_user") or not node.get("db_password"):
        raise HTTPException(422, "No DB credentials configured for this node")

    value = "ON" if body.enabled else "OFF"

    def _do_set() -> None:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            client.execute(f"SET GLOBAL slow_query_log = {value}")

    try:
        await asyncio.to_thread(_do_set)
    except DBError as exc:
        msg = str(exc)
        if any(code in msg for code in ("1227", "1044", "1142", "Access denied")):
            raise HTTPException(403, f"Insufficient privileges: {msg}")
        raise HTTPException(500, msg)

    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        node_id=node_id,
        source="diagnostics",
        level="INFO",
        message=f"slow_query_log set to {value} on node {node['name']}",
    )
    return {"ok": True, "slow_query_log": value}
