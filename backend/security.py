from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Response

from config import settings

# Cookie name used throughout the application
AUTH_COOKIE_NAME = "access_token"


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------
def create_access_token(username: str) -> str:
    """
    Create a signed JWT for the given username.
    Expiry is controlled by settings.JWT_EXPIRE_HOURS (default: 8h).
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    payload = {
        "sub": username,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------
def decode_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT.
    Returns the username (sub claim) on success, None on any failure.
    Does NOT raise — callers decide how to handle None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: Optional[str] = payload.get("sub")
        return username
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set the authentication cookie on the response.

    - httponly=True  : not accessible from JavaScript
    - samesite="lax" : protects against CSRF while allowing normal navigation
    - secure         : controlled by settings.COOKIE_SECURE (default True).
                       Set COOKIE_SECURE=false only for local dev without TLS.
    """
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clear the authentication cookie.
    Must match the same path/samesite/secure settings as set_auth_cookie.
    """
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
