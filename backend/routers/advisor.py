from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from database import engine, get_cluster_or_404
from dependencies import require_auth
from services.db_client import DBClient, DBError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clusters/{cluster_id}/advisor",
    tags=["advisor"],
    dependencies=[Depends(require_auth)],
)


# ── Enums ─────────────────────────────────────────────────────────────────────

class AdvisorSeverity(str, Enum):
    info = "info"
    warn = "warn"
    critical = "critical"


class AdvisorCategory(str, Enum):
    config = "config"
    performance = "performance"
    replication = "replication"
    availability = "availability"
    storage = "storage"
    sst = "sst"
    maintenance = "maintenance"


class AdvisorActionType(str, Enum):
    none = "none"
    open_panel = "open_panel"
    node_action = "node_action"
    config_change = "config_change"
    recovery = "recovery"


# ── Models ────────────────────────────────────────────────────────────────────

class AdvisorEvidence(BaseModel):
    node_ids: list[int] | None = None
    node_names: list[str] | None = None
    params: dict[str, Any] | None = None
    raw_refs: list[dict[str, Any]] | None = None


class AdvisorAction(BaseModel):
    action_type: AdvisorActionType = AdvisorActionType.none
    action_id: str | None = None
    description: str | None = None
    ui_hint: str | None = None
    danger_level: AdvisorSeverity | None = None


class AdvisorCard(BaseModel):
    id: str
    severity: AdvisorSeverity
    category: AdvisorCategory
    source: str
    title: str
    summary: str
    details: str | None = None
    evidence: AdvisorEvidence | None = None
    recommended_action: AdvisorAction | None = None


class AdvisorResponse(BaseModel):
    cluster_id: int
    generated_at: datetime
    advisors: list[AdvisorCard]


# ── Internal DB helpers ───────────────────────────────────────────────────────

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

async def _collect_node_availability(cluster_id: int) -> list[dict]:

    from services.poller import live_node_states

    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)
    if not nodes:
        return []

    cluster_states = live_node_states.get(cluster_id, {})
    result = []
    for node in nodes:
        state = cluster_states.get(node["id"])
        ssh_ok = state.ssh_ok if state else False
        result.append({
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "ssh_ok":    ssh_ok,
        })
    return result

# ── Data collectors ───────────────────────────────────────────────────────────

async def _collect_config_health(cluster_id: int) -> list[dict]:
    """
    Re-use _fetch_config_health from diagnostics module.
    Returns list of {node_id, node_name, host, checks, error}.
    """
    from routers.diagnostics import _fetch_config_health

    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)
    tasks = [asyncio.to_thread(_fetch_config_health, node) for node in nodes]
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


def _fetch_active_transactions_for_node(node: dict, min_age_sec: int = 60) -> dict:
    """Fetch long-running transactions from a single node."""
    if not node.get("db_user") or not node.get("db_password"):
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "trx_list":  [],
            "error":     "No DB credentials configured",
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
                    t.trx_state,
                    DATE_FORMAT(t.trx_started, '%Y-%m-%dT%H:%i:%S') AS trx_started,
                    TIMESTAMPDIFF(SECOND, t.trx_started, NOW())      AS trx_age_sec,
                    t.trx_mysql_thread_id,
                    t.trx_query,
                    t.trx_tables_locked,
                    t.trx_rows_locked,
                    t.trx_rows_modified,
                    p.user,
                    p.host AS process_host
                FROM information_schema.INNODB_TRX t
                LEFT JOIN information_schema.PROCESSLIST p
                       ON p.ID = t.trx_mysql_thread_id
                WHERE TIMESTAMPDIFF(SECOND, t.trx_started, NOW()) >= %s
                ORDER BY trx_age_sec DESC
                LIMIT 20
                """,
                (min_age_sec,),
            )
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "trx_list":  [
                {
                    "trx_id":              r.get("trx_id"),
                    "trx_state":           r.get("trx_state"),
                    "trx_started":         r.get("trx_started"),
                    "trx_age_sec":         r.get("trx_age_sec"),
                    "trx_mysql_thread_id": r.get("trx_mysql_thread_id"),
                    "trx_query":           r.get("trx_query"),
                    "trx_tables_locked":   r.get("trx_tables_locked"),
                    "trx_rows_locked":     r.get("trx_rows_locked"),
                    "trx_rows_modified":   r.get("trx_rows_modified"),
                    "user":                r.get("user"),
                    "host":                r.get("process_host"),
                }
                for r in rows
            ],
            "error": None,
        }
    except DBError as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "trx_list":  [],
            "error":     str(exc),
        }
    except Exception as exc:
        return {
            "node_id":   node["id"],
            "node_name": node["name"],
            "host":      node["host"],
            "trx_list":  [],
            "error":     str(exc),
        }


async def _collect_active_transactions(cluster_id: int) -> list[dict]:
    """Return long-running transactions (age >= 60s) across all nodes."""
    nodes = await asyncio.to_thread(_get_enabled_nodes, cluster_id)
    tasks = [asyncio.to_thread(_fetch_active_transactions_for_node, node, 60) for node in nodes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            output.append({
                "node_id":   node["id"],
                "node_name": node["name"],
                "host":      node["host"],
                "trx_list":  [],
                "error":     str(result),
            })
        else:
            output.append(result)
    return output


async def _collect_sst_status(cluster_id: int) -> list[dict]:
    """
    Return SST-stuck nodes from poller live state.

    Reads directly from services.poller.live_node_states (dict[cluster_id → dict[node_id → LiveNodeState]])
    and cross-references with DB node names.
    A node is considered stuck when wsrep_local_state_comment is in SST_STUCK_STATES
    and state_since_ts is set (meaning it has been in that state since state_since_ts).
    SST_STUCK_THRESHOLD_SEC is imported from poller to stay in sync.
    """
    from services.poller import live_node_states, SST_STUCK_THRESHOLD_SEC, SST_STUCK_STATES

    cluster_states = live_node_states.get(cluster_id)
    if not cluster_states:
        return []

    # Load node meta from DB for names/hosts (cached per request — small table)
    nodes_meta = await asyncio.to_thread(_get_enabled_nodes_with_id, cluster_id)
    node_meta_map: dict[int, dict] = {n["id"]: n for n in nodes_meta}

    now = datetime.now(timezone.utc)
    result = []

    for node_id, state in cluster_states.items():
        wsrep_state = state.wsrep_local_state_comment
        if wsrep_state.upper() not in SST_STUCK_STATES:
            continue

        # Calculate how long the node has been in this state
        stuck_for_sec = 0
        is_stuck = False
        if state.state_since_ts is not None:
            stuck_for_sec = int((now - state.state_since_ts).total_seconds())
            is_stuck = stuck_for_sec >= SST_STUCK_THRESHOLD_SEC

        meta = node_meta_map.get(node_id, {})
        result.append({
            "node_id":       node_id,
            "node_name":     meta.get("name", f"node-{node_id}"),
            "host":          meta.get("host", ""),
            "wsrep_state":   wsrep_state,
            "is_stuck":      is_stuck,
            "stuck_for_sec": stuck_for_sec,
        })

    return result


async def _collect_replication_lag(cluster_id: int) -> list[dict]:
    """
    Return recv_queue average per node from poller ring buffer.

    Uses recv_queue_history deque (up to 30 points) from LiveNodeState.
    avg = mean of last N points in the ring buffer.
    Only includes nodes that are reachable (ssh_ok=True) and have data.
    """
    from services.poller import live_node_states

    cluster_states = live_node_states.get(cluster_id)
    if not cluster_states:
        return []

    nodes_meta = await asyncio.to_thread(_get_enabled_nodes_with_id, cluster_id)
    node_meta_map: dict[int, dict] = {n["id"]: n for n in nodes_meta}

    lag_data = []
    for node_id, state in cluster_states.items():
        if not state.ssh_ok:
            continue
        history = list(state.recv_queue_history)
        if not history:
            continue
        avg = sum(history) / len(history)
        meta = node_meta_map.get(node_id, {})
        lag_data.append({
            "node_id":        node_id,
            "node_name":      meta.get("name", f"node-{node_id}"),
            "host":           meta.get("host", ""),
            "recv_queue_avg": avg,
        })

    return lag_data


async def _collect_disk_usage(cluster_id: int) -> list[dict]:
    """
    Disk usage data is NOT collected by the poller (LiveNodeState has no disk fields).
    Returns empty list — disk advisor cards will not fire until disk collection is implemented.
    """
    return []


# ── Internal helper: nodes with id ───────────────────────────────────────────

def _get_enabled_nodes_with_id(cluster_id: int) -> list[dict]:
    """Like _get_enabled_nodes but always includes id, name, host."""
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


# ── Rules engine ──────────────────────────────────────────────────────────────

def _rules_availability(availability_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []
    if not availability_results:
        return cards

    total      = len(availability_results)
    unreachable = [n for n in availability_results if not n["ssh_ok"]]
    if not unreachable:
        return cards

    all_down  = len(unreachable) == total
    severity  = AdvisorSeverity.critical
    node_names = [n["node_name"] for n in unreachable]
    node_ids   = [n["node_id"]   for n in unreachable]

    if all_down:
        title   = "All cluster nodes are unreachable"
        summary = "Orchestrator cannot connect to any node via SSH. MariaDB may be down or SSH credentials are invalid."
    else:
        title   = f"{len(unreachable)} of {total} node(s) unreachable"
        summary = f"Nodes {', '.join(node_names)} are not reachable via SSH. Cluster may be degraded."

    cards.append(AdvisorCard(
        id="node-availability",
        severity=severity,
        category=AdvisorCategory.availability,
        source="node-availability",
        title=title,
        summary=summary,
        details="SSH connectivity is required for monitoring and management. Check node status and SSH credentials.",
        evidence=AdvisorEvidence(
            node_ids=node_ids,
            node_names=node_names,
        ),
        recommended_action=AdvisorAction(
            action_type=AdvisorActionType.open_panel,
            action_id="open-connections",
            description="Run Connection Check to diagnose SSH and DB connectivity.",
            ui_hint="open-diagnostics-tab:connections",
            danger_level=AdvisorSeverity.critical,
        ),
    ))
    return cards

def _rules_config_health(config_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []

    SEVERITY_MAP = {"error": AdvisorSeverity.critical, "warn": AdvisorSeverity.warn}
    ACTIONABLE_PARAMS = {
        "innodb_buffer_pool_size",
        "max_connections",
        "wsrep_slave_threads",
        "innodb_flush_log_at_trx_commit",
    }

    for node_result in config_results:
        if node_result.get("error"):
            continue
        for chk in node_result.get("checks", []):
            if chk["status"] not in ("error", "warn"):
                continue
            if chk["param"] not in ACTIONABLE_PARAMS:
                continue

            severity  = SEVERITY_MAP.get(chk["status"], AdvisorSeverity.warn)
            param     = chk["param"]
            node_name = node_result["node_name"]
            node_id   = node_result["node_id"]

            cards.append(AdvisorCard(
                id=f"config-{param.replace('_', '-')}-{node_id}",
                severity=severity,
                category=AdvisorCategory.config,
                source="config-health",
                title=f"{param} needs attention on {node_name}",
                summary=chk.get("recommendation") or f"{param} is not optimal.",
                details=chk.get("context"),
                evidence=AdvisorEvidence(
                    node_ids=[node_id],
                    node_names=[node_name],
                    params={"current_value": chk.get("current_human")},
                    raw_refs=[{"source": "config-health", "param": param, "node_id": node_id}],
                ),
                recommended_action=AdvisorAction(
                    action_type=AdvisorActionType.config_change,
                    action_id=f"tune-{param.replace('_', '-')}",
                    description=chk.get("recommendation"),
                    ui_hint="open-diagnostics-tab:config-health",
                    danger_level=AdvisorSeverity.warn,
                ),
            ))

    return cards


def _rules_active_transactions(trx_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []

    for node_result in trx_results:
        if node_result.get("error") or not node_result.get("trx_list"):
            continue

        trx_list  = node_result["trx_list"]
        max_age   = max((t.get("trx_age_sec") or 0) for t in trx_list)
        count     = len(trx_list)
        node_name = node_result["node_name"]
        node_id   = node_result["node_id"]

        severity = AdvisorSeverity.critical if max_age >= 900 else AdvisorSeverity.warn

        top3 = sorted(trx_list, key=lambda t: t.get("trx_age_sec") or 0, reverse=True)[:3]
        evidence_rows = [
            {
                "trx_id":    t.get("trx_id"),
                "thread_id": t.get("trx_mysql_thread_id"),
                "age_sec":   t.get("trx_age_sec"),
                "query":     (t.get("trx_query") or "")[:120],
            }
            for t in top3
        ]

        cards.append(AdvisorCard(
            id=f"long-trx-{node_id}",
            severity=severity,
            category=AdvisorCategory.performance,
            source="active-transactions",
            title=f"{count} long-running transaction(s) on {node_name}",
            summary=f"Longest transaction is {max_age}s old. Long transactions can cause row-lock contention and replication lag.",
            details=f"{count} transaction(s) running longer than 60 seconds. Oldest: {max_age}s.",
            evidence=AdvisorEvidence(
                node_ids=[node_id],
                node_names=[node_name],
                params={"max_age_sec": max_age, "count": count},
                raw_refs=evidence_rows,
            ),
            recommended_action=AdvisorAction(
                action_type=AdvisorActionType.open_panel,
                action_id="open-active-transactions",
                description="Review and kill long-running transactions if safe.",
                ui_hint="open-diagnostics-tab:active-transactions",
                danger_level=AdvisorSeverity.warn,
            ),
        ))

    return cards


def _rules_sst(sst_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []

    for node in sst_results:
        if not node.get("is_stuck"):
            continue

        stuck_sec = node.get("stuck_for_sec", 0)
        cards.append(AdvisorCard(
            id=f"sst-stuck-{node['node_id']}",
            severity=AdvisorSeverity.critical,
            category=AdvisorCategory.sst,
            source="sst-status",
            title=f"Node {node['node_name']} is stuck in SST/IST",
            summary=f"Node has been in '{node['wsrep_state']}' state for {stuck_sec}s. Manual intervention required.",
            details="A stuck SST/IST can block donor node performance and cause cluster stall.",
            evidence=AdvisorEvidence(
                node_ids=[node["node_id"]],
                node_names=[node["node_name"]],
                params={"wsrep_state": node["wsrep_state"], "stuck_for_sec": stuck_sec},
            ),
            recommended_action=AdvisorAction(
                action_type=AdvisorActionType.node_action,
                action_id="restart-sst",
                description="Restart SST on the stuck node.",
                ui_hint="open-diagnostics-tab:sst-status",
                danger_level=AdvisorSeverity.critical,
            ),
        ))

    return cards


def _rules_replication_lag(lag_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []

    LAG_WARN     = 0.5
    LAG_CRITICAL = 2.0

    lagging = [n for n in lag_results if n["recv_queue_avg"] >= LAG_WARN]
    if not lagging:
        return cards

    max_lag    = max(n["recv_queue_avg"] for n in lagging)
    severity   = AdvisorSeverity.critical if max_lag >= LAG_CRITICAL else AdvisorSeverity.warn
    node_names = [n["node_name"] for n in lagging]
    node_ids   = [n["node_id"]   for n in lagging]

    cards.append(AdvisorCard(
        id="replication-lag",
        severity=severity,
        category=AdvisorCategory.replication,
        source="replication-lag",
        title=f"Replication lag detected on {len(lagging)} node(s)",
        summary=f"wsrep_local_recv_queue avg={max_lag:.2f} — receiver queue is growing. Consider increasing wsrep_slave_threads.",
        details="A non-zero recv_queue indicates the node can't apply writesets fast enough. This may lead to stale reads and OOM under load.",
        evidence=AdvisorEvidence(
            node_ids=node_ids,
            node_names=node_names,
            params={"max_recv_queue_avg": max_lag, "lagging_nodes": len(lagging)},
        ),
        recommended_action=AdvisorAction(
            action_type=AdvisorActionType.config_change,
            action_id="tune-wsrep-slave-threads",
            description="Increase wsrep_slave_threads (recommended: number of CPU cores).",
            ui_hint="open-diagnostics-tab:config-health",
            danger_level=AdvisorSeverity.warn,
        ),
    ))

    return cards


def _rules_disk(disk_results: list[dict]) -> list[AdvisorCard]:
    cards: list[AdvisorCard] = []

    WARN_RATIO     = 0.80
    CRITICAL_RATIO = 0.90

    for node in disk_results:
        ratio = node["ratio"]
        if ratio < WARN_RATIO:
            continue

        severity = AdvisorSeverity.critical if ratio >= CRITICAL_RATIO else AdvisorSeverity.warn
        used_gb  = node["used_bytes"]  / (1024 ** 3)
        total_gb = node["total_bytes"] / (1024 ** 3)

        cards.append(AdvisorCard(
            id=f"disk-usage-{node['node_id']}",
            severity=severity,
            category=AdvisorCategory.storage,
            source="disk-usage",
            title=f"High disk usage on {node['node_name']}",
            summary=f"Disk is {ratio * 100:.1f}% full ({used_gb:.1f} GB of {total_gb:.1f} GB used).",
            details="Running out of disk space will cause MariaDB to crash and the node to leave the cluster.",
            evidence=AdvisorEvidence(
                node_ids=[node["node_id"]],
                node_names=[node["node_name"]],
                params={
                    "used_bytes":  node["used_bytes"],
                    "total_bytes": node["total_bytes"],
                    "ratio":       round(ratio, 4),
                },
            ),
            recommended_action=AdvisorAction(
                action_type=AdvisorActionType.open_panel,
                action_id="open-disk-usage",
                description="Review large tables and binary logs. Consider purging old binary logs.",
                ui_hint="open-diagnostics-tab:disk-usage",
                danger_level=AdvisorSeverity.critical,
            ),
        ))

    return cards


# ── Sorting / dedup ───────────────────────────────────────────────────────────

_SEVERITY_ORDER = {
    AdvisorSeverity.critical: 0,
    AdvisorSeverity.warn:     1,
    AdvisorSeverity.info:     2,
}


def _sort_and_dedup(cards: list[AdvisorCard]) -> list[AdvisorCard]:
    seen:   set[str]       = set()
    unique: list[AdvisorCard] = []
    for card in sorted(cards, key=lambda c: _SEVERITY_ORDER.get(c.severity, 99)):
        if card.id not in seen:
            seen.add(card.id)
            unique.append(card)
    return unique


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("", response_model=AdvisorResponse)
async def get_advisor(cluster_id: int) -> AdvisorResponse:
    """
    Aggregate diagnostic signals for the cluster and return advisor cards.
    Each card has severity (info/warn/critical), evidence, and a recommended action.
    """
    # Validate cluster exists (raises 404 if not)
    await asyncio.to_thread(get_cluster_or_404, cluster_id)

    (
        availability_results,
        config_results,
        trx_results,
        sst_results,
        lag_results,
        disk_results,
    ) = await asyncio.gather(
        _collect_node_availability(cluster_id),
        _collect_config_health(cluster_id),
        _collect_active_transactions(cluster_id),
        _collect_sst_status(cluster_id),
        _collect_replication_lag(cluster_id),
        _collect_disk_usage(cluster_id),
        return_exceptions=False,
    )

    cards: list[AdvisorCard] = []
    cards.extend(_rules_availability(availability_results))
    cards.extend(_rules_config_health(config_results))
    cards.extend(_rules_active_transactions(trx_results))
    cards.extend(_rules_sst(sst_results))
    cards.extend(_rules_replication_lag(lag_results))
    cards.extend(_rules_disk(disk_results))

    return AdvisorResponse(
        cluster_id=cluster_id,
        generated_at=datetime.now(timezone.utc),
        advisors=_sort_and_dedup(cards),
    )
