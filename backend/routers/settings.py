"""
Settings router — ТЗ раздел 16.

ТЗ 16.1 endpoint map:
  GET    /api/settings/datacenters
  POST   /api/settings/datacenters
  PATCH  /api/settings/datacenters/{dc_id}
  DELETE /api/settings/datacenters/{dc_id}

  GET    /api/settings/clusters
  POST   /api/settings/clusters
  PATCH  /api/settings/clusters/{cluster_id}
  DELETE /api/settings/clusters/{cluster_id}

  GET    /api/settings/nodes?cluster_id=N
  POST   /api/settings/nodes            (body содержит cluster_id)
  PATCH  /api/settings/nodes/{node_id}
  DELETE /api/settings/nodes/{node_id}

  GET    /api/settings/arbitrators?cluster_id=N
  POST   /api/settings/arbitrators      (body содержит cluster_id)
  PATCH  /api/settings/arbitrators/{arb_id}
  DELETE /api/settings/arbitrators/{arb_id}

  GET    /api/settings/system
  PATCH  /api/settings/system
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.crypto import encrypt_password
from services.event_log import write_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(require_auth)],
)


# ════════════════════════════════════════════════════════════════════════════════
# DATACENTERS
# ════════════════════════════════════════════════════════════════════════════════

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
    write_event(level="INFO", source="ui", message=f"Datacenter '{body.name}' created (id={new_id})")
    return {"id": new_id, "name": body.name}


@router.patch("/datacenters/{dc_id}")
async def update_datacenter(dc_id: int, body: DatacenterCreate) -> dict:
    _get_datacenter_or_404(dc_id)
    _assert_datacenter_name_unique(body.name, exclude_id=dc_id)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE datacenters SET name = :name WHERE id = :id"),
            {"name": body.name, "id": dc_id},
        )
    write_event(level="INFO", source="ui", message=f"Datacenter id={dc_id} renamed to '{body.name}'")
    return {"id": dc_id, "name": body.name}


@router.delete("/datacenters/{dc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datacenter(dc_id: int) -> Response:
    _get_datacenter_or_404(dc_id)
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


# ════════════════════════════════════════════════════════════════════════════════
# CLUSTERS
# ════════════════════════════════════════════════════════════════════════════════

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


@router.get("/clusters")
async def list_clusters() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT c.id, c.name, c.contour_id, c.description, ct.name AS contour_name "
                "FROM clusters c "
                "LEFT JOIN contours ct ON ct.id = c.contour_id "
                "ORDER BY c.name"
            )
        ).mappings().fetchall()
    return [dict(r) for r in rows]


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
    write_event(level="INFO", source="ui", message=f"Cluster '{body.name}' created (id={new_id})")
    return {"id": new_id, "name": body.name, "contour_id": body.contour_id}


@router.patch("/clusters/{cluster_id}")
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
    write_event(level="INFO", source="ui", message=f"Cluster id={cluster_id} updated: name='{body.name}'")
    return {"id": cluster_id, "name": body.name, "contour_id": body.contour_id}


@router.delete("/clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(cluster_id: int) -> Response:
    _get_cluster_or_404(cluster_id)
    with engine.connect() as conn:
        usage = conn.execute(
            text(
                "SELECT COUNT(*) FROM nodes WHERE cluster_id = :id "
                "UNION ALL "
                "SELECT COUNT(*) FROM arbitrators WHERE cluster_id = :id"
            ),
            {"id": cluster_id},
        ).fetchall()
    total = sum(r[0] for r in usage)
    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cluster {cluster_id} still has {total} node(s)/arbitrator(s). Remove them first.",
        )
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clusters WHERE id = :id"), {"id": cluster_id})
    write_event(level="INFO", source="ui", message=f"Cluster id={cluster_id} deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


# ════════════════════════════════════════════════════════════════════════════════
# NODES
# ════════════════════════════════════════════════════════════════════════════════

class NodeCreate(BaseModel):
    cluster_id: int
    name: str
    host: str
    port: int = 3306
    ssh_port: int = 22
    ssh_user: str = "root"
    db_user: str | None = None
    db_password: str | None = None
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


class NodeUpdate(BaseModel):
    name: str
    host: str
    port: int = 3306
    ssh_port: int = 22
    ssh_user: str = "root"
    db_user: str | None = None
    db_password: str | None = None
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


@router.get("/nodes")
async def list_nodes_settings(
        cluster_id: int | None = Query(None),
) -> list[dict]:
    query = (
        "SELECT n.id, n.name, n.host, n.port, n.ssh_port, n.ssh_user, "
        "n.db_user, n.enabled, n.maintenance, n.datacenter_id, "
        "d.name AS datacenter_name, n.cluster_id "
        "FROM nodes n "
        "LEFT JOIN datacenters d ON d.id = n.datacenter_id"
    )
    params: dict = {}
    if cluster_id is not None:
        query += " WHERE n.cluster_id = :cid"
        params["cid"] = cluster_id
    query += " ORDER BY n.name"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/nodes", status_code=status.HTTP_201_CREATED)
async def create_node_settings(body: NodeCreate) -> dict:
    _get_cluster_or_404(body.cluster_id)
    _assert_node_host_port_unique(body.cluster_id, body.host, body.port)
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
                "cluster_id":    body.cluster_id,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
            },
        )
        new_id = result.lastrowid

    write_event(
        level="INFO",
        cluster_id=body.cluster_id,
        node_id=new_id,
        source="ui",
        message=f"Node '{body.name}' ({body.host}:{body.port}) created in cluster {body.cluster_id}",
    )
    return {"id": new_id, "name": body.name, "host": body.host, "port": body.port, "cluster_id": body.cluster_id}


@router.patch("/nodes/{node_id}")
async def update_node_settings(node_id: int, body: NodeUpdate) -> dict:
    node = _get_node_or_404_by_id(node_id)
    _assert_node_host_port_unique(node["cluster_id"], body.host, body.port, exclude_id=node_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)

    if body.db_password:
        encrypted_pw = encrypt_password(body.db_password)
    else:
        encrypted_pw = node["db_password"]

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE nodes SET
                                 name          = :name,
                                 host          = :host,
                                 port          = :port,
                                 ssh_port      = :ssh_port,
                                 ssh_user      = :ssh_user,
                                 db_user       = :db_user,
                                 db_password   = :db_password,
                                 datacenter_id = :datacenter_id,
                                 enabled       = :enabled
                WHERE id = :id
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
            },
        )
    write_event(
        level="INFO",
        cluster_id=node["cluster_id"],
        node_id=node_id,
        source="ui",
        message=f"Node '{body.name}' (id={node_id}) updated",
    )
    return {"id": node_id, "name": body.name, "host": body.host, "port": body.port}


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node_settings(node_id: int) -> Response:
    node = _get_node_or_404_by_id(node_id)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM nodes WHERE id = :id"), {"id": node_id})
    write_event(
        level="INFO",
        cluster_id=node["cluster_id"],
        source="ui",
        message=f"Node id={node_id} deleted from cluster {node['cluster_id']}",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_node_or_404_by_id(node_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, name, host, port, ssh_port, ssh_user, db_user, "
                "db_password, cluster_id, datacenter_id, enabled, maintenance "
                "FROM nodes WHERE id = :id"
            ),
            {"id": node_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Node {node_id} not found")
    return dict(row)


def _assert_node_host_port_unique(
        cluster_id: int, host: str, port: int, exclude_id: int | None = None
) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id FROM nodes "
                "WHERE cluster_id = :cid AND host = :host AND port = :port"
            ),
            {"cid": cluster_id, "host": host, "port": port},
        ).fetchone()
    if row and (exclude_id is None or row[0] != exclude_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Node {host}:{port} already exists in this cluster",
        )


# ════════════════════════════════════════════════════════════════════════════════
# ARBITRATORS
# ════════════════════════════════════════════════════════════════════════════════

class ArbitratorCreate(BaseModel):
    cluster_id: int
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


class ArbitratorUpdate(BaseModel):
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


@router.get("/arbitrators")
async def list_arbitrators_settings(
        cluster_id: int | None = Query(None),
) -> list[dict]:
    query = (
        "SELECT a.id, a.name, a.host, a.ssh_port, a.ssh_user, "
        "a.enabled, a.datacenter_id, d.name AS datacenter_name, a.cluster_id "
        "FROM arbitrators a "
        "LEFT JOIN datacenters d ON d.id = a.datacenter_id"
    )
    params: dict = {}
    if cluster_id is not None:
        query += " WHERE a.cluster_id = :cid"
        params["cid"] = cluster_id
    query += " ORDER BY a.name"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/arbitrators", status_code=status.HTTP_201_CREATED)
async def create_arbitrator_settings(body: ArbitratorCreate) -> dict:
    _get_cluster_or_404(body.cluster_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO arbitrators
                    (name, host, ssh_port, ssh_user, cluster_id, datacenter_id, enabled)
                VALUES
                    (:name, :host, :ssh_port, :ssh_user, :cluster_id, :datacenter_id, :enabled)
                """
            ),
            {
                "name":          body.name,
                "host":          body.host,
                "ssh_port":      body.ssh_port,
                "ssh_user":      body.ssh_user,
                "cluster_id":    body.cluster_id,
                "datacenter_id": body.datacenter_id,
                "enabled":       1 if body.enabled else 0,
            },
        )
        new_id = result.lastrowid
    write_event(
        level="INFO",
        cluster_id=body.cluster_id,
        source="ui",
        message=f"Arbitrator '{body.name}' ({body.host}) created in cluster {body.cluster_id}",
    )
    return {"id": new_id, "name": body.name, "host": body.host, "cluster_id": body.cluster_id}


@router.patch("/arbitrators/{arb_id}")
async def update_arbitrator_settings(arb_id: int, body: ArbitratorUpdate) -> dict:
    arb = _get_arbitrator_or_404_by_id(arb_id)
    if body.datacenter_id:
        _get_datacenter_or_404(body.datacenter_id)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE arbitrators SET
                                       name          = :name,
                                       host          = :host,
                                       ssh_port      = :ssh_port,
                                       ssh_user      = :ssh_user,
                                       datacenter_id = :datacenter_id,
                                       enabled       = :enabled
                WHERE id = :id
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
            },
        )
    write_event(
        level="INFO",
        cluster_id=arb["cluster_id"],
        source="ui",
        message=f"Arbitrator id={arb_id} updated",
    )
    return {"id": arb_id, "name": body.name, "host": body.host}


@router.delete("/arbitrators/{arb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_arbitrator_settings(arb_id: int) -> Response:
    arb = _get_arbitrator_or_404_by_id(arb_id)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM arbitrators WHERE id = :id"), {"id": arb_id})
    write_event(
        level="INFO",
        cluster_id=arb["cluster_id"],
        source="ui",
        message=f"Arbitrator id={arb_id} deleted",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_arbitrator_or_404_by_id(arb_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM arbitrators WHERE id = :id"),
            {"id": arb_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Arbitrator {arb_id} not found")
    return dict(row)


# ════════════════════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ════════════════════════════════════════════════════════════════════════════════

class SystemSettingsUpdate(BaseModel):
    polling_interval_sec: int = 5
    event_log_limit: int = 200
    rolling_restart_timeout_sec: Optional[int] = None

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
                "SELECT polling_interval_sec, event_log_limit, "
                "rolling_restart_timeout_sec, updated_at "
                "FROM system_settings WHERE id = 1"
            )
        ).mappings().fetchone()
        if row is None:
            raise HTTPException(500, detail="system_settings row not found — run init_db()")
        return dict(row)


@router.patch("/system")
async def update_system_settings(body: SystemSettingsUpdate) -> dict:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE system_settings SET
                                           polling_interval_sec = :interval,
                                           event_log_limit = :log_limit,
                                           rolling_restart_timeout_sec = :rr_timeout,
                                           updated_at = :now
                WHERE id = 1
                """
            ),
            {
                "interval":   body.polling_interval_sec,
                "log_limit":  body.event_log_limit,
                "rr_timeout": body.rolling_restart_timeout_sec,
                "now":        datetime.now(timezone.utc).isoformat(),
            },
        )
    write_event(level="INFO", source="ui", message="System settings updated")
    return {
        "polling_interval_sec":        body.polling_interval_sec,
        "event_log_limit":             body.event_log_limit,
        "rolling_restart_timeout_sec": body.rolling_restart_timeout_sec,
    }
