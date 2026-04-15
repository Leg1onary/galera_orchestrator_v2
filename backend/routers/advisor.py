from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import get_current_user
from services.db_client import DBClient
from database import get_cluster_or_404

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clusters/{cluster_id}/advisor",
    tags=["advisor"],
    dependencies=[Depends(get_current_user)],
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
    ui_hint: str | None = None  # e.g. "open-diagnostics-tab:config-health"
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


# ── Data collectors ───────────────────────────────────────────────────────────

async def _get_cluster_nodes(cluster_id: int) -> list[dict]:
    """Return list of node dicts from DB for the given cluster."""
    from database import engine
    import sqlalchemy as sa
    from models import nodes_table, datacenters_table

    def _query():
        with engine.connect() as conn:
            stmt = (
                sa.select(
                    nodes_table.c.id,
                    nodes_table.c.name,
                    nodes_table.c.host,
                    nodes_table.c.port,
                    nodes_table.c.db_user,
                    nodes_table.c.db_password,
                )
                .where(nodes_table.c.cluster_id == cluster_id)
                .where(nodes_table.c.is_active == True)
            )
            return [dict(r._mapping) for r in conn.execute(stmt)]

    return await asyncio.to_thread(_query)


async def _collect_config_health(cluster_id: int) -> list[dict]:
    """
    Re-use logic from diagnostics config-health:
    return list of {node_id, node_name, host, checks: [{param, status, current_human,
    recommendation, context}], error}
    """
    from routers.diagnostics import _run_config_health_for_node

    nodes = await _get_cluster_nodes(cluster_id)
    results = []
    for node in nodes:
        try:
            checks = await asyncio.to_thread(_run_config_health_for_node, node)
            results.append({
                "node_id": node["id"],
                "node_name": node["name"],
                "host": node["host"],
                "checks": checks,
                "error": None,
            })
        except Exception as e:
            results.append({
                "node_id": node["id"],
                "node_name": node["name"],
                "host": node["host"],
                "checks": [],
                "error": str(e),
            })
    return results


async def _collect_active_transactions(cluster_id: int) -> list[dict]:
    """
    Return long-running transactions (age >= 60 sec) across all nodes.
    Returns list of {node_id, node_name, host, trx_list, error}.
    """
    nodes = await _get_cluster_nodes(cluster_id)
    results = []
    for node in nodes:
        try:
            db = DBClient(
                host=node["host"],
                port=node["port"],
                user=node["db_user"],
                password=node["db_password"],
            )

            def _query(db=db):
                with db.connect() as conn:
                    rows = conn.execute("""
                        SELECT
                            trx_id,
                            trx_state,
                            trx_started,
                            TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS trx_age_sec,
                            trx_mysql_thread_id,
                            trx_query,
                            trx_tables_in_use,
                            trx_tables_locked,
                            trx_rows_locked
                        FROM information_schema.INNODB_TRX
                        WHERE TIMESTAMPDIFF(SECOND, trx_started, NOW()) >= 60
                        ORDER BY trx_age_sec DESC
                        LIMIT 20
                    """).fetchall()
                    return [dict(r._mapping) for r in rows]

            trx_list = await asyncio.to_thread(_query)
            results.append({
                "node_id": node["id"],
                "node_name": node["name"],
                "host": node["host"],
                "trx_list": trx_list,
                "error": None,
            })
        except Exception as e:
            results.append({
                "node_id": node["id"],
                "node_name": node["name"],
                "host": node["host"],
                "trx_list": [],
                "error": str(e),
            })
    return results


async def _collect_sst_status(cluster_id: int) -> list[dict]:
    """
    Return SST-stuck nodes from poller state.
    """
    from services.poller import get_cluster_state

    state = get_cluster_state(cluster_id)
    if not state:
        return []

    stuck = []
    for node in state.get("nodes", []):
        wsrep_state = node.get("wsrep_local_state_comment", "")
        if wsrep_state in ("Joining", "Donor/Desynced", "Joined"):
            stuck.append({
                "node_id": node.get("id"),
                "node_name": node.get("name"),
                "host": node.get("host"),
                "wsrep_state": wsrep_state,
                "is_stuck": node.get("sst_stuck", False),
                "stuck_for_sec": node.get("sst_stuck_for_sec", 0),
            })
    return stuck


async def _collect_replication_lag(cluster_id: int) -> list[dict]:
    """
    Return per-node recv_queue_avg from poller state.
    """
    from services.poller import get_cluster_state

    state = get_cluster_state(cluster_id)
    if not state:
        return []

    lag_data = []
    for node in state.get("nodes", []):
        avg = node.get("wsrep_local_recv_queue_avg")
        if avg is not None:
            lag_data.append({
                "node_id": node.get("id"),
                "node_name": node.get("name"),
                "host": node.get("host"),
                "recv_queue_avg": float(avg),
            })
    return lag_data


async def _collect_disk_usage(cluster_id: int) -> list[dict]:
    """
    Return disk usage ratios from poller state.
    """
    from services.poller import get_cluster_state

    state = get_cluster_state(cluster_id)
    if not state:
        return []

    disk_data = []
    for node in state.get("nodes", []):
        disk = node.get("disk")
        if disk and disk.get("total_bytes") and disk["total_bytes"] > 0:
            used = disk.get("used_bytes", 0)
            total = disk["total_bytes"]
            ratio = used / total
            disk_data.append({
                "node_id": node.get("id"),
                "node_name": node.get("name"),
                "host": node.get("host"),
                "used_bytes": used,
                "total_bytes": total,
                "ratio": ratio,
            })
    return disk_data


# ── Rules engine ──────────────────────────────────────────────────────────────

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
        if node_result["error"]:
            continue
        for chk in node_result["checks"]:
            if chk["status"] not in ("error", "warn"):
                continue
            if chk["param"] not in ACTIONABLE_PARAMS:
                continue

            severity = SEVERITY_MAP.get(chk["status"], AdvisorSeverity.warn)
            param = chk["param"]
            node_name = node_result["node_name"]
            node_id = node_result["node_id"]

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
        if node_result["error"] or not node_result["trx_list"]:
            continue

        max_age = max((t.get("trx_age_sec") or 0) for t in node_result["trx_list"])
        count = len(node_result["trx_list"])
        node_name = node_result["node_name"]
        node_id = node_result["node_id"]

        severity = AdvisorSeverity.critical if max_age >= 900 else AdvisorSeverity.warn

        # Top-3 oldest for evidence
        top3 = sorted(node_result["trx_list"], key=lambda t: t.get("trx_age_sec") or 0, reverse=True)[:3]
        evidence_rows = []
        for t in top3:
            evidence_rows.append({
                "trx_id": t.get("trx_id"),
                "thread_id": t.get("trx_mysql_thread_id"),
                "age_sec": t.get("trx_age_sec"),
                "query": (t.get("trx_query") or "")[:120],
            })

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

    LAG_WARN = 0.5
    LAG_CRITICAL = 2.0

    lagging = [n for n in lag_results if n["recv_queue_avg"] >= LAG_WARN]
    if not lagging:
        return cards

    max_lag = max(n["recv_queue_avg"] for n in lagging)
    severity = AdvisorSeverity.critical if max_lag >= LAG_CRITICAL else AdvisorSeverity.warn
    node_names = [n["node_name"] for n in lagging]
    node_ids = [n["node_id"] for n in lagging]

    cards.append(AdvisorCard(
        id="replication-lag",
        severity=severity,
        category=AdvisorCategory.replication,
        source="replication-lag",
        title=f"Replication lag detected on {len(lagging)} node(s)",
        summary=f"wsrep_local_recv_queue_avg={max_lag:.2f} — receiver queue is growing. Consider increasing wsrep_slave_threads.",
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

    WARN_RATIO = 0.80
    CRITICAL_RATIO = 0.90

    for node in disk_results:
        ratio = node["ratio"]
        if ratio < WARN_RATIO:
            continue

        severity = AdvisorSeverity.critical if ratio >= CRITICAL_RATIO else AdvisorSeverity.warn
        used_gb = node["used_bytes"] / (1024 ** 3)
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
                    "used_bytes": node["used_bytes"],
                    "total_bytes": node["total_bytes"],
                    "ratio": round(ratio, 4),
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
    AdvisorSeverity.warn: 1,
    AdvisorSeverity.info: 2,
}


def _sort_and_dedup(cards: list[AdvisorCard]) -> list[AdvisorCard]:
    seen: set[str] = set()
    unique: list[AdvisorCard] = []
    for card in sorted(cards, key=lambda c: _SEVERITY_ORDER.get(c.severity, 99)):
        if card.id not in seen:
            seen.add(card.id)
            unique.append(card)
    return unique


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("", response_model=AdvisorResponse)
async def get_advisor(cluster_id: int):
    """
    Aggregate diagnostic signals for the cluster and return advisor cards.
    Each card has severity (info/warn/critical), evidence, and a recommended action.
    """
    cluster = await asyncio.to_thread(get_cluster_or_404, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Collect all data sources concurrently
    (
        config_results,
        trx_results,
        sst_results,
        lag_results,
        disk_results,
    ) = await asyncio.gather(
        _collect_config_health(cluster_id),
        _collect_active_transactions(cluster_id),
        _collect_sst_status(cluster_id),
        _collect_replication_lag(cluster_id),
        _collect_disk_usage(cluster_id),
        return_exceptions=False,
    )

    # Apply rules
    cards: list[AdvisorCard] = []
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
