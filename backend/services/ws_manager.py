"""
ConnectionManager — WebSocket connection registry and broadcast.

Per ТЗ раздел 5: cluster-scoped WebSocket connections.
Each cluster_id has a set of connected WebSocket clients.

Broadcast sends to all clients of a given cluster_id in parallel.
Failed/disconnected clients are removed automatically.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections keyed by cluster_id.

    Thread safety: all methods are async and should be called from
    the same asyncio event loop. Do NOT call from threads.
    """

    def __init__(self) -> None:
        # cluster_id → set of active WebSocket connections
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, cluster_id: int, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection for a cluster.

        Args:
            cluster_id: the cluster this client is subscribing to
            websocket:  the WebSocket instance (already accepted by the caller)
        """
        await websocket.accept()
        if cluster_id not in self._connections:
            self._connections[cluster_id] = set()
        self._connections[cluster_id].add(websocket)
        logger.info(
            "WS client connected to cluster %d — total: %d",
            cluster_id,
            len(self._connections[cluster_id]),
        )

    def disconnect(self, cluster_id: int, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the registry.
        Safe to call even if the connection was already removed.

        Args:
            cluster_id: the cluster this client was subscribed to
            websocket:  the WebSocket instance to remove
        """
        if cluster_id in self._connections:
            self._connections[cluster_id].discard(websocket)
            logger.info(
                "WS client disconnected from cluster %d — remaining: %d",
                cluster_id,
                len(self._connections[cluster_id]),
            )

    async def broadcast(self, cluster_id: int, event: dict) -> None:
        """
        Send a JSON event to all clients subscribed to a cluster.
        Dead connections are silently removed.

        Args:
            cluster_id: target cluster
            event:      dict that will be serialised to JSON
        """
        clients = self._connections.get(cluster_id, set())
        if not clients:
            return

        # Snapshot the set — we may mutate it while iterating
        snapshot = list(clients)

        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_json(event)
            except Exception as exc:
                logger.debug(
                    "WS send failed for cluster %d, removing client: %s",
                    cluster_id, exc,
                )
                self.disconnect(cluster_id, ws)

        await asyncio.gather(*[_send(ws) for ws in snapshot], return_exceptions=True)

    def client_count(self, cluster_id: int) -> int:
        """Return number of active connections for a cluster."""
        return len(self._connections.get(cluster_id, set()))

    def all_cluster_ids(self) -> list[int]:
        """Return all cluster_ids that have at least one active connection."""
        return [cid for cid, conns in self._connections.items() if conns]


# ── Singleton instance ────────────────────────────────────────────────────────
# Imported by routers/ws.py and services/poller.py
ws_manager = ConnectionManager()