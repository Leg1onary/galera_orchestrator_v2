# routers/contours.py
from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text

from database import get_connection
from dependencies import require_auth

router = APIRouter(prefix="/contours", tags=["contours"])


@router.get("", summary="List all contours")
def list_contours(
        user=Depends(require_auth),
        conn: Connection = Depends(get_connection),   # ← Depends!
):
    rows = conn.execute(
        text("SELECT id, name FROM contours ORDER BY name")
    ).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]