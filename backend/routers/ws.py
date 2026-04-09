"""
WebSocket endpoint — WS /ws/clusters/{cluster_id}

Per ТЗ раздел 5:
  - Auth via httpOnly cookie (same JWT as REST API)
  - One endpoint per cluster_id
  - Frontend reconnects every 5s on disconnect

Per ТЗ раздел 5.2: events:
  node_state_changed, arbitrator_state_changed,
  operation_started, operation_progress, operation_finished, log_entry
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from security import decode_token
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_token_from_websocket(websocket: WebSocket) -> str | None:
    """
    Extract JWT from the httpOnly cookie on the WebSocket upgrade request.

    The browser sends cookies automatically on WS upgrade — same as REST.
    We read the cookie named 'access_token' (set by POST /api/auth/login).
    """
    return websocket.cookies.get("access_token")


@router.websocket("/ws/clusters/{cluster_id}")
async def websocket_endpoint(websocket: WebSocket, cluster_id: int) -> None:
    """
    Cluster-scoped WebSocket endpoint.

    Authentication:
      - Reads JWT from the 'access_token' httpOnly cookie
      - Closes with 1008 (Policy Violation) if not authenticated

    Lifecycle:
      - On connect: register with ConnectionManager
      - On disconnect: deregister from ConnectionManager
      - Does not send data itself — Poller calls ws_manager.broadcast()
    """
    # ── Auth check ────────────────────────────────────────────────────────────
    token = _get_token_from_websocket(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "WS connection rejected — no auth cookie (cluster_id=%d, client=%s)",
            cluster_id, websocket.client,
        )
        return

    try:
        decode_token(token)
    except Exception as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "WS connection rejected — invalid token (cluster_id=%d): %s",
            cluster_id, exc,
        )
        return

    # ── Register connection ───────────────────────────────────────────────────
    await ws_manager.connect(cluster_id, websocket)

    try:
        # Keep the connection open — wait for client disconnect or error
        # Poller pushes data via ws_manager.broadcast(), not here
        while True:
            # recv_text() blocks until the client sends something or disconnects.
            # Clients should send periodic pings to keep the connection alive;
            # if they don't send anything we still stay open until disconnect.
            data = await websocket.receive_text()
            # Silently ignore client messages in Phase 1
            # Phase 2+: handle "ping" → "pong" keepalive
            logger.debug(
                "WS received from cluster %d client: %r (ignored)", cluster_id, data
            )

    except WebSocketDisconnect as exc:
        logger.info(
            "WS client disconnected from cluster %d (code=%s)",
            cluster_id, exc.code,
        )
    except Exception as exc:
        logger.warning(
            "WS error on cluster %d: %s", cluster_id, exc
        )
    finally:
        ws_manager.disconnect(cluster_id, websocket)