from __future__ import annotations

from typing import Generator

from fastapi import Cookie, HTTPException, status
from sqlalchemy.engine import Connection

from database import get_connection
from security import AUTH_COOKIE_NAME, decode_token


def require_auth(
        access_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> str:
    """
    FastAPI dependency — extract and validate JWT from httpOnly cookie.

    Returns the authenticated username on success.
    Raises HTTP 401 if the cookie is missing or the token is invalid/expired.

    Usage:
        @router.get("/protected")
        async def protected(username: str = Depends(require_auth)):
            ...
    """
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    username = decode_token(access_token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return username


def get_db() -> Generator[Connection, None, None]:
    """
    FastAPI dependency — yield a SQLAlchemy Core Connection.
    get_connection() is a plain generator (not a context manager).
    """
    yield from get_connection()