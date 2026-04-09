"""
Clusters router — Phase 1

GET /api/clusters
    List all clusters from SQLite with live summary from poller.

GET /api/clusters/{cluster_id}/status
    Full live state for all nodes and arbitrators of a cluster.

Per ТЗ раздел 6.1 and 7: cluster-scoped, real data only.
No mock data, no stubs.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.poller import live_node_states, live_arbitrator_states

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/clusters", tags=["clusters"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_clusters() -> list[dict]:
    """Load all clusters with their contour + datacenter info."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    c.id,
                    c.name,
                    c.description,
                    c.contour_id,
                    ct.name   AS contour_name,
                    c.created_at
                FROM clusters c
                         JOIN contours ct ON ct.id = c.contour_id
                ORDER BY ct.name, c.name
                """
            )
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _fetch_cluster_by_id(cluster_id: int) -> dict | None:
    """Load a single cluster row. Returns None if not found."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    c.id,
                    c.name,
                    c.description,
                    c.contour_id,
                    ct.name AS contour_name,
                    c.created_at
                FROM clusters c
                         JOIN contours ct ON ct.id = c.contour_id
                WHERE c.id = :cluster_id
                """
            ),
            {"cluster_id": cluster_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def _fetch_nodes_for_cluster(cluster_id: int) -> list[dict]:
    """Load all nodes for a cluster (enabled and disabled)."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    n.id,
                    n.name,
                    n.host,
                    n.port,
                    n.ssh_port,
                    n.ssh_user,
                    n.db_user,
                    n.enabled,
                    n.maintenance,
                    n.datacenter_id,
                    d.name AS datacenter_name
                FROM nodes n
                         LEFT JOIN datacenters d ON d.id = n.datacenter_id
                WHERE n.cluster_id = :cluster_id
                ORDER BY n.name
                """
            ),
            {"cluster_id": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _fetch_arbitrators_for_cluster(cluster_id: int) -> list[dict]:
    """Load all arbitrators for a cluster."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    a.id,
                    a.name,
                    a.host,
                    a.ssh_port,
                    a.ssh_user,
                    a.enabled,
                    a.datacenter_id,
                    d.name AS datacenter_name
                FROM arbitrators a
                         LEFT JOIN datacenters d ON d.id = a.datacenter_id
                WHERE a.cluster_id = :cluster_id
                ORDER BY a.name
                """
            ),
            {"cluster_id": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


def _derive_cluster_live_summary(
        cluster_id: int,
        nodes: list[dict],
) -> dict[str, Any]:
    """
    Derive a compact live summary for the cluster list endpoint.

    Returns fields:
      - total_nodes: int
      - nodes_synced: int     — ssh_ok=True AND wsrep_local_state_comment=SYNCED
      - nodes_online: int     — ssh_ok=True
      - nodes_offline: int    — ssh_ok=False
      - cluster_status: str   — PRIMARY / NON-PRIMARY / UNKNOWN
      - has_live_data: bool   — False if poller hasn't run yet
    """
    node_states = live_node_states.get(cluster_id, {})

    if not node_states:
        return {
            "total_nodes":   len(nodes),
            "nodes_synced":  0,
            "nodes_online":  0,
            "nodes_offline": 0,
            "cluster_status": "UNKNOWN",
            "has_live_data": False,
        }

    synced = 0
    online = 0
    offline = 0
    cluster_status = "UNKNOWN"

    for node in nodes:
        state = node_states.get(node["id"])
        if state is None:
            offline += 1
            continue
        if state.ssh_ok:
            online += 1
            if state.wsrep_local_state_comment == "SYNCED":
                synced += 1
            # Use wsrep_cluster_status from any responding node
            if cluster_status == "UNKNOWN" and state.db_ok:
                cluster_status = state.wsrep_cluster_status
        else:
            offline += 1

    return {
        "total_nodes":    len(nodes),
        "nodes_synced":   synced,
        "nodes_online":   online,
        "nodes_offline":  offline,
        "cluster_status": cluster_status,
        "has_live_data":  True,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", dependencies=[Depends(require_auth)])
async def list_clusters() -> list[dict]:
    """
    GET /api/clusters

    Return all clusters enriched with a live summary snapshot.
    If the poller hasn't completed its first cycle yet for a cluster,
    has_live_data=False and node counts are zeroed.

    Per ТЗ раздел 6.1.
    """
    clusters = _fetch_clusters()

    result = []
    for cluster in clusters:
        cid = cluster["id"]
        nodes = _fetch_nodes_for_cluster(cid)
        live_summary = _derive_cluster_live_summary(cid, nodes)
        result.append({**cluster, "live": live_summary})

    return result


@router.get("/{cluster_id}/status", dependencies=[Depends(require_auth)])
async def cluster_status(cluster_id: int) -> dict:
    """
    GET /api/clusters/{cluster_id}/status

    Full live state for all nodes and arbitrators of the cluster.
    Node live fields come from live_node_states (populated by Poller).
    If the poller hasn't polled a node yet, its live field is null.

    Per ТЗ раздел 7.
    """
    cluster = _fetch_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )

    nodes = _fetch_nodes_for_cluster(cluster_id)
    arbitrators = _fetch_arbitrators_for_cluster(cluster_id)

    node_states = live_node_states.get(cluster_id, {})
    arb_states = live_arbitrator_states.get(cluster_id, {})

    # Build node list with live state merged in
    nodes_out = []
    for node in nodes:
        nid = node["id"]
        live = node_states.get(nid)
        nodes_out.append({
            # Static config fields (no db_password — never expose)
            "id":             node["id"],
            "name":           node["name"],
            "host":           node["host"],
            "port":           node["port"],
            "ssh_port":       node["ssh_port"],
            "ssh_user":       node["ssh_user"],
            "db_user":        node["db_user"],
            "enabled":        bool(node["enabled"]),
            "maintenance":    bool(node["maintenance"]),
            "datacenter_id":  node["datacenter_id"],
            "datacenter_name": node["datacenter_name"],
            # Live state — null until poller has run
            "live":           live.to_dict() if live is not None else None,
        })

    # Build arbitrator list with live state merged in
    arbitrators_out = []
    for arb in arbitrators:
        aid = arb["id"]
        live = arb_states.get(aid)
        arbitrators_out.append({
            "id":             arb["id"],
            "name":           arb["name"],
            "host":           arb["host"],
            "ssh_port":       arb["ssh_port"],
            "ssh_user":       arb["ssh_user"],
            "enabled":        bool(arb["enabled"]),
            "datacenter_id":  arb["datacenter_id"],
            "datacenter_name": arb["datacenter_name"],
            "live":           live.to_dict() if live is not None else None,
        })

    # Cluster-level derived status
    has_live = bool(node_states)
    primary_count = sum(
        1 for s in node_states.values()
        if s.db_ok and s.wsrep_cluster_status == "PRIMARY"
    )
    cluster_status_str = (
        "PRIMARY" if primary_count > 0 else
        "NON-PRIMARY" if has_live else
        "UNKNOWN"
    )

    return {
        "cluster":      cluster,
        "cluster_status": cluster_status_str,
        "has_live_data": has_live,
        "nodes":        nodes_out,
        "arbitrators":  arbitrators_out,
    }