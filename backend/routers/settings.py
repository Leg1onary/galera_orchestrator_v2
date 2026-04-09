"""
Settings router — Phase 2

CRUD for: datacenters, clusters, nodes, arbitrators, system_settings.
All entities are cluster-scoped where applicable.
db_password is always Fernet-encrypted before storage.
db_password is NEVER returned in read responses.

Per ТЗ раздел 9.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.crypto import encrypt_password
from services.event_log import write_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(require_auth)],
)


# ═══════════════════════════════════════════════════════════════════════════════
# DATACENTERS
# ═══════════════════════════════════════════════════════════════════════════════

class DatacenterCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


@router.get("/datacenters")
async def list_datacenters() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name FROM datacenters ORDER BY name")
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/datacenters", status_code=status.HTTP_201_CREATED)
async def create_datacenter(body: DatacenterCreate) -> dict:
    _assert_datacenter_name_unique(body.name)
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO datacenters (name) VALUES (:name)"),
            {"name": body.name},
        )
        new_id = result.lastrowid
    write_event(source="ui", message=f"Datacenter '{body.name}' created (id={new_id})")
    return {"id": new_id, "name": body.name}


@router.put("/datacenters/{dc_id}")
async def update_datacenter(dc_id: int, body: DatacenterCreate) -> dict:
    _get_datacenter_or_404(dc_id)
    _assert_datacenter_name_unique(body.name, exclude_id=dc_id)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE datacenters SET name = :name WHERE id = :id"),
            {"name": body.name, "id": dc_id},
        )
    write_event(source="ui", message=f"Datacenter id={dc_id} renamed to '{body.name}'")
    return {"id": dc_id, "name": body.name}


@router.delete("/datacenters/{dc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datacenter(dc_id: int) -> None:
    _get_datacenter_or_404(dc_id)
    # Check for references in nodes/arbitrators
    with engine.connect() as conn:
        usage = conn.execute(
            text(
                "SELECT COUNT(*) FROM nodes WHERE datacenter_id = :id "
                "UNION ALL "
                "SELECT COUNT(*) FROM arbitrators WHERE datacenter_id = :id"
            ),
            {"id": dc_id},
        ).fetchall()
    total = sum(r[0] for r in usage)
    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Datacenter {dc_id} is still referenced by {total} node(s)/arbitrator(s)",
        )
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM datacenters WHERE id = :id"), {"id": dc_id})


def _get_datacenter_or_404(dc_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name FROM datacenters WHERE id = :id"), {"id": dc_id}
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Datacenter {dc_id} not found")
    return dict(row)


def _assert_datacenter_name_unique(name: str, exclude_id: int | None = None) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM datacenters WHERE name = :name"),
            {"name": name},
        ).fetchone()
    if row and (exclude_id is None or row[0] != exclude_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Datacenter with name '{name}' already exists",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTERS
# ═══════════════════════════════════════════════════════════════════════════════

class ClusterCreate(BaseModel):
    name: str
    contour_id: int
    description: str = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


@router.post("/clusters", status_code=status.HTTP_201_CREATED)
async def create_cluster(body: ClusterCreate) -> dict:
    _assert_contour_exists(body.contour_id)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO clusters (name, contour_id, description) "
                "VALUES (:name, :contour_id, :description)"
            ),
            {
                "name":        body.name,
                "contour_id":  body.contour_id,
                "description": body.description,
            },
        )
        new_id = result.lastrowid
    write_event(source="ui", message=f"Cluster '{body.name}' created (id={new_id})")
    return {"id": new_id, "name": body.name, "contour_id": body.contour_id}


@router.put("/clusters/{cluster_id}")
async def update_cluster(cluster_id: int, body: ClusterCreate) -> dict:
    _get_cluster_or_404(cluster_id)
    _assert_contour_exists(body.contour_id)
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE clusters SET name = :name, contour_id = :contour_id, "
                "description = :description WHERE id = :id"
            ),
            {
                "name":        body.name,
                "contour_id":  body.contour_id,
                "description": body.description,
                "id":          cluster_id,
            },
        )
    write_event(source="ui", message=f"Cluster id={cluster_id} updated: name='{body.name}'")
    return {"id": cluster_id, "name": body.name, "contour_id": body.contour_id}


@router.delete("/clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(cluster_id: int) -> None:
    _get_cluster_or_404(cluster_id)
    # CASCADE handles nodes + arbitrators + cluster_operations + event_logs
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clusters WHERE id = :id"), {"id": cluster_id})
    write_event(source="ui", message=f"Cluster id={cluster_id} deleted")


def _get_cluster_or_404(cluster_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, contour_id FROM clusters WHERE id = :id"),
            {"id": cluster_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return dict(row)


def _assert_contour_exists(contour_id: int) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM contours WHERE id = :id"), {"id": contour_id}
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Contour {contour_id} not found",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODES
# ═══════════════════════════════════════════════════════════════════════════════

class NodeCreate(BaseModel):
    name: str
    host: str
    port: int = 3306
    ssh_port: int = 22
    ssh_user: str = "root"
    db_user: str | None = None
    db_password: str | None = None   # plaintext, encrypted before storage
    datacenter_id: int | None = None
    enabled: bool = True

    @field_validator("name", "host")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field cannot be empty")
        return v

    @field_validator("port", "ssh_port")
    @classmethod
    def valid_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("port must be 1–65535")
        return v


class NodeUpdate(NodeCreate):
    pass


@router.get("/clusters/{cluster_id}/nodes")
async def list_nodes(cluster_id: int) -> list[dict]:
    """List all nodes for a cluster (config only, no live data, no db_password)."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT n.id, n.name, n.host, n.port, n.ssh_port, n.ssh_user,
                       n.db_user, n.enabled, n.maintenance, n.datacenter_id,
                       d.name AS datacenter_name
                FROM nodes n
                         LEFT JOIN datacenters d ON d.id = n.datacenter_id
                WHERE n.cluster_id = :cid
                ORDER BY n.name
                """
            ),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/clusters/{cluster_id}/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(cluster_id: int, body: NodeCreate) -> dict:
    _get_cluster_or_404(cluster_id)
    _assert_node_host_port_unique(cluster_id, body.host, body.port)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)

    encrypted_pw = encrypt_password(body.db_password) if body.db_password else None

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO nodes
                (name, host, port, ssh_port, ssh_user, db_user, db_password,
                 cluster_id, datacenter_id, enabled, maintenance)
                VALUES
                    (:name, :host, :port, :ssh_port, :ssh_user, :db_user, :db_password,
                     :cluster_id, :datacenter_id, :enabled, 0)
                """
            ),
            {
                "name":          body.name,
                "host":          body.host,
                "port":          body.port,
                "ssh_port":      body.ssh_port,
                "ssh_user":      body.ssh_user,
                "db_user":       body.db_user,
                "db_password":   encrypted_pw,
                "cluster_id":    cluster_id,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
            },
        )
        new_id = result.lastrowid

    write_event(
        cluster_id=cluster_id,
        node_id=new_id,
        source="ui",
        message=f"Node '{body.name}' ({body.host}:{body.port}) created in cluster {cluster_id}",
    )
    return {"id": new_id, "name": body.name, "host": body.host, "port": body.port}


@router.put("/clusters/{cluster_id}/nodes/{node_id}")
async def update_node(cluster_id: int, node_id: int, body: NodeUpdate) -> dict:
    node = _get_node_or_404(cluster_id, node_id)
    _assert_node_host_port_unique(cluster_id, body.host, body.port, exclude_id=node_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)

    # Only re-encrypt if password was explicitly provided in the request
    if body.db_password is not None:
        encrypted_pw = encrypt_password(body.db_password) if body.db_password else None
    else:
        encrypted_pw = node["db_password"]  # keep existing encrypted value

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE nodes SET
                                 name=:name, host=:host, port=:port, ssh_port=:ssh_port,
                                 ssh_user=:ssh_user, db_user=:db_user, db_password=:db_password,
                                 datacenter_id=:datacenter_id, enabled=:enabled
                WHERE id=:id AND cluster_id=:cluster_id
                """
            ),
            {
                "name":          body.name,
                "host":          body.host,
                "port":          body.port,
                "ssh_port":      body.ssh_port,
                "ssh_user":      body.ssh_user,
                "db_user":       body.db_user,
                "db_password":   encrypted_pw,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
                "id":            node_id,
                "cluster_id":    cluster_id,
            },
        )
    write_event(
        cluster_id=cluster_id, node_id=node_id, source="ui",
        message=f"Node '{body.name}' (id={node_id}) updated",
    )
    return {"id": node_id, "name": body.name, "host": body.host, "port": body.port}


@router.delete("/clusters/{cluster_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(cluster_id: int, node_id: int) -> None:
    _get_node_or_404(cluster_id, node_id)
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM nodes WHERE id=:id AND cluster_id=:cid"),
            {"id": node_id, "cid": cluster_id},
        )
    write_event(
        cluster_id=cluster_id, node_id=None, source="ui",
        message=f"Node id={node_id} deleted from cluster {cluster_id}",
    )


def _get_node_or_404(cluster_id: int, node_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM nodes WHERE id=:id AND cluster_id=:cid"),
            {"id": node_id, "cid": cluster_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Node {node_id} not found in cluster {cluster_id}")
    return dict(row)


def _assert_node_host_port_unique(
        cluster_id: int, host: str, port: int, exclude_id: int | None = None
) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id FROM nodes WHERE cluster_id=:cid AND host=:host AND port=:port"
            ),
            {"cid": cluster_id, "host": host, "port": port},
        ).fetchone()
    if row and (exclude_id is None or row[0] != exclude_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Node with host:port {host}:{port} already exists in this cluster",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ARBITRATORS
# ═══════════════════════════════════════════════════════════════════════════════

class ArbitratorCreate(BaseModel):
    name: str
    host: str
    ssh_port: int = 22
    ssh_user: str = "root"
    datacenter_id: int | None = None
    enabled: bool = True

    @field_validator("name", "host")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field cannot be empty")
        return v


@router.get("/clusters/{cluster_id}/arbitrators")
async def list_arbitrators(cluster_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT a.id, a.name, a.host, a.ssh_port, a.ssh_user,
                       a.enabled, a.datacenter_id, d.name AS datacenter_name
                FROM arbitrators a
                         LEFT JOIN datacenters d ON d.id = a.datacenter_id
                WHERE a.cluster_id=:cid ORDER BY a.name
                """
            ),
            {"cid": cluster_id},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/clusters/{cluster_id}/arbitrators", status_code=status.HTTP_201_CREATED)
async def create_arbitrator(cluster_id: int, body: ArbitratorCreate) -> dict:
    _get_cluster_or_404(cluster_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO arbitrators
                    (name, host, ssh_port, ssh_user, cluster_id, datacenter_id, enabled)
                VALUES (:name, :host, :ssh_port, :ssh_user, :cluster_id, :datacenter_id, :enabled)
                """
            ),
            {
                "name":          body.name,
                "host":          body.host,
                "ssh_port":      body.ssh_port,
                "ssh_user":      body.ssh_user,
                "cluster_id":    cluster_id,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
            },
        )
        new_id = result.lastrowid
    write_event(
        cluster_id=cluster_id, source="ui",
        message=f"Arbitrator '{body.name}' ({body.host}) created in cluster {cluster_id}",
    )
    return {"id": new_id, "name": body.name, "host": body.host}


@router.put("/clusters/{cluster_id}/arbitrators/{arb_id}")
async def update_arbitrator(cluster_id: int, arb_id: int, body: ArbitratorCreate) -> dict:
    _get_arbitrator_or_404(cluster_id, arb_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE arbitrators SET
                                       name=:name, host=:host, ssh_port=:ssh_port, ssh_user=:ssh_user,
                                       datacenter_id=:datacenter_id, enabled=:enabled
                WHERE id=:id AND cluster_id=:cid
                """
            ),
            {
                "name":          body.name,
                "host":          body.host,
                "ssh_port":      body.ssh_port,
                "ssh_user":      body.ssh_user,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
                "id":            arb_id,
                "cid":           cluster_id,
            },
        )
    write_event(
        cluster_id=cluster_id, source="ui",
        message=f"Arbitrator id={arb_id} updated",
    )
    return {"id": arb_id, "name": body.name, "host": body.host}


@router.delete("/clusters/{cluster_id}/arbitrators/{arb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_arbitrator(cluster_id: int, arb_id: int) -> None:
    _get_arbitrator_or_404(cluster_id, arb_id)
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM arbitrators WHERE id=:id AND cluster_id=:cid"),
            {"id": arb_id, "cid": cluster_id},
        )
    write_event(
        cluster_id=cluster_id, source="ui",
        message=f"Arbitrator id={arb_id} deleted from cluster {cluster_id}",
    )


def _get_arbitrator_or_404(cluster_id: int, arb_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM arbitrators WHERE id=:id AND cluster_id=:cid"),
            {"id": arb_id, "cid": cluster_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Arbitrator {arb_id} not found in cluster {cluster_id}")
    return dict(row)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class SystemSettingsUpdate(BaseModel):
    polling_interval_sec: int = 5
    event_log_limit: int = 200
    timezone: str = "UTC"

    @field_validator("polling_interval_sec")
    @classmethod
    def valid_interval(cls, v: int) -> int:
        if not (1 <= v <= 300):
            raise ValueError("polling_interval_sec must be 1–300 seconds")
        return v

    @field_validator("event_log_limit")
    @classmethod
    def valid_limit(cls, v: int) -> int:
        if not (10 <= v <= 10000):
            raise ValueError("event_log_limit must be 10–10000")
        return v


@router.get("/system")
async def get_system_settings() -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT polling_interval_sec, event_log_limit, timezone, updated_at "
                "FROM system_settings WHERE id = 1"
            )
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(500, detail="system_settings row not found — run init_db()")
    return dict(row)


@router.put("/system")
async def update_system_settings(body: SystemSettingsUpdate) -> dict:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE system_settings SET
                                           polling_interval_sec = :interval,
                                           event_log_limit      = :log_limit,
                                           timezone             = :tz,
                                           updated_at           = :now
                WHERE id = 1
                """
            ),
            {
                "interval":  body.polling_interval_sec,
                "log_limit": body.event_log_limit,
                "tz":        body.timezone,
                "now":       datetime.now(timezone.utc).isoformat(),
            },
        )
    write_event(source="ui", message="System settings updated")
    return {
        "polling_interval_sec": body.polling_interval_sec,
        "event_log_limit":      body.event_log_limit,
        "timezone":             body.timezone,
    }