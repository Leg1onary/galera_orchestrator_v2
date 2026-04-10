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
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import text

from database import engine
from security import decode_token
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_token_from_websocket(websocket: WebSocket) -> str | None:
    """
    Extract JWT from the httpOnly cookie on the WebSocket upgrade request.
    The browser sends cookies automatically on WS upgrade — same as REST.
    Cookie name 'access_token' — set by POST /api/auth/login.
    """
    return websocket.cookies.get("access_token")


def _cluster_exists(cluster_id: int) -> bool:
    """Check that cluster_id is present in DB. Sync — called before accept()."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM clusters WHERE id = :cid"),
            {"cid": cluster_id},
        ).fetchone()
    return row is not None


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/clusters/{cluster_id}")
async def websocket_endpoint(websocket: WebSocket, cluster_id: int) -> None:
    """
    Cluster-scoped WebSocket endpoint.

    Authentication:
      - Reads JWT from the 'access_token' httpOnly cookie
      - Closes with 1008 (Policy Violation) if not authenticated

    Lifecycle:
      - On connect: accept → auth check → cluster check → register
      - On disconnect: deregister from ConnectionManager
      - Does not push data itself — Poller calls ws_manager.broadcast()

    Keepalive:
      - Client sends "ping" → server responds "pong"
      - Frontend reconnects every 5s on disconnect (ТЗ 5.3)
    """
    # FIX MAJOR: accept() ВСЕГДА первым — Starlette требует accept() до любого close()
    # без этого close() не доходит до клиента на части браузеров/прокси
    await websocket.accept()

    # ── Auth: token present? ──────────────────────────────────────────────────
    token = _get_token_from_websocket(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "WS rejected — no auth cookie (cluster_id=%d, client=%s)",
            cluster_id, websocket.client,
        )
        return

    # ── Auth: token valid? ────────────────────────────────────────────────────
    try:
        decode_token(token)
    except Exception as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "WS rejected — invalid token (cluster_id=%d): %s",
            cluster_id, exc,
        )
        return

    # ── FIX MINOR: cluster_id существует в БД? ────────────────────────────────
    if not _cluster_exists(cluster_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "WS rejected — cluster %d not found in DB", cluster_id
        )
        return

    # ── Register connection ───────────────────────────────────────────────────
    await ws_manager.connect(cluster_id, websocket)
    logger.info(
        "WS connected — cluster_id=%d client=%s", cluster_id, websocket.client
    )

    try:
        # Keep the connection alive.
        # Poller pushes events via ws_manager.broadcast() — we only handle
        # inbound messages here (ping/pong keepalive).
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                # FIX MINOR (Phase 2 keepalive): respond to ping from frontend
                # Prevents nginx/proxy timeout-based disconnects (default 60–90s)
                await websocket.send_text("pong")
                logger.debug("WS ping/pong — cluster_id=%d", cluster_id)
            else:
                logger.debug(
                    "WS received from cluster %d: %r (ignored)", cluster_id, data
                )

    except WebSocketDisconnect as exc:
        logger.info(
            "WS client disconnected — cluster_id=%d code=%s",
            cluster_id, exc.code,
        )
    except Exception as exc:
        logger.warning(
            "WS error — cluster_id=%d: %s", cluster_id, exc
        )
    finally:
        # FIX MAJOR: disconnect приведён к await-форме
        # ws_manager.disconnect() должен быть async (см. ws_manager.py)
        await ws_manager.disconnect(cluster_id, websocket)
        logger.info(
            "WS deregistered — cluster_id=%d client=%s", cluster_id, websocket.client
        )