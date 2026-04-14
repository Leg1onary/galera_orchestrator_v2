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
# innodb-status lives in routers/nodes.py — not duplicated here.
# Timeouts (ТЗ 15.11): SSH connect=5s, DB connect=3s, SSH exec=10s.

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
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
#
# journalctl выводит служебные строки вроде "-- No entries --" или
# "-- Logs begin at Mon 2026-04-13..." — фильтруем их.
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


# ── _fetch_arbitrator_log (Variant A) ───────────────────────────────────────────────
#
# Стратегия поиска лога garbd (в порядке приоритета):
#
#   1. journalctl с несколькими именами unit:
#      garbd → garb → garbd@ (systemd prefix match)
#      Каждый вызов — отдельный execute(), без || цепочек.
#
#   2. Файловые fallback-и через отдельные execute():
#      /var/log/garbd.log
#      /var/log/garbd/garbd.log
#      /var/log/garb/garbd.log
#      Раздельные вызовы исключают баг: файл есть, но пуст → exit 0 →
#      || цепочка останавливается и не пробует следующий путь.
#
#   3. Last resort: journalctl без unit-фильтра + grep garb.
#      Ловит случаи когда сервис логируется под другим именем.
#
# Поле `source` в ответе показывает откуда взяты строки.
# При lines=[] && error=null фронт должен показывать
# "garbd log not found on this host", а не пустой блок.

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

            # 1. journalctl — пробуем несколько имён unit по очереди
            for unit in _GARBD_SYSTEMD_UNITS:
                stdout, _ = client.execute(
                    f"journalctl -u {unit} -n {lines} --no-pager 2>/dev/null"
                )
                candidate = _filter_journalctl_noise(stdout)
                if candidate:
                    log_lines = candidate
                    source_used = f"journalctl -u {unit}"
                    break

            # 2. Файловые fallback-и — каждый файл отдельным execute()
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

            # 3. Last resort: journalctl без unit-фильтра + grep
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

# Пробуем кандидатов по очереди, возвращаем первый непустой результат.
# Каждый кандидат работает через отдельный execute() — нет бага с пустым
# файлом в || цепочке (файл есть, но пустой → exit 0 → цепочка останавливается).
_ERROR_LOG_CANDIDATES = [
    # systemd (Debian/Ubuntu/RHEL при systemd-based установке)
    ("journalctl", "journalctl -u mariadb -n {lines} --no-pager 2>/dev/null"),
    # Debian/Ubuntu классика
    ("file",        "tail -n {lines} /var/log/mysql/error.log 2>/dev/null"),
    # RHEL/CentOS/Rocky
    ("file",        "tail -n {lines} /var/log/mariadb/mariadb.log 2>/dev/null"),
    # альтернатива RHEL
    ("file",        "tail -n {lines} /var/log/mysqld.log 2>/dev/null"),
    # datadir fallback: ищем через find — не glob, чтобы shell раскрыл glob
    ("file",        "find /var/lib/mysql -maxdepth 1 -name '*.err' 2>/dev/null | head -1 | xargs -r tail -n {lines}"),
]


def _fetch_error_log(node: dict, lines: int) -> dict:
    """
    Читаем error log через SSH.

    Пробуем кандидатов в порядке приоритета:
      1. journalctl -u mariadb   (фильтруем шум)
      2. /var/log/mysql/error.log
      3. /var/log/mariadb/mariadb.log
      4. /var/log/mysqld.log
      5. find /var/lib/mysql -name '*.err' | xargs tail
    Возвращаем первый непустой результат.
    """
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


# ── Slow query helpers ───────────────────────────────────────────────────────────────

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
            # Check if slow_query_log is enabled
            var_rows = client.query("SHOW GLOBAL VARIABLES LIKE 'slow_query_log'")
            slow_log_enabled: bool | None = None
            if var_rows:
                slow_log_enabled = var_rows[0]["Value"].upper() == "ON"

            rows = []
            if slow_log_enabled:
                raw = client.query(
                    "SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 500"
                )
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

        return {
            "node_id":          node["id"],
            "node_name":        node["name"],
            "slow_log_enabled": slow_log_enabled,
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


# ── Process list helpers ─────────────────────────────────────────────────────────────

def _fetch_process_list(node: dict) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "processes": [],
            "error":     "No DB credentials configured",
        }
    try:
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            raw = client.query("SHOW FULL PROCESSLIST")
            processes = [
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
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "processes": processes,
            "error":     None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "processes": [],
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "processes": [],
            "error":     str(exc),
        }


# ── Galera status helpers ────────────────────────────────────────────────────────────

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
            rows = client.query("SHOW STATUS LIKE 'wsrep_%'")
            status = {r["Variable_name"]: r["Value"] for r in rows}
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "status":    status,
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


# ── check-all helpers ────────────────────────────────────────────────────────────────

def _check_node(node: dict) -> dict:
    ssh = _probe_node_ssh(node)
    db  = _probe_node_db(node)
    return {
        "node_id":       node["id"],
        "node_name":     node["name"],
        "host":          node["host"],
        "role":          "node",
        **ssh,
        **db,
    }


def _check_arbitrator(arb: dict) -> dict:
    result = _probe_arbitrator(arb)
    return {
        "node_id":        arb["id"],
        "node_name":      arb["name"],
        "host":           arb["host"],
        "role":           "arbitrator",
        "ssh_ok":         result["ssh_ok"],
        "db_ok":          None,
        "ssh_latency_ms": result["latency_ssh_ms"],
        "db_latency_ms":  None,
        "ssh_error":      result["error"],
        "db_error":       None,
        "garbd_running":  result["garbd_running"],
        "latency_ssh_ms": result["latency_ssh_ms"],
    }


# ── config-diff helpers ──────────────────────────────────────────────────────────────

_DIFF_VARIABLES = [
    "wsrep_cluster_name",
    "wsrep_provider",
    "wsrep_slave_threads",
    "wsrep_sync_wait",
    "wsrep_sst_method",
    "innodb_buffer_pool_size",
    "innodb_flush_log_at_trx_commit",
    "sync_binlog",
    "max_connections",
    "character_set_server",
    "collation_server",
]


def _fetch_variables_for_diff(node: dict) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":    node["id"],
            "node_name":  node["name"],
            "host":       node["host"],
            "values":     {},
            "fetch_ok":   False,
            "error":      "No DB credentials configured",
        }
    try:
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            rows = client.query("SHOW GLOBAL VARIABLES")
            all_vars = {r["Variable_name"]: r["Value"] for r in rows}
            values = {v: all_vars.get(v) for v in _DIFF_VARIABLES}
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "values":    values,
            "fetch_ok":  True,
            "error":     None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "values":    {},
            "fetch_ok":  False,
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "values":    {},
            "fetch_ok":  False,
            "error":     str(exc),
        }


# ── variables helpers ────────────────────────────────────────────────────────────────

def _fetch_variables(node: dict, wsrep_only: bool = False) -> dict:
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "total":     0,
            "variables": [],
            "error":     "No DB credentials configured",
        }
    try:
        with DBClient(
                host=node["host"],
                port=int(node.get("port") or 3306),
                user=node["db_user"],
                encrypted_password=node["db_password"],
        ) as client:
            if wsrep_only:
                rows = client.query(
                    "SHOW GLOBAL VARIABLES WHERE Variable_name LIKE 'wsrep%'"
                )
            else:
                rows = client.query("SHOW GLOBAL VARIABLES")
            variables = [
                {"name": r["Variable_name"], "value": r["Value"]}
                for r in rows
            ]
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "total":     len(variables),
            "variables": variables,
            "error":     None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "total":     0,
            "variables": [],
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "total":     0,
            "variables": [],
            "error":     str(exc),
        }


# ── Routes ───────────────────────────────────────────────────────────────────────────

@router.post("/diagnostics/check-all")
async def check_all(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    arbs  = _get_enabled_arbitrators(cluster_id)

    node_results = await asyncio.gather(*[
        asyncio.to_thread(_check_node, n) for n in nodes
    ])
    arb_results = await asyncio.gather(*[
        asyncio.to_thread(_check_arbitrator, a) for a in arbs
    ])

    return {
        "nodes":        list(node_results),
        "arbitrators":  list(arb_results),
    }


@router.get("/diagnostics/config-diff")
async def config_diff(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)

    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_variables_for_diff, n) for n in nodes
    ])

    variable_rows = []
    for var in _DIFF_VARIABLES:
        values_list = [
            {
                "node_id":    r["node_id"],
                "node_name":  r["node_name"],
                "value":      r["values"].get(var) if r["fetch_ok"] else None,
                "fetch_error": not r["fetch_ok"],
            }
            for r in results
        ]
        unique_vals = set(
            v["value"] for v in values_list
            if not v["fetch_error"] and v["value"] is not None
        )
        variable_rows.append({
            "variable": var,
            "values":   values_list,
            "has_diff": len(unique_vals) > 1,
        })

    return {
        "variables":  variable_rows,
        "nodes":      [{"node_id": r["node_id"], "node_name": r["node_name"], "host": r["host"], "fetch_ok": r["fetch_ok"]} for r in results],
        "diff_found": any(row["has_diff"] for row in variable_rows),
    }


@router.get("/diagnostics/variables")
async def variables(
        cluster_id: int,
        node_id: int = Query(...),
        wsrep_only: bool = Query(False),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
        )
    return await asyncio.to_thread(_fetch_variables, node, wsrep_only)


@router.get("/diagnostics/variables/all")
async def variables_all(
        cluster_id: int,
        wsrep_only: bool = Query(False),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_variables, n, wsrep_only) for n in nodes
    ])
    return list(results)


@router.post("/diagnostics/resources")
async def resources(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_resources, n) for n in nodes
    ])
    return {"nodes": list(results)}


@router.get("/diagnostics/galera-status")
async def galera_status(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_galera_status, n) for n in nodes
    ])
    return list(results)


@router.get("/diagnostics/process-list")
async def process_list(
        cluster_id: int,
        node_id: int | None = Query(None),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    if node_id is not None:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_process_list, n) for n in nodes
    ])
    return list(results)


@router.get("/diagnostics/slow-queries")
async def slow_queries(
        cluster_id: int,
        node_id: int | None = Query(None),
) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    nodes = _get_enabled_nodes(cluster_id)
    if node_id is not None:
        nodes = [n for n in nodes if n["id"] == node_id]
    results = await asyncio.gather(*[
        asyncio.to_thread(_fetch_slow_queries, n) for n in nodes
    ])
    return list(results)


@router.get("/nodes/{node_id}/error-log")
async def error_log(
        cluster_id: int,
        node_id: int,
        lines: int = Query(200, ge=10, le=2000),
) -> dict:
    _assert_cluster_exists(cluster_id)
    node = _get_node_for_cluster(node_id, cluster_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found or disabled in cluster {cluster_id}",
        )
    return await asyncio.to_thread(_fetch_error_log, node, lines)


@router.get("/arbitrators/{arb_id}/test-connection")
async def arbitrator_test_connection(
        cluster_id: int,
        arb_id: int,
) -> dict:
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_or_404(cluster_id, arb_id)
    result = _probe_arbitrator(arb)
    return {
        "ssh_ok":         result["ssh_ok"],
        "garbd_running":  result["garbd_running"],
        "latency_ssh_ms": result["latency_ssh_ms"],
        "error":          result["error"],
    }


@router.get("/arbitrators/{arb_id}/log")
async def arbitrator_log(
        cluster_id: int,
        arb_id: int,
        lines: int = Query(50, ge=10, le=500),
) -> dict:
    _assert_cluster_exists(cluster_id)
    arb = _get_arbitrator_or_404(cluster_id, arb_id)
    return await asyncio.to_thread(_fetch_arbitrator_log, arb, lines)
