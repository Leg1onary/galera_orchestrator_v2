from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)

metadata = MetaData()

# ---------------------------------------------------------------------------
# contours
# ---------------------------------------------------------------------------
contours = Table(
    "contours",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False, unique=True),
)

# ---------------------------------------------------------------------------
# datacenters
# ---------------------------------------------------------------------------
datacenters = Table(
    "datacenters",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False, unique=True),
)

# ---------------------------------------------------------------------------
# clusters
# ---------------------------------------------------------------------------
clusters = Table(
    "clusters",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column(
        "contour_id",
        Integer,
        ForeignKey("contours.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("description", Text, nullable=False, server_default="''"),
)

# ---------------------------------------------------------------------------
# nodes
# db_password stored encrypted (Fernet). Encryption handled in services/crypto.py
# ---------------------------------------------------------------------------
nodes = Table(
    "nodes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("host", Text, nullable=False),
    Column("port", Integer, nullable=False, server_default="3306"),
    Column("ssh_port", Integer, nullable=False, server_default="22"),
    Column("ssh_user", Text, nullable=False, server_default="root"),
    Column("db_user", Text, nullable=True),
    Column("db_password", Text, nullable=True),
    Column(
        "cluster_id",
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "datacenter_id",
        Integer,
        ForeignKey("datacenters.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("maintenance", Boolean, nullable=False, server_default="0"),
    Column("enabled", Boolean, nullable=False, server_default="1"),
)

# ---------------------------------------------------------------------------
# arbitrators
# ---------------------------------------------------------------------------
arbitrators = Table(
    "arbitrators",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("host", Text, nullable=False),
    Column("ssh_port", Integer, nullable=False, server_default="22"),
    Column("ssh_user", Text, nullable=False, server_default="root"),
    Column(
        "cluster_id",
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "datacenter_id",
        Integer,
        ForeignKey("datacenters.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("enabled", Boolean, nullable=False, server_default="1"),
)

# ---------------------------------------------------------------------------
# cluster_operations
# ---------------------------------------------------------------------------
cluster_operations = Table(
    "cluster_operations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "cluster_id",
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("started_at", DateTime, nullable=True),
    Column("finished_at", DateTime, nullable=True),
    Column("created_by", Text, nullable=True),
    Column(
        "target_node_id",
        Integer,
        ForeignKey("nodes.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("details_json", Text, nullable=True),
    Column("error_message", Text, nullable=True),
)

# ---------------------------------------------------------------------------
# event_logs
# ---------------------------------------------------------------------------
event_logs = Table(
    "event_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "ts",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("level", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("message", Text, nullable=False),
    Column(
        "node_id",
        Integer,
        ForeignKey("nodes.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "arbitrator_id",
        Integer,
        ForeignKey("arbitrators.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "cluster_id",
        Integer,
        ForeignKey("clusters.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "operation_id",
        Integer,
        ForeignKey("cluster_operations.id", ondelete="SET NULL"),
        nullable=True,
    ),
)

# ---------------------------------------------------------------------------
# system_settings
# Single-row table. Always query WHERE id=1.
# ---------------------------------------------------------------------------
system_settings = Table(
    "system_settings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("polling_interval_sec", Integer, nullable=False, server_default="5"),
    Column("event_log_limit", Integer, nullable=False, server_default="200"),
    Column("rolling_restart_timeout_sec", Integer, nullable=False, server_default="300"),
    Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)
