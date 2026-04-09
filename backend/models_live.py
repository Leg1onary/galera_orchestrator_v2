"""
Live node/arbitrator state models — in-memory only, not persisted to SQLite.

Per ТЗ раздел 7.2: live fields populated by Poller from SSH + DB.
Per ТЗ раздел 7.4: arbitrator live fields.

These are dataclasses, not SQLAlchemy tables.
"""

from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
from typing import Deque


# ── Node live state ───────────────────────────────────────────────────────────

@dataclass
class LiveNodeState:
    """
    Live state of a single Galera node.
    Populated by Poller._poll_node() on every polling cycle.

    Per ТЗ раздел 7.2: exactly these fields.
    """

    # ── wsrep fields (from SHOW GLOBAL STATUS) ────────────────────────────────
    wsrep_cluster_status: str = "NON-PRIMARY"   # PRIMARY / NON-PRIMARY
    wsrep_cluster_size: int = 0
    wsrep_connected: str = "OFF"                # ON / OFF
    wsrep_ready: str = "OFF"                    # ON / OFF
    wsrep_local_state_comment: str = "OFFLINE"  # SYNCED / DONOR / JOINER / DESYNCED / OFFLINE
    wsrep_local_recv_queue: int = 0
    wsrep_local_send_queue: int = 0
    wsrep_flow_control_paused: float = 0.0      # 0.0 – 1.0

    # ── Extra live fields ─────────────────────────────────────────────────────
    readonly: bool = False          # SHOW GLOBAL VARIABLES LIKE 'read_only'
    maintenance_drift: bool = False # node.maintenance=True AND readonly=False in DB

    # ── Connection health ─────────────────────────────────────────────────────
    ssh_ok: bool = False
    db_ok: bool = False
    ssh_latency_ms: float | None = None
    db_latency_ms: float | None = None
    error: str | None = None        # Last error message if ssh_ok=False or db_ok=False

    # ── Timestamp ─────────────────────────────────────────────────────────────
    last_check_ts: datetime | None = None

    # ── Ring buffers for sparklines (30 points, not serialised to WS payload) ─
    # Per ТЗ раздел 8: backend keeps 30 points for frontend sparklines.
    flow_control_history: Deque[float] = field(
        default_factory=lambda: deque(maxlen=30)
    )
    recv_queue_history: Deque[int] = field(
        default_factory=lambda: deque(maxlen=30)
    )

    def to_dict(self) -> dict:
        """
        Serialise to a dict for WebSocket broadcast and API status responses.
        Ring buffers are included as lists for sparkline rendering.
        """
        return {
            "wsrep_cluster_status":      self.wsrep_cluster_status,
            "wsrep_cluster_size":        self.wsrep_cluster_size,
            "wsrep_connected":           self.wsrep_connected,
            "wsrep_ready":               self.wsrep_ready,
            "wsrep_local_state_comment": self.wsrep_local_state_comment,
            "wsrep_local_recv_queue":    self.wsrep_local_recv_queue,
            "wsrep_local_send_queue":    self.wsrep_local_send_queue,
            "wsrep_flow_control_paused": self.wsrep_flow_control_paused,
            "readonly":                  self.readonly,
            "maintenance_drift":         self.maintenance_drift,
            "ssh_ok":                    self.ssh_ok,
            "db_ok":                     self.db_ok,
            "ssh_latency_ms":            self.ssh_latency_ms,
            "db_latency_ms":             self.db_latency_ms,
            "error":                     self.error,
            "last_check_ts":             self.last_check_ts.isoformat() if self.last_check_ts else None,
            "flow_control_history":      list(self.flow_control_history),
            "recv_queue_history":        list(self.recv_queue_history),
        }

    def node_status_color(self) -> str:
        """
        Per ТЗ раздел 7.3: derive display colour from state.
        """
        if not self.ssh_ok:
            return "#ef4444"  # OFFLINE
        if self.wsrep_ready == "OFF":
            return "#f97316"  # wsrep not ready (degraded)
        if self.wsrep_local_state_comment == "SYNCED" and self.readonly:
            return "#eab308"  # SYNCED read-only
        if self.wsrep_local_state_comment == "SYNCED":
            return "#22c55e"  # SYNCED
        if self.wsrep_local_state_comment in ("DONOR", "JOINER", "DESYNCED"):
            return "#38bdf8"  # syncing
        return "#ef4444"      # OFFLINE fallback


# ── Arbitrator live state ─────────────────────────────────────────────────────

@dataclass
class LiveArbitratorState:
    """
    Live state of a garbd arbitrator.
    Per ТЗ раздел 7.4.
    """
    ssh_ok: bool = False
    garbd_running: bool = False
    ssh_latency_ms: float | None = None
    last_check_ts: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        state = "online" if (self.ssh_ok and self.garbd_running) else \
            "degraded" if (self.ssh_ok and not self.garbd_running) else \
                "offline"
        return {
            "ssh_ok":         self.ssh_ok,
            "garbd_running":  self.garbd_running,
            "ssh_latency_ms": self.ssh_latency_ms,
            "last_check_ts":  self.last_check_ts.isoformat() if self.last_check_ts else None,
            "state":          state,
            "error":          self.error,
        }