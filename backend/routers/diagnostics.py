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
# Improvement #6:
#   POST /api/clusters/{cluster_id}/nodes/{node_id}/kill-processes
#        body: { filter: "sleep"|"user", min_time?: int, user?: str }
#        → { killed: [int], skipped: int, errors: [str], node_name: str }
#
# Improvement #13:
#   POST /api/clusters/{cluster_id}/diagnostics/disk-usage
#        body: { node_id: int }
#        → { node_id, node_name, top_tables, binary_logs, binary_logs_total_mb, ibdata1_mb, error }
#
# Improvement #15:
#   GET  /api/clusters/{cluster_id}/diagnostics/active-transactions?node_id=N&min_age_sec=N
#        → [{ node_id, node_name, transactions: [...], error }]
#
# innodb-status lives in routers/nodes.py — not duplicated here.
# Timeouts (ТЗ 15.11): SSH connect=5s, DB connect=3s, SSH exec=10s.

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
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
            client.execute(f"KILL {process_id}")

    try:
        await asyncio.to_thread(_do_kill)
    except DBError as exc:
        msg = str(exc)
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


# ── POST /nodes/{node_id}/kill-processes ─────────────────────────────────────────────
# Improvement #6: Kill ALL processes matching a filter on a given node.

_SYSTEM_USERS = frozenset({"system user", "event_scheduler"})
_SYSTEM_COMMANDS = frozenset({"Daemon", "Binlog Dump", "Binlog Dump GTID"})


class _KillFilter(str, Enum):
    sleep = "sleep"
    user  = "user"


class _KillProcessesBody(BaseModel):
    filter: _KillFilter
    min_time: int = 5
    user: str | None = None

    @field_validator("user")
    @classmethod
    def user_required_for_user_filter(cls, v: str | None, info: Any) -> str | None:
        if info.data.get("filter") == _KillFilter.user and not v:
            raise ValueError("'user' field is required when filter='user'")
        return v


def _do_kill_processes(node: dict, body: _KillProcessesBody) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        raise DBError("No DB credentials configured")

    with DBClient(
        host=node["host"],
        port=int(node.get("port") or 3306),
        user=node["db_user"],
        encrypted_password=node["db_password"],
    ) as client:
        rows = client.query("SHOW FULL PROCESSLIST")

        own_id_rows = client.query("SELECT CONNECTION_ID() AS cid")
        own_id = own_id_rows[0]["cid"] if own_id_rows else None

        candidates: list[int] = []
        skipped = 0

        for r in rows:
            pid     = r.get("Id")
            user    = r.get("User") or ""
            command = r.get("Command") or ""
            time_s  = int(r.get("Time") or 0)

            if pid == own_id:
                skipped += 1
                continue
            if user.lower() in _SYSTEM_USERS or command in _SYSTEM_COMMANDS:
                skipped += 1
                continue

            if body.filter == _KillFilter.sleep:
                if command == "Sleep" and time_s >= body.min_time:
                    candidates.append(pid)
                else:
                    skipped += 1
            else:
                if user == body.user:
                    candidates.append(pid)
                else:
                    skipped += 1

        killed: list[int] = []
        errors: list[str] = []

        for pid in candidates:
            try:
                client.execute(f"KILL {pid}")
                killed.append(pid)
            except DBError as exc:
                msg = str(exc)
                if "1094" in msg:
                    killed.append(pid)
                else:
                    errors.append(f"pid {pid}: {msg}")

    return {"killed": killed, "skipped": skipped, "errors": errors}


@router.post("/nodes/{node_id}/kill-processes")
async def kill_processes(
    cluster_id: int,
    node_id: int,
    body: _KillProcessesBody,
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

    try:
        result = await asyncio.to_thread(_do_kill_processes, node, body)
    except DBError as exc:
        msg = str(exc)
        if any(code in msg for code in ("1227", "1044", "1142", "Access denied")):
            raise HTTPException(status_code=403, detail=f"Insufficient privileges: {msg}")
        raise HTTPException(status_code=500, detail=msg)

    filter_desc = (
        f"sleep >= {body.min_time}s"
        if body.filter == _KillFilter.sleep
        else f"user={body.user}"
    )
    await asyncio.to_thread(
        write_event,
        cluster_id=cluster_id,
        node_id=node_id,
        source="diagnostics",
        level="WARN",
        message=(
            f"kill-processes ({filter_desc}) on {node['name']}: "
            f"killed={len(result['killed'])}, skipped={result['skipped']}, "
            f"errors={len(result['errors'])}"
        ),
    )

    return {
        "killed":    result["killed"],
        "skipped":   result["skipped"],
        "errors":    result["errors"],
        "node_name": node["name"],
    }


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

            # NOTE: DATE_FORMAT / TIME_FORMAT use %% to avoid Python format() confusion
            # when the query is passed to PyMySQL which also uses % for param substitution.
            rows = client.query(
                """
                SELECT
                    DATE_FORMAT(start_time, '%%Y-%%m-%%dT%%H:%%i:%%S') AS start_time,
                    user_host,
                    TIME_FORMAT(query_time,  '%%H:%%i:%%s') AS query_time,
                    TIME_FORMAT(lock_time,   '%%H:%%i:%%s') AS lock_time,
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


# ── POST /diagnostics/disk-usage ─────────────────────────────────────────────────────
# Improvement #13: per-node disk details — top tables, binary logs, ibdata1

class _DiskUsageBody(BaseModel):
    node_id: int


def _fetch_disk_usage(node: dict) -> dict:
    result: dict[str, Any] = {
        "node_id":              node["id"],
        "node_name":            node["name"],
        "top_tables":           [],
        "binary_logs":          [],
        "binary_logs_total_mb": None,
        "ibdata1_mb":           None,
        "error":                None,
    }

    if node.get("db_user") and node.get("db_password"):
        try:
            with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
            ) as client:
                rows = client.query("""
                    SELECT
                        table_schema  AS `schema`,
                        table_name    AS `table`,
                        ROUND(data_length  / 1048576, 2) AS data_mb,
                        ROUND(index_length / 1048576, 2) AS index_mb,
                        ROUND((data_length + index_length) / 1048576, 2) AS total_mb
                    FROM information_schema.TABLES
                    WHERE table_schema NOT IN
                          ('information_schema','performance_schema','mysql','sys')
                    ORDER BY (data_length + index_length) DESC
                    LIMIT 10
                """)
                result["top_tables"] = rows

                try:
                    blrows = client.query("SHOW BINARY LOGS")
                    logs = [
                        {"log_name": r["Log_name"], "file_size": int(r["File_size"])}
                        for r in blrows
                    ]
                    result["binary_logs"] = logs
                    result["binary_logs_total_mb"] = round(
                        sum(r["file_size"] for r in logs) / 1_048_576, 2
                    )
                except Exception:
                    pass
        except DBError as exc:
            result["error"] = str(exc)
        except Exception as exc:
            result["error"] = str(exc)

    try:
        with SSHClient(
            host=node["host"],
            port=int(node.get("ssh_port") or 22),
            username=node.get("ssh_user") or "root",
        ) as client:
            stdout, _ = client.execute(
                "test -f /var/lib/mysql/ibdata1 "
                "&& du -sb /var/lib/mysql/ibdata1 2>/dev/null | awk '{print $1}' "
                "|| echo ''"
            )
            val = stdout.strip()
            if val:
                result["ibdata1_mb"] = round(int(val) / 1_048_576, 2)
    except Exception:
        pass

    return result


@router.post("/diagnostics/disk-usage")
async def disk_usage(
    cluster_id: int,
    body: _DiskUsageBody,
    _user: dict = Depends(require_auth),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(body.node_id, cluster_id)
    if node is None:
        raise HTTPException(
            status_code=404,
            detail=f"Node {body.node_id} not found or disabled in cluster {cluster_id}",
        )

    result = await asyncio.to_thread(_fetch_disk_usage, node)
    return result


# ── GET /diagnostics/active-transactions ─────────────────────────────────────────────
# Improvement #15: active transactions from information_schema.INNODB_TRX
# older than min_age_sec seconds.
#
# FIX: DATE_FORMAT uses %% to prevent Python / PyMySQL from interpreting
#      %Y, %H, %i, %S as Python format characters when params tuple is passed.

def _fetch_active_transactions(node: dict, min_age_sec: int) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":      node["id"],
            "node_name":    node["name"],
            "transactions": [],
            "error":        "No DB credentials configured",
        }
    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query(
                """
                SELECT
                    t.trx_id,
                    DATE_FORMAT(t.trx_started, '%%Y-%%m-%%dT%%H:%%i:%%S') AS trx_started,
                    TIMESTAMPDIFF(SECOND, t.trx_started, NOW())            AS trx_age_sec,
                    t.trx_state,
                    t.trx_mysql_thread_id,
                    t.trx_query,
                    t.trx_tables_locked,
                    t.trx_rows_locked,
                    t.trx_rows_modified,
                    p.user,
                    p.host
                FROM information_schema.INNODB_TRX t
                LEFT JOIN information_schema.PROCESSLIST p
                       ON p.ID = t.trx_mysql_thread_id
                WHERE TIMESTAMPDIFF(SECOND, t.trx_started, NOW()) >= %s
                ORDER BY trx_age_sec DESC
                """,
                (min_age_sec,),
            )
        return {
            "node_id":      node["id"],
            "node_name":    node["name"],
            "transactions": [
                {
                    "trx_id":              r.get("trx_id"),
                    "trx_started":         r.get("trx_started"),
                    "trx_age_sec":         r.get("trx_age_sec"),
                    "trx_state":           r.get("trx_state"),
                    "trx_mysql_thread_id": r.get("trx_mysql_thread_id"),
                    "trx_query":           r.get("trx_query"),
                    "trx_tables_locked":   r.get("trx_tables_locked"),
                    "trx_rows_locked":     r.get("trx_rows_locked"),
                    "trx_rows_modified":   r.get("trx_rows_modified"),
                    "user":                r.get("user"),
                    "host":                r.get("host"),
                }
                for r in rows
            ],
            "error": None,
        }
    except DBError as exc:
        return {
            "node_id":      node["id"],
            "node_name":    node["name"],
            "transactions": [],
            "error":        str(exc),
        }
    except Exception as exc:
        return {
            "node_id":      node["id"],
            "node_name":    node["name"],
            "transactions": [],
            "error":        f"Unexpected error querying {node['host']}:{node.get('port', 3306)}: {exc}",
        }


@router.get("/diagnostics/active-transactions")
async def active_transactions(
    cluster_id: int,
    node_id: int | None = Query(None, description="Filter by node id; omit for all nodes"),
    min_age_sec: int    = Query(default=0, ge=0, description="Minimum transaction age in seconds"),
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

    tasks   = [asyncio.to_thread(_fetch_active_transactions, node, min_age_sec) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":      node["id"],
                "node_name":    node["name"],
                "transactions": [],
                "error":        str(result),
            })
        else:
            output.append(result)

    return output

# ── GET /diagnostics/config-health ───────────────────────────────────────────────────
# Improvement #17: Check key MariaDB config params against best-practices rules.

import re as _re


def _fetch_config_health(node: dict) -> dict:
    result: dict[str, Any] = {
        "node_id":   node["id"],
        "node_name": node["name"],
        "host":      node["host"],
        "checks":    [],
        "error":     None,
    }

    # ── SSH: RAM + CPU ───────────────────────────────────────────────────────────
    ram_bytes: int | None = None
    cpu_cores: int | None = None
    try:
        with SSHClient(
            host=node["host"],
            port=int(node.get("ssh_port") or 22),
            username=node.get("ssh_user") or "root",
        ) as ssh:
            stdout, _ = ssh.execute("grep MemTotal /proc/meminfo")
            m = _re.search(r"(\d+)", stdout)
            if m:
                ram_bytes = int(m.group(1)) * 1024  # kB → bytes

            stdout, _ = ssh.execute("nproc")
            cpu_cores = int(stdout.strip()) if stdout.strip().isdigit() else None
    except Exception as exc:
        result["error"] = f"SSH error: {exc}"
        return result

    # ── DB: SHOW GLOBAL VARIABLES ────────────────────────────────────────────────
    if not node.get("db_user") or not node.get("db_password"):
        result["error"] = "No DB credentials configured"
        return result

    try:
        with DBClient(
            host=node["host"],
            port=int(node.get("port") or 3306),
            user=node["db_user"],
            encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL VARIABLES")
        variables = {r["Variable_name"]: r["Value"] for r in rows}
    except DBError as exc:
        result["error"] = str(exc)
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result

    checks = []

    # ── Rule 1: innodb_buffer_pool_size ─────────────────────────────────────────
    bp_raw = variables.get("innodb_buffer_pool_size")
    if bp_raw is not None:
        bp_bytes = int(bp_raw)
        if ram_bytes:
            ratio = bp_bytes / ram_bytes
            bp_gb  = round(bp_bytes  / 1_073_741_824, 2)
            ram_gb = round(ram_bytes / 1_073_741_824, 2)
            if ratio >= 0.60:
                status = "ok"
                rec = None
            elif ratio >= 0.40:
                status = "warn"
                rec = f"Рекомендуется 60–70% от RAM. Текущее: {round(ratio*100)}% ({bp_gb} GB / {ram_gb} GB). Рекомендовано: ~{round(ram_gb*0.65, 1)} GB"
            else:
                status = "error"
                rec = f"Критично низкое значение: {round(ratio*100)}% от RAM ({bp_gb} GB / {ram_gb} GB). Установите ~{round(ram_gb*0.65, 1)} GB"
            checks.append({
                "param":           "innodb_buffer_pool_size",
                "current_value":   bp_raw,
                "current_human":   f"{bp_gb} GB",
                "status":          status,
                "recommendation":  rec,
                "context":         f"RAM: {ram_gb} GB, ratio: {round(ratio*100)}%",
            })
        else:
            checks.append({
                "param":          "innodb_buffer_pool_size",
                "current_value":  bp_raw,
                "current_human":  f"{round(int(bp_raw)/1_073_741_824, 2)} GB",
                "status":         "info",
                "recommendation": "Не удалось получить RAM для сравнения",
                "context":        None,
            })

    # ── Rule 2: max_connections ─────────────────────────────────────────────────
    mc_raw = variables.get("max_connections")
    if mc_raw is not None:
        mc = int(mc_raw)
        if mc <= 500:
            status = "ok"; rec = None
        elif mc <= 1000:
            status = "warn"; rec = f"max_connections={mc}: при пиковой нагрузке каждое соединение потребляет память. Убедитесь, что RAM достаточно."
        else:
            status = "error"; rec = f"max_connections={mc} очень высокое. Риск OOM. Рекомендуется <= 500–1000."
        checks.append({
            "param":          "max_connections",
            "current_value":  mc_raw,
            "current_human":  str(mc),
            "status":         status,
            "recommendation": rec,
            "context":        None,
        })

    # ── Rule 3: wsrep_slave_threads ─────────────────────────────────────────────
    wst_raw = variables.get("wsrep_slave_threads")
    if wst_raw is not None:
        wst = int(wst_raw)
        if cpu_cores:
            if wst >= cpu_cores:
                status = "ok"; rec = None
            elif wst >= max(1, cpu_cores // 2):
                status = "warn"; rec = f"wsrep_slave_threads={wst}, CPU cores={cpu_cores}. Рекомендуется >= {cpu_cores}."
            else:
                status = "error"; rec = f"wsrep_slave_threads={wst} значительно ниже CPU cores={cpu_cores}. Replication lag вероятен."
            ctx = f"CPU cores: {cpu_cores}"
        else:
            status = "info"; rec = "Не удалось получить CPU cores для сравнения"; ctx = None
        checks.append({
            "param":          "wsrep_slave_threads",
            "current_value":  wst_raw,
            "current_human":  str(wst),
            "status":         status,
            "recommendation": rec,
            "context":        ctx,
        })

    # ── Rule 4: innodb_flush_log_at_trx_commit ───────────────────────────────────
    fl_raw = variables.get("innodb_flush_log_at_trx_commit")
    if fl_raw is not None:
        if fl_raw == "1":
            status = "ok"; rec = None
        else:
            status = "warn"
            rec = f"innodb_flush_log_at_trx_commit={fl_raw}. Значение != 1 снижает durability (допустимо в dev/staging, не в prod Galera)."
        checks.append({
            "param":          "innodb_flush_log_at_trx_commit",
            "current_value":  fl_raw,
            "current_human":  fl_raw,
            "status":         status,
            "recommendation": rec,
            "context":        "1 = полная durability (flush на каждый commit)",
        })

    # ── Rule 5: wsrep_sync_wait ──────────────────────────────────────────────────
    sw_raw = variables.get("wsrep_sync_wait")
    if sw_raw is not None:
        sw = int(sw_raw)
        checks.append({
            "param":          "wsrep_sync_wait",
            "current_value":  sw_raw,
            "current_human":  str(sw),
            "status":         "info" if sw == 0 else "ok",
            "recommendation": "0 = sync_wait отключён (reads могут быть stale). Включите для causal reads." if sw == 0 else None,
            "context":        "0=disabled, 1=READ, 2=UPDATE/DELETE, 3=INSERT, 4=REPLACE, 7=all",
        })

    result["checks"] = checks
    return result


@router.get("/diagnostics/config-health")
async def config_health(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    if not nodes:
        return []

    tasks   = [asyncio.to_thread(_fetch_config_health, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "host":      node["host"],
                "checks":    [],
                "error":     str(result),
            })
        else:
            output.append(result)

    return output


# ══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENTS BATCH v2
# ══════════════════════════════════════════════════════════════════════════════

# ── #11 Flow Control Monitor ───────────────────────────────────────────────────
@router.get("/diagnostics/flow-control")
async def get_flow_control(cluster_id: int) -> list[dict]:
    """
    #11 Flow Control Monitor — live wsrep_flow_control_paused per node.
    Also returns wsrep_flow_control_sent, wsrep_flow_control_recv.
    Alert threshold: paused > 0.05 (5%).
    """
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    async def fetch_fc(node: dict) -> dict:
        result = {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "wsrep_flow_control_paused": None,
            "wsrep_flow_control_sent":   None,
            "wsrep_flow_control_recv":   None,
            "wsrep_local_recv_queue_avg": None,
            "wsrep_local_send_queue_avg": None,
            "alert":  False,
            "error":  None,
        }
        try:
            db = DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node.get("db_user") or "root",
                encrypted_password=node.get("db_password") or "",
            )
            db.connect()
            try:
                rows = db.query(
                    "SHOW GLOBAL STATUS WHERE Variable_name IN ("
                    "'wsrep_flow_control_paused',"
                    "'wsrep_flow_control_sent',"
                    "'wsrep_flow_control_recv',"
                    "'wsrep_local_recv_queue_avg',"
                    "'wsrep_local_send_queue_avg')"
                )
                sm = {(r.get("Variable_name") or r.get("variable_name") or "").lower():
                      (r.get("Value") or r.get("value") or "0") for r in rows}
                for field_name in ("wsrep_flow_control_paused", "wsrep_local_recv_queue_avg",
                                   "wsrep_local_send_queue_avg"):
                    try:
                        result[field_name] = float(sm.get(field_name, "0") or "0")
                    except ValueError:
                        pass
                for field_name in ("wsrep_flow_control_sent", "wsrep_flow_control_recv"):
                    try:
                        result[field_name] = int(sm.get(field_name, "0") or "0")
                    except ValueError:
                        pass
                fcp = result.get("wsrep_flow_control_paused")
                result["alert"] = fcp is not None and fcp > 0.05
            finally:
                db.close()
        except DBError as exc:
            result["error"] = str(exc)
        return result

    tasks = [fetch_fc(node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({"node_id": nodes[i]["id"], "node_name": nodes[i]["name"],
                           "host": nodes[i]["host"], "error": str(r)})
        else:
            output.append(r)
    return output


# ── #14 Cert Conflict Rate ─────────────────────────────────────────────────────
@router.get("/diagnostics/cert-conflicts")
async def get_cert_conflicts(cluster_id: int) -> list[dict]:
    """
    #14 Certificate Conflict Rate — wsrep_local_cert_failures + wsrep_local_replays.
    High cert failures = concurrent write conflicts between nodes.
    Alert threshold: cert_failures > 0 in the last interval.
    """
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    async def fetch_cert(node: dict) -> dict:
        result = {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "wsrep_local_cert_failures": None,
            "wsrep_local_replays":       None,
            "wsrep_cert_deps_distance":  None,
            "wsrep_local_bf_aborts":     None,
            "alert":  False,
            "error":  None,
        }
        try:
            db = DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node.get("db_user") or "root",
                encrypted_password=node.get("db_password") or "",
            )
            db.connect()
            try:
                rows = db.query(
                    "SHOW GLOBAL STATUS WHERE Variable_name IN ("
                    "'wsrep_local_cert_failures',"
                    "'wsrep_local_replays',"
                    "'wsrep_cert_deps_distance',"
                    "'wsrep_local_bf_aborts')"
                )
                sm = {(r.get("Variable_name") or r.get("variable_name") or "").lower():
                      (r.get("Value") or r.get("value") or "0") for r in rows}
                for field_name in ("wsrep_local_cert_failures", "wsrep_local_replays",
                                   "wsrep_local_bf_aborts"):
                    try:
                        result[field_name] = int(sm.get(field_name, "0") or "0")
                    except ValueError:
                        pass
                try:
                    result["wsrep_cert_deps_distance"] = float(sm.get("wsrep_cert_deps_distance", "0") or "0")
                except ValueError:
                    pass
                cf = result.get("wsrep_local_cert_failures")
                result["alert"] = cf is not None and cf > 0
            finally:
                db.close()
        except DBError as exc:
            result["error"] = str(exc)
        return result

    tasks = [fetch_cert(node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({"node_id": nodes[i]["id"], "node_name": nodes[i]["name"],
                           "host": nodes[i]["host"], "error": str(r)})
        else:
            output.append(r)
    return output


# ── #13 Disk Space Sentinel ────────────────────────────────────────────────────
@router.get("/diagnostics/disk-sentinel")
async def get_disk_sentinel(cluster_id: int) -> list[dict]:
    """
    #13 Disk Space Sentinel — Galera-aware disk check.
    Per node: gcache.size (from wsrep_provider_options), actual galera.cache file size,
    ibdata1 size (SSH du), data dir free space.
    Alert if: free < 10GB, or gcache file > configured size (cache overflow), or ibdata1 > 10GB.
    """
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    def fetch_sentinel(node: dict) -> dict:
        result = {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "gcache_configured_bytes":  None,
            "gcache_file_size_bytes":   None,
            "ibdata1_size_bytes":       None,
            "datadir_free_bytes":       None,
            "datadir_total_bytes":      None,
            "sst_method":               None,
            "alert_free_space":         False,
            "alert_gcache_overflow":    False,
            "alert_ibdata1_large":      False,
            "error":                    None,
        }
        ssh_err = None
        db_err  = None

        # SSH: file sizes
        try:
            with SSHClient(
                host=node["host"],
                port=int(node.get("ssh_port") or 22),
                username=node.get("ssh_user") or "root",
            ) as ssh:
                # ibdata1 size
                ibdata, _ = ssh.execute(
                    "du -sb /var/lib/mysql/ibdata1 2>/dev/null | awk '{print $1}' || echo ''"
                )
                try:
                    result["ibdata1_size_bytes"] = int(ibdata.strip())
                except ValueError:
                    pass

                # galera.cache size
                gcache, _ = ssh.execute(
                    "stat -c%s /var/lib/mysql/galera.cache 2>/dev/null || echo ''"
                )
                try:
                    result["gcache_file_size_bytes"] = int(gcache.strip())
                except ValueError:
                    pass

                # Data dir free space
                df_out, _ = ssh.execute(
                    "df -B1 /var/lib/mysql 2>/dev/null | tail -1"
                )
                parts = df_out.strip().split()
                if len(parts) >= 4:
                    try:
                        result["datadir_total_bytes"] = int(parts[1])
                        result["datadir_free_bytes"]  = int(parts[3])
                    except ValueError:
                        pass
        except SSHError as exc:
            ssh_err = str(exc)

        # DB: wsrep_provider_options for gcache.size, sst method
        try:
            db = DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node.get("db_user") or "root",
                encrypted_password=node.get("db_password") or "",
            )
            db.connect()
            try:
                prov_rows = db.query("SHOW GLOBAL VARIABLES LIKE 'wsrep_provider_options'")
                if prov_rows:
                    prov_val = prov_rows[0].get("Value") or prov_rows[0].get("value") or ""
                    for part in prov_val.split(";"):
                        part = part.strip()
                        if "gcache.size" in part:
                            try:
                                val_str = part.split("=", 1)[1].strip()
                                if val_str.endswith("M"):
                                    result["gcache_configured_bytes"] = int(float(val_str[:-1]) * 1024 * 1024)
                                elif val_str.endswith("G"):
                                    result["gcache_configured_bytes"] = int(float(val_str[:-1]) * 1024 * 1024 * 1024)
                                else:
                                    result["gcache_configured_bytes"] = int(val_str)
                            except (ValueError, IndexError):
                                pass

                sst_rows = db.query("SHOW GLOBAL VARIABLES LIKE 'wsrep_sst_method'")
                if sst_rows:
                    result["sst_method"] = sst_rows[0].get("Value") or sst_rows[0].get("value")
            finally:
                db.close()
        except DBError as exc:
            db_err = str(exc)

        if ssh_err and db_err:
            result["error"] = f"SSH: {ssh_err}; DB: {db_err}"
        elif ssh_err:
            result["error"] = f"SSH: {ssh_err}"
        elif db_err:
            result["error"] = f"DB: {db_err}"

        # Alerts
        free = result.get("datadir_free_bytes")
        result["alert_free_space"] = free is not None and free < 10 * 1024 * 1024 * 1024  # < 10GB

        gc_conf = result.get("gcache_configured_bytes")
        gc_file = result.get("gcache_file_size_bytes")
        result["alert_gcache_overflow"] = (
            gc_conf is not None and gc_file is not None and gc_file > gc_conf * 1.2
        )

        ibdata = result.get("ibdata1_size_bytes")
        result["alert_ibdata1_large"] = ibdata is not None and ibdata > 10 * 1024 * 1024 * 1024  # > 10GB

        return result

    tasks = [asyncio.to_thread(fetch_sentinel, node) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({"node_id": nodes[i]["id"], "node_name": nodes[i]["name"],
                           "host": nodes[i]["host"], "error": str(r)})
        else:
            output.append(r)
    return output


# ── #15 Quorum Status ─────────────────────────────────────────────────────────
@router.get("/diagnostics/quorum-status")
async def get_quorum_status(cluster_id: int) -> dict:
    """
    #15 Quorum Status — cluster-level quorum health.
    Returns: primary_count, non_primary_count, expected_nodes from settings,
    quorum_ok, wsrep_cluster_status per node.
    """
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    total_configured = len(nodes)

    async def fetch_wsrep_status(node: dict) -> dict:
        r: dict = {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "wsrep_cluster_status": None,
            "wsrep_cluster_size":   None,
            "wsrep_local_state_comment": None,
            "wsrep_connected": None,
            "error": None,
        }
        try:
            db = DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node.get("db_user") or "root",
                encrypted_password=node.get("db_password") or "",
            )
            db.connect()
            try:
                rows = db.query(
                    "SHOW GLOBAL STATUS WHERE Variable_name IN ("
                    "'wsrep_cluster_status','wsrep_cluster_size',"
                    "'wsrep_local_state_comment','wsrep_connected')"
                )
                sm = {(row.get("Variable_name") or row.get("variable_name") or "").lower():
                      (row.get("Value") or row.get("value") or "") for row in rows}
                r["wsrep_cluster_status"]        = sm.get("wsrep_cluster_status", "NON-PRIMARY")
                r["wsrep_local_state_comment"]   = sm.get("wsrep_local_state_comment", "OFFLINE")
                r["wsrep_connected"]             = sm.get("wsrep_connected", "OFF")
                try:
                    r["wsrep_cluster_size"] = int(sm.get("wsrep_cluster_size", "0") or "0")
                except ValueError:
                    r["wsrep_cluster_size"] = 0
            finally:
                db.close()
        except DBError as exc:
            r["error"] = str(exc)
            r["wsrep_cluster_status"] = "OFFLINE"
        return r

    tasks = [fetch_wsrep_status(node) for node in nodes]
    node_results = await asyncio.gather(*tasks, return_exceptions=True)

    node_statuses = []
    for i, r in enumerate(node_results):
        if isinstance(r, Exception):
            node_statuses.append({
                "node_id": nodes[i]["id"],
                "node_name": nodes[i]["name"],
                "host": nodes[i]["host"],
                "wsrep_cluster_status": "OFFLINE",
                "error": str(r),
            })
        else:
            node_statuses.append(r)

    primary_nodes     = [n for n in node_statuses if (n.get("wsrep_cluster_status") or "").upper() == "PRIMARY"]
    non_primary_nodes = [n for n in node_statuses if (n.get("wsrep_cluster_status") or "").upper() != "PRIMARY"
                         and not n.get("error")]
    offline_nodes     = [n for n in node_statuses if n.get("error") or
                         (n.get("wsrep_cluster_status") or "OFFLINE") == "OFFLINE"]

    primary_count = len(primary_nodes)
    quorum_ok     = primary_count > 0 and primary_count > total_configured // 2

    # Get cluster_size from first primary node
    cluster_size = next(
        (n.get("wsrep_cluster_size") for n in primary_nodes if n.get("wsrep_cluster_size")),
        None,
    )

    status = "healthy" if quorum_ok and primary_count == total_configured else \
             "degraded" if quorum_ok else "critical"

    return {
        "cluster_id":          cluster_id,
        "total_configured":    total_configured,
        "primary_count":       primary_count,
        "non_primary_count":   len(non_primary_nodes),
        "offline_count":       len(offline_nodes),
        "cluster_size":        cluster_size,
        "quorum_ok":           quorum_ok,
        "status":              status,
        "nodes":               node_statuses,
    }
