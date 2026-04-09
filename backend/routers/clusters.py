"""
Clusters router

GET  /api/clusters                    — список кластеров с live-сводкой
GET  /api/clusters?contour_id=N       — фильтр по контуру
GET  /api/clusters/{cluster_id}/status — полный live-статус кластера

ТЗ разделы 6.1, 7, 9.1, 9.2
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.poller import live_node_states, live_arbitrator_states

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clusters", tags=["clusters"])


# ── DB helpers ────────────────────────────────────────────────────────────────

def _fetch_clusters(contour_id: int | None = None) -> list[dict]:
    sql = """
        SELECT c.id, c.name, c.contour_id, ct.name AS contour_name
        FROM clusters c
        JOIN contours ct ON ct.id = c.contour_id
        {where}
        ORDER BY ct.name, c.name
    """.format(where="WHERE c.contour_id = :contour_id" if contour_id else "")

    params = {"contour_id": contour_id} if contour_id else {}

    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().fetchall()
    return [dict(r) for r in rows]


def _fetch_cluster_by_id(cluster_id: int) -> dict | None:
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                 SELECT c.id, c.name, c.contour_id, ct.name AS contour_name
                 FROM clusters c
                          JOIN contours ct ON ct.id = c.contour_id
                 WHERE c.id = :cluster_id
                 """),
            {"cluster_id": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def _fetch_nodes(cluster_id: int) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                 SELECT
                     n.id, n.name, n.host, n.port,
                     n.ssh_port, n.ssh_user, n.db_user,
                     n.enabled, n.maintenance,
                     n.datacenter_id AS dc_id, 
                     d.name AS dc_name
                 FROM nodes n
                          LEFT JOIN datacenters d ON d.id = n.datacenter_id
                 WHERE n.cluster_id = :cluster_id
                 ORDER BY n.name
                 """),
            {"cluster_id": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _fetch_arbitrators(cluster_id: int) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                 SELECT
                     a.id, a.name, a.host,
                     a.ssh_port, a.ssh_user, a.enabled,
                     a.datacenter_id AS dc_id,
                     d.name AS dc_name
                 FROM arbitrators a
                          LEFT JOIN datacenters d ON d.id = a.datacenter_id
                 WHERE a.cluster_id = :cluster_id
                 ORDER BY a.name
                 """),
            {"cluster_id": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── Live status helpers ───────────────────────────────────────────────────────

def _calc_cluster_status(
        node_states: dict,
        nodes: list[dict],
) -> str:
    """
    ТЗ 7.1:
      healthy  — все enabled-ноды в Primary Component
      critical — split-brain (wsrep_cluster_status != Primary)
      degraded — всё остальное (часть нод недоступна, но не split-brain)
    """
    enabled_nodes = [n for n in nodes if n["enabled"]]
    if not enabled_nodes or not node_states:
        return "degraded"

    # Split-brain: хотя бы одна нода с db_ok видит non-Primary
    for s in node_states.values():
        if s.db_ok and s.wsrep_cluster_status.upper() != "PRIMARY":
            return "critical"

    # Healthy: все enabled-ноды ssh_ok + SYNCED/DONOR/JOINER
    online_ids = {
        node["id"] for node in enabled_nodes
        if node_states.get(node["id"]) and node_states[node["id"]].ssh_ok
    }
    if len(online_ids) == len(enabled_nodes):
        return "healthy"

    return "degraded"


def _build_cluster_live_summary(
        cluster_id: int,
        nodes: list[dict],
) -> dict[str, Any]:
    """Компактная live-сводка для GET /api/clusters (list endpoint)."""
    node_states = live_node_states.get(cluster_id, {})

    if not node_states:
        return {
            "status":        "degraded",
            "has_live_data": False,
            "total_nodes":   len(nodes),
            "online_nodes":  0,
            "synced_nodes":  0,
        }

    online = sum(1 for n in nodes if node_states.get(n["id"]) and node_states[n["id"]].ssh_ok)
    synced = sum(
        1 for n in nodes
        if node_states.get(n["id"])
        and node_states[n["id"]].ssh_ok
        and node_states[n["id"]].wsrep_local_state_comment == "SYNCED"
    )

    return {
        "status":        _calc_cluster_status(node_states, nodes),
        "has_live_data": True,
        "total_nodes":   len(nodes),
        "online_nodes":  online,
        "synced_nodes":  synced,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", dependencies=[Depends(require_auth)])
async def list_clusters(contour_id: int | None = None) -> list[dict]:
    """
    GET /api/clusters
    GET /api/clusters?contour_id=N

    ТЗ 9.1
    """
    clusters = _fetch_clusters(contour_id)
    result = []
    for cluster in clusters:
        nodes = _fetch_nodes(cluster["id"])
        result.append({
            **cluster,
            "live": _build_cluster_live_summary(cluster["id"], nodes),
        })
    return result


@router.get("/{cluster_id}/status", dependencies=[Depends(require_auth)])
async def cluster_status(cluster_id: int) -> dict:
    """
    GET /api/clusters/{cluster_id}/status

    ТЗ 9.2 — полный live-статус: cluster + nodes + arbitrators + active_operation
    """
    cluster = _fetch_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Cluster {cluster_id} not found")

    nodes       = _fetch_nodes(cluster_id)
    arbitrators = _fetch_arbitrators(cluster_id)

    node_states = live_node_states.get(cluster_id, {})
    arb_states  = live_arbitrator_states.get(cluster_id, {})

    # Nodes с live-полями
    nodes_out = []
    for n in nodes:
        live = node_states.get(n["id"])
        nodes_out.append({
            "id":          n["id"],
            "name":        n["name"],
            "host":        n["host"],
            "port":        n["port"],
            "ssh_port":    n["ssh_port"],
            "ssh_user":    n["ssh_user"],
            "db_user":     n["db_user"],
            "enabled":     bool(n["enabled"]),
            "maintenance": bool(n["maintenance"]),
            "dc_id":       n["dc_id"],
            "dc_name":     n["dc_name"],
            "live":        live.to_dict() if live is not None else None,
        })

    # Arbitrators с live-полями
    arbitrators_out = []
    for a in arbitrators:
        live = arb_states.get(a["id"])
        arbitrators_out.append({
            "id":       a["id"],
            "name":     a["name"],
            "host":     a["host"],
            "ssh_port": a["ssh_port"],
            "ssh_user": a["ssh_user"],
            "enabled":  bool(a["enabled"]),
            "dc_id":    a["dc_id"],
            "dc_name":  a["dc_name"],
            "live":     live.to_dict() if live is not None else None,
        })

    # Cluster-level derived fields (ТЗ 9.2 response shape)
    cluster_status_str = _calc_cluster_status(node_states, nodes)
    has_live = bool(node_states)

    online_nodes = sum(1 for n in nodes_out if n["live"] and n["live"].get("ssh_ok"))
    online_arbs  = sum(1 for a in arbitrators_out if a["live"] and a["live"].get("ssh_ok"))

    # wsrep_cluster_size из любой живой ноды
    wsrep_cluster_size = None
    for s in node_states.values():
        if s.db_ok and s.wsrep_cluster_size:
            wsrep_cluster_size = s.wsrep_cluster_size
            break

    # active_operation — ТЗ 9.2
    with engine.begin() as conn:
        op_row = conn.execute(
            text("""
                 SELECT id, type, status, started_at, target_node_id
                 FROM cluster_operations
                 WHERE cluster_id = :cid
                   AND status IN ('pending', 'running', 'cancel_requested')
                 ORDER BY id DESC
                 LIMIT 1
                 """),
            {"cid": cluster_id},
        ).mappings().fetchone()
    active_operation = dict(op_row) if op_row else None

    return {
        "id":                cluster["id"],
        "name":              cluster["name"],
        "contour":           cluster["contour_name"],
        "status":            cluster_status_str,
        "primary":           cluster_status_str != "critical",
        "wsrep_cluster_size": wsrep_cluster_size,
        "online_nodes":      online_nodes,
        "total_nodes":       len(nodes),
        "online_arbitrators": online_arbs,
        "total_arbitrators": len(arbitrators),
        "has_live_data":     has_live,
        "last_update_ts":    None,  # поллер проставит через live state
        "nodes":             nodes_out,
        "arbitrators":       arbitrators_out,
        "active_operation":  active_operation,
    }