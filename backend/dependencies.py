from __future__ import annotations

from typing import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.engine import Connection

from database import get_connection
from security import AUTH_COOKIE_NAME, decode_token


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def get_current_user(request: Request) -> str:
    """
    FastAPI dependency — extract and validate JWT from httpOnly cookie.

    Returns the authenticated username on success.
    Raises HTTP 401 if the cookie is missing or the token is invalid/expired.

    Usage:
        @router.get("/protected")
        async def protected(username: str = Depends(get_current_user)):
            ...
    """
    token: str | None = request.cookies.get(AUTH_COOKIE_NAME)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    username = decode_token(token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return username


# ---------------------------------------------------------------------------
# Database connection dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Connection, None, None]:
    """
    FastAPI dependency — yield a SQLAlchemy Core Connection.

    Commits automatically on success, rolls back on exception.
    Uses the engine-level transaction (engine.begin()).

    Usage:
        @router.get("/items")
        async def get_items(conn: Connection = Depends(get_db)):
            result = conn.execute(select(items))
            ...
    """
    with get_connection() as conn:
        yield conn