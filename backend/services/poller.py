from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# STUB — Phase 1
#
# The polling loop is an asyncio background task that:
# 1. Reads polling_interval_sec from system_settings on each cycle
# 2. For each enabled node in each cluster:
#    - Opens SSH connection
#    - Runs SHOW GLOBAL STATUS WHERE Variable_name IN (...)
#    - Updates in-memory live state
#    - Emits node_state_changed WS event if state changed
# 3. For each enabled arbitrator:
#    - Checks SSH connectivity and garbd process
#    - Emits arbitrator_state_changed WS event if state changed
# 4. Maintains ring buffer of 30 data points per node for
#    flow_control and recv_queue sparklines (in-memory only)
#
# Ring buffer and live state are stored in module-level dicts
# (cluster_id → node_id → LiveNodeState) — survives only until restart.
# ---------------------------------------------------------------------------

# In-memory live state storage — populated in Phase 1
_live_node_states: dict[int, dict[int, dict]] = {}  # cluster_id → node_id → state
_live_arbitrator_states: dict[int, dict[int, dict]] = {}  # cluster_id → arb_id → state
_sparkline_buffers: dict[int, dict[str, list[float]]] = {}  # node_id → metric → [30 pts]

_poller_task: Optional[asyncio.Task] = None


async def start_poller() -> None:
    """
    Start the background polling task.
    Called from FastAPI startup event in main.py.
    STUB — implement in Phase 1.
    """
    global _poller_task
    logger.info("Polling loop start requested — STUB, not yet implemented (Phase 1)")
    # Phase 1: _poller_task = asyncio.create_task(_poll_loop())


async def stop_poller() -> None:
    """
    Stop the background polling task gracefully.
    Called from FastAPI shutdown event in main.py.
    STUB — implement in Phase 1.
    """
    global _poller_task
    if _poller_task is not None:
        _poller_task.cancel()
        try:
            await _poller_task
        except asyncio.CancelledError:
            pass
    logger.info("Polling loop stopped")


def get_live_node_state(cluster_id: int, node_id: int) -> dict | None:
    """
    Return the latest polled live state for a node.
    Returns None if no data yet (node not yet polled or poller not started).
    STUB — returns None in Phase 0.
    """
    return _live_node_states.get(cluster_id, {}).get(node_id)


def get_live_arbitrator_state(cluster_id: int, arbitrator_id: int) -> dict | None:
    """
    Return the latest polled live state for an arbitrator.
    Returns None if no data yet.
    STUB — returns None in Phase 0.
    """
    return _live_arbitrator_states.get(cluster_id, {}).get(arbitrator_id)


def get_sparkline(node_id: int, metric: str) -> list[float]:
    """
    Return the sparkline ring buffer for a node metric.
    metrics: 'flow_control' | 'recv_queue'
    Returns empty list if no data yet.
    STUB — returns [] in Phase 0.
    """
    return _sparkline_buffers.get(node_id, {}).get(metric, [])