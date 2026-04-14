"""
Poller — asyncio background task for real-time node status collection.

Per ТЗ раздел 8:
  - Interval from system_settings.polling_interval_sec (default 5s)
  - Reads interval from DB on every cycle (picks up Settings changes live)
  - enabled=False nodes are skipped entirely
  - Ring buffer 30 points for flow_control and recv_queue (sparklines)
  - Emits node_state_changed via ws_manager on state change

Per ТЗ раздел 15.11:
  - SSH connect timeout: 5s
  - DB connect timeout: 3s

Lifecycle:
  start_poller() → called from main.py lifespan on startup
  stop_poller()  → called from main.py lifespan on shutdown

Fix (2026-04-09):
  - interval_sec is fetched BEFORE the poll attempt; errors in
    _poll_all_clusters do NOT affect the sleep duration.
  - _get_polling_interval failures fall back to DEFAULT_POLL_INTERVAL.
  - ssh_client.close() always reached via shared DB finally block.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from database import engine
from models_live import LiveArbitratorState, LiveNodeState
from services.ssh_client import SSHClient, SSHError
from services.db_client import DBClient, DBError
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

# Fallback when system_settings row is missing or unreadable
DEFAULT_POLL_INTERVAL = 5

# ── Global live state stores ─────────────────────────────────────────────────────
# Accessed by GET /api/clusters/{id}/status without locking —
# Python GIL makes dict reads safe for our single-worker use case.
# Keys: cluster_id → node_id → LiveNodeState
live_node_states: dict[int, dict[int, LiveNodeState]] = {}

# Keys: cluster_id → arbitrator_id → LiveArbitratorState
live_arbitrator_states: dict[int, dict[int, LiveArbitratorState]] = {}

# ── Poller task handle ───────────────────────────────────────────────────────────
_poller_task: asyncio.Task | None = None

# ── wsrep STATUS variables to fetch per ТЗ раздел 7.2 ──────────────────────
_WSREP_STATUS_VARS = (
    "wsrep_cluster_status",
    "wsrep_cluster_size",
    "wsrep_connected",
    "wsrep_ready",
    "wsrep_local_state_comment",
    "wsrep_local_recv_queue",
    "wsrep_local_send_queue",
    "wsrep_flow_control_paused",
    "wsrep_flow_control_sent",
    "wsrep_incoming_addresses",
)

_WSREP_IN_CLAUSE = ", ".join(f"'{v}'" for v in _WSREP_STATUS_VARS)


# ── Public lifecycle API ────────────────────────────────────────────────────────────

def start_poller() -> None:
    """
    Schedule the polling loop as an asyncio background task.
    Called from main.py lifespan on startup.
    """
    global _poller_task
    if _poller_task is not None and not _poller_task.done():
        logger.warning("Poller already running — ignoring start_poller() call")
        return
    _poller_task = asyncio.create_task(_poll_loop(), name="poller")
    logger.info("Poller task started")


def stop_poller() -> None:
    """
    Cancel the polling loop task.
    Called from main.py lifespan on shutdown.
    """
    global _poller_task
    if _poller_task is not None and not _poller_task.done():
        _poller_task.cancel()
        logger.info("Poller task cancelled")
    _poller_task = None


# ── Public one-shot poll ──────────────────────────────────────────────────────────

async def poll_single_node(cluster_id: int, node: dict) -> None:
    """
    Immediately poll one node outside the regular poll cycle and emit
    node_state_changed via WebSocket if state has changed.

    Called by node_action worker after async operations complete
    (stop / start / restart / rejoin-force) so the frontend receives
    the updated state without waiting for the next poller tick.

    Per ТЗ п.5.2 — бэкенд должен эмитить node_state_changed после
    завершения любой операции, влияющей на состояние ноды.
    """
    await _poll_node(cluster_id, node)


# ── Main polling loop ─────────────────────────────────────────────────────────────

async def _poll_loop() -> None:
    """Infinite loop: poll all clusters, sleep interval, repeat.

    Design invariant:
      interval_sec is always resolved BEFORE the poll attempt.
      Errors during polling do NOT affect the sleep duration — the
      configured interval is preserved so settings changes are respected
      even in a degraded environment.
    """
    logger.info("Polling loop started")
    while True:
        # ── 1. Resolve interval (isolated try — fallback only on DB read failure)
        try:
            interval_sec = await asyncio.to_thread(_get_polling_interval)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            interval_sec = DEFAULT_POLL_INTERVAL
            logger.warning(
                "Could not read polling_interval_sec from DB (%s) — using %ds fallback",
                exc, DEFAULT_POLL_INTERVAL,
            )

        # ── 2. Poll (errors logged, do NOT override interval_sec)
        try:
            await _poll_all_clusters()
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled — shutting down")
            raise
        except Exception as exc:
            logger.exception("Unhandled error in poll cycle: %s", exc)

        # ── 3. Sleep for the configured interval
        await asyncio.sleep(interval_sec)


def _get_polling_interval() -> int:
    """Read polling_interval_sec from system_settings synchronously."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT polling_interval_sec FROM system_settings LIMIT 1")
        ).fetchone()
    return int(row[0]) if row else DEFAULT_POLL_INTERVAL


# ── Cluster-level dispatch ──────────────────────────────────────────────────────────

async def _poll_all_clusters() -> None:
    nodes_by_cluster, arbitrators_by_cluster = await asyncio.to_thread(_load_all_targets)

    cluster_ids = set(nodes_by_cluster) | set(arbitrators_by_cluster)
    if not cluster_ids:
        return

    # FIX MINOR: удаляем stale кластеры из live state
    for stale_cid in list(live_node_states.keys()):
        if stale_cid not in cluster_ids:
            del live_node_states[stale_cid]
    for stale_cid in list(live_arbitrator_states.keys()):
        if stale_cid not in cluster_ids:
            del live_arbitrator_states[stale_cid]

    # удаляем stale ноды внутри кластера
    for cid, node_states in live_node_states.items():
        active_node_ids = {n["id"] for n in nodes_by_cluster.get(cid, [])}
        for stale_nid in list(node_states.keys()):
            if stale_nid not in active_node_ids:
                del node_states[stale_nid]

    await asyncio.gather(
        *[
            _poll_cluster(
                cluster_id,
                nodes_by_cluster.get(cluster_id, []),
                arbitrators_by_cluster.get(cluster_id, []),
            )
            for cluster_id in cluster_ids
        ],
        return_exceptions=True,
    )


def _load_all_targets() -> tuple[dict[int, list[dict]], dict[int, list[dict]]]:
    """Load all enabled nodes and arbitrators from SQLite."""
    nodes_by_cluster: dict[int, list[dict]] = {}
    arbitrators_by_cluster: dict[int, list[dict]] = {}

    with engine.connect() as conn:
        node_rows = conn.execute(
            text(
                """
                SELECT id, name, host, port, ssh_port, ssh_user,
                       db_user, db_password, cluster_id, maintenance
                FROM nodes
                WHERE enabled = 1
                """
            )
        ).mappings().fetchall()

        arb_rows = conn.execute(
            text(
                """
                SELECT id, name, host, ssh_port, ssh_user, cluster_id
                FROM arbitrators
                WHERE enabled = 1
                """
            )
        ).mappings().fetchall()

    for row in node_rows:
        cid = row["cluster_id"]
        nodes_by_cluster.setdefault(cid, []).append(dict(row))

    for row in arb_rows:
        cid = row["cluster_id"]
        arbitrators_by_cluster.setdefault(cid, []).append(dict(row))

    return nodes_by_cluster, arbitrators_by_cluster


async def _poll_cluster(
        cluster_id: int,
        nodes: list[dict],
        arbitrators: list[dict],
) -> None:
    tasks = (
            [_poll_node(cluster_id, node) for node in nodes]
            + [_poll_arbitrator(cluster_id, arb) for arb in arbitrators]
    )
    if not tasks:
        return
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
            logger.warning("Poll task error in cluster %d: %s", cluster_id, r)


# ── Node polling ────────────────────────────────────────────────────────────────

async def _poll_node(cluster_id: int, node: dict) -> None:
    """
    Poll a single node: SSH check → DB status → update live state → broadcast.
    Runs the blocking I/O in a thread pool via asyncio.to_thread().
    """
    node_id = node["id"]

    # Ensure slot exists
    live_node_states.setdefault(cluster_id, {})
    if node_id not in live_node_states[cluster_id]:
        live_node_states[cluster_id][node_id] = LiveNodeState()

    previous = live_node_states[cluster_id][node_id]
    prev_state_comment = previous.wsrep_local_state_comment
    prev_ssh_ok = previous.ssh_ok

    new_state = await asyncio.to_thread(_collect_node_state, node, previous)
    live_node_states[cluster_id][node_id] = new_state

    # ── Change detection → WS broadcast + event log ──────────────────────────────
    state_changed = (
            new_state.wsrep_local_state_comment != prev_state_comment
            or new_state.ssh_ok != prev_ssh_ok
    )

    if state_changed:
        await _broadcast_node_state_changed(cluster_id, node_id, node["name"], new_state)
        await asyncio.to_thread(
            _write_event_log,
            cluster_id=cluster_id,
            node_id=node_id,
            source="ssh" if not new_state.ssh_ok else "system",
            message=(
                    f"Node '{node['name']}' state changed: "
                    f"{prev_state_comment} → {new_state.wsrep_local_state_comment}"
                    + (f" (SSH: {prev_ssh_ok} → {new_state.ssh_ok})" if prev_ssh_ok != new_state.ssh_ok else "")
            ),
        )


def _collect_node_state(node: dict, previous: LiveNodeState) -> LiveNodeState:
    """
    Blocking: open SSH + DB connections, collect all live fields.
    Returns a fully populated LiveNodeState.

    Strategy:
      1. SSH connect → ssh_ok, ssh_latency_ms
      2. If SSH failed → db_ok=False, fill wsrep defaults, return early
      3. DB connect → db_ok, db_latency_ms
      4. SHOW GLOBAL STATUS WHERE Variable_name IN (...)
      5. SHOW GLOBAL VARIABLES LIKE 'read_only'
      6. SHOW GLOBAL VARIABLES LIKE 'wsrep_desync'
      7. maintenance_drift check
      8. Append to ring buffers (carry over from previous state)

    Resource safety:
      ssh_client is closed in the DB finally block so a failure at any
      step after SSH connect cannot leak a connection.
    """
    new_state = LiveNodeState(
        flow_control_history=previous.flow_control_history,
        recv_queue_history=previous.recv_queue_history,
    )
    new_state.last_check_ts = datetime.now(timezone.utc)

    # ── Step 1: SSH ────────────────────────────────────────────────────────────────
    ssh_client = SSHClient(
        host=node["host"],
        port=int(node.get("ssh_port") or 22),
        username=node.get("ssh_user") or "root",
    )
    try:
        ssh_client.connect()
        new_state.ssh_latency_ms = ssh_client.test_connection()
        new_state.ssh_ok = True
    except SSHError as exc:
        new_state.ssh_ok = False
        new_state.db_ok = False
        new_state.error = str(exc)
        logger.warning("SSH failed for node %s (%s): %s", node["name"], node["host"], exc)
        _fill_wsrep_defaults(new_state)
        return new_state
    # ssh_client kept open — closed in DB finally block below

    # ── Steps 2–5: DB + queries (ssh_client always closed in finally) ─────────────
    db_client = DBClient(
        host=node["host"],
        port=int(node.get("port") or 3306),
        user=node.get("db_user") or "root",
        encrypted_password=node.get("db_password") or "",
    )
    try:
        db_client.connect()
        new_state.db_latency_ms = db_client.test_connection()
        new_state.db_ok = True

        # ── wsrep status ───────────────────────────────────────────────────────
        try:
            status_rows = db_client.query(
                f"SHOW GLOBAL STATUS WHERE Variable_name IN ({_WSREP_IN_CLAUSE})"
            )
            status_map = _parse_status_rows(status_rows)
            _apply_wsrep_status(new_state, status_map)

            ro_rows = db_client.query("SHOW GLOBAL VARIABLES LIKE 'read_only'")
            ro_map = _parse_status_rows(ro_rows)
            new_state.readonly = ro_map.get("read_only", "OFF").upper() in ("ON", "1")

            desync_rows = db_client.query("SHOW GLOBAL VARIABLES LIKE 'wsrep_desync'")
            desync_map  = _parse_status_rows(desync_rows)
            new_state.wsrep_desync = desync_map.get("wsrep_desync", "OFF").upper() in ("ON", "1")

        except DBError as exc:
            new_state.error = f"Status query failed: {exc}"
            logger.warning("Status query failed for node %s: %s", node["name"], exc)
            _fill_wsrep_defaults(new_state)

    except DBError as exc:
        new_state.db_ok = False
        new_state.error = str(exc)
        logger.warning("DB failed for node %s (%s): %s", node["name"], node["host"], exc)
        _fill_wsrep_defaults(new_state)
    finally:
        db_client.close()
        ssh_client.close()

    # ── Step 4: maintenance_drift ──────────────────────────────────────────────────
    new_state.maintenance_drift = bool(node.get("maintenance")) and not new_state.readonly

    # ── Step 5: ring buffers ────────────────────────────────────────────────────────
    new_state.flow_control_history.append(new_state.wsrep_flow_control_paused)
    new_state.recv_queue_history.append(new_state.wsrep_local_recv_queue)

    return new_state


def _parse_status_rows(rows: list[dict]) -> dict[str, str]:
    """
    Convert SHOW GLOBAL STATUS / VARIABLES rows to a flat dict.
    Normalises pymysql DictCursor key casing to lowercase.
    """
    result: dict[str, str] = {}
    for row in rows:
        normalised = {k.lower(): v for k, v in row.items()}
        name = normalised.get("variable_name", "")
        value = normalised.get("value", "")
        if name:
            result[name.lower()] = str(value) if value is not None else ""
    return result


def _apply_wsrep_status(state: LiveNodeState, status_map: dict[str, str]) -> None:
    """
    Populate wsrep fields on state from the status_map.
    Missing keys → safe defaults (non-Galera MariaDB returns empty result set).
    """
    state.wsrep_cluster_status       = status_map.get("wsrep_cluster_status", "NON-PRIMARY")
    state.wsrep_connected             = status_map.get("wsrep_connected", "OFF")
    state.wsrep_ready                 = status_map.get("wsrep_ready", "OFF")
    state.wsrep_local_state_comment   = status_map.get("wsrep_local_state_comment", "OFFLINE")
    state.wsrep_incoming_addresses    = status_map.get("wsrep_incoming_addresses", "")

    try:
        state.wsrep_cluster_size = int(status_map.get("wsrep_cluster_size", "0") or "0")
    except ValueError:
        state.wsrep_cluster_size = 0

    try:
        state.wsrep_local_recv_queue = int(status_map.get("wsrep_local_recv_queue", "0") or "0")
    except ValueError:
        state.wsrep_local_recv_queue = 0

    try:
        state.wsrep_local_send_queue = int(status_map.get("wsrep_local_send_queue", "0") or "0")
    except ValueError:
        state.wsrep_local_send_queue = 0

    try:
        state.wsrep_flow_control_paused = float(status_map.get("wsrep_flow_control_paused", "0") or "0")
    except ValueError:
        state.wsrep_flow_control_paused = 0.0

    if not state.wsrep_local_state_comment:
        state.wsrep_local_state_comment = "OFFLINE"


def _fill_wsrep_defaults(state: LiveNodeState) -> None:
    """Set safe offline defaults when SSH or DB is unavailable."""
    state.wsrep_cluster_status       = "NON-PRIMARY"
    state.wsrep_cluster_size          = 0
    state.wsrep_connected             = "OFF"
    state.wsrep_ready                 = "OFF"
    state.wsrep_local_state_comment   = "OFFLINE"
    state.wsrep_local_recv_queue      = 0
    state.wsrep_local_send_queue      = 0
    state.wsrep_flow_control_paused   = 0.0
    state.wsrep_incoming_addresses    = ""
    state.readonly                    = False
    state.wsrep_desync                = False


# ── Arbitrator polling ──────────────────────────────────────────────────────────────

async def _poll_arbitrator(cluster_id: int, arb: dict) -> None:
    """
    Poll a single garbd arbitrator: SSH check + pgrep garbd.
    """
    arb_id = arb["id"]
    live_arbitrator_states.setdefault(cluster_id, {})
    if arb_id not in live_arbitrator_states[cluster_id]:
        live_arbitrator_states[cluster_id][arb_id] = LiveArbitratorState()

    previous = live_arbitrator_states[cluster_id][arb_id]
    prev_ssh_ok = previous.ssh_ok
    prev_garbd_running = previous.garbd_running

    new_state = await asyncio.to_thread(_collect_arbitrator_state, arb)
    live_arbitrator_states[cluster_id][arb_id] = new_state

    state_changed = (
            new_state.ssh_ok != prev_ssh_ok
            or new_state.garbd_running != prev_garbd_running
    )
    if state_changed:
        await _broadcast_arbitrator_state_changed(cluster_id, arb_id, arb["name"], new_state)
        await asyncio.to_thread(
            _write_event_log,
            cluster_id=cluster_id,
            arbitrator_id=arb_id,
            source="ssh",
            message=(
                f"Arbitrator '{arb['name']}' state changed: "
                f"ssh_ok={prev_ssh_ok}→{new_state.ssh_ok}, "
                f"garbd_running={prev_garbd_running}→{new_state.garbd_running}"
            ),
        )


def _collect_arbitrator_state(arb: dict) -> LiveArbitratorState:
    """
    Blocking: SSH connect, check garbd process.
    Per ТЗ раздел 7.4.
    """
    state = LiveArbitratorState()
    state.last_check_ts = datetime.now(timezone.utc)

    ssh_client = SSHClient(
        host=arb["host"],
        port=int(arb.get("ssh_port") or 22),
        username=arb.get("ssh_user") or "root",
    )
    try:
        ssh_client.connect()
        state.ssh_latency_ms = ssh_client.test_connection()
        state.ssh_ok = True
        state.garbd_running = ssh_client.check_process_running("garbd")
    except SSHError as exc:
        state.ssh_ok = False
        state.garbd_running = False
        state.error = str(exc)
        logger.warning(
            "SSH failed for arbitrator %s (%s): %s",
            arb["name"], arb["host"], exc,
        )
    finally:
        ssh_client.close()

    return state


# ── WebSocket broadcast helpers ──────────────────────────────────────────────────────

async def _broadcast_node_state_changed(
        cluster_id: int,
        node_id: int,
        node_name: str,
        state: LiveNodeState,
) -> None:
    event = {
        "event":      "node_state_changed",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "node_id":   node_id,
            "node_name": node_name,
            **state.to_dict(),
        },
    }
    await ws_manager.broadcast(cluster_id, event)
    logger.debug(
        "WS broadcast node_state_changed: cluster=%d node=%d state=%s",
        cluster_id, node_id, state.wsrep_local_state_comment,
    )


async def _broadcast_arbitrator_state_changed(
        cluster_id: int,
        arb_id: int,
        arb_name: str,
        state: LiveArbitratorState,
) -> None:
    event = {
        "event":      "arbitrator_state_changed",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "arbitrator_id":   arb_id,
            "arbitrator_name": arb_name,
            **state.to_dict(),
        },
    }
    await ws_manager.broadcast(cluster_id, event)


# ── Event log writer ────────────────────────────────────────────────────────────────

def _write_event_log(
        *,
        cluster_id: int,
        node_id: int | None = None,
        arbitrator_id: int | None = None,
        source: str,
        message: str,
        level: str = "INFO",
) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO event_logs
                        (cluster_id, node_id, arbitrator_id, source, level, message, ts)
                    VALUES
                        (:cluster_id, :node_id, :arbitrator_id, :source, :level, :message, :ts)
                    """
                ),
                {
                    "cluster_id":     cluster_id,
                    "node_id":        node_id,
                    "arbitrator_id":  arbitrator_id,
                    "source":         source,
                    "level":          level,
                    "message":        message,
                    "ts":             datetime.now(timezone.utc).isoformat(),
                },
            )
    except Exception as exc:
        logger.warning("Failed to write event_log: %s", exc)
