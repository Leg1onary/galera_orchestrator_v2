from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from security import AUTH_COOKIE_NAME, decode_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# ---------------------------------------------------------------------------
# STUB — Phase 1
# Full implementation requires:
#   - ConnectionManager class with per-cluster subscription dict
#   - broadcast() for each of the 6 event types
#   - Integration with polling loop to emit node_state_changed events
#
# Event types (per ТЗ section 5.2):
#   node_state_changed
#   arbitrator_state_changed
#   operation_started
#   operation_progress
#   operation_finished
#   log_entry
# ---------------------------------------------------------------------------


@router.websocket("/ws/clusters/{cluster_id}")
async def websocket_endpoint(websocket: WebSocket, cluster_id: int) -> None:
    """
    WebSocket endpoint for cluster-scoped real-time events.

    Auth: validated via httpOnly cookie (same cookie as REST API).
    The browser sends cookies automatically during the WS upgrade handshake.

    Phase 0: accepts connection, sends a stub 'connected' message, then
    waits and handles disconnect. Full implementation in Phase 1.
    """
    # Auth check via cookie (browsers send cookies on WS upgrade)
    token = websocket.cookies.get(AUTH_COOKIE_NAME)
    if token is None or decode_token(token) is None:
        await websocket.close(code=4001)
        logger.warning(
            "WS auth failed for cluster_id=%d — no valid cookie", cluster_id
        )
        return

    await websocket.accept()
    logger.info("WS connection accepted for cluster_id=%d", cluster_id)

    try:
        # Send a stub connected event so frontend can validate the handshake
        await websocket.send_json(
            {
                "event": "connected",
                "cluster_id": cluster_id,
                "ts": None,
                "payload": {"message": "WebSocket stub — Phase 1 pending"},
            }
        )

        # Keep connection alive until client disconnects
        while True:
            # In Phase 1 this loop will receive messages and handle pings
            data = await websocket.receive_text()
            logger.debug(
                "WS received from cluster_id=%d: %s", cluster_id, data
            )

    except WebSocketDisconnect:
        logger.info("WS disconnected for cluster_id=%d", cluster_id)