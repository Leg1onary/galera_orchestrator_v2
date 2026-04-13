import logging

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings
from dependencies import require_auth
from security import clear_auth_cookie, create_access_token, set_auth_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    authenticated: bool
    username: str


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=MessageResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
) -> MessageResponse:
    """
    Authenticate with username + password.
    Rate limited to 5 attempts per minute per IP (SEC-001).
    Password verified against bcrypt hash stored in ADMIN_PASSWORD_HASH (SEC-003).
    On success, sets a JWT in an httpOnly cookie.
    """
    username_ok = body.username == settings.ADMIN_USERNAME
    try:
        password_ok = bcrypt.checkpw(
            body.password.encode("utf-8"),
            settings.ADMIN_PASSWORD_HASH.encode("utf-8"),
        )
    except Exception:
        password_ok = False

    if not username_ok or not password_ok:
        logger.warning("Failed login attempt for username: %s", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(username=body.username)
    set_auth_cookie(response, token)

    logger.info("Successful login for username: %s", body.username)
    return MessageResponse(message="Login successful")


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------
@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    """
    Clear the authentication cookie.
    Does not require the user to be authenticated —
    clearing a missing cookie is a no-op and should not error.
    """
    clear_auth_cookie(response)
    return MessageResponse(message="Logged out successfully")


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=MeResponse)
async def me(username: str = Depends(require_auth)) -> MeResponse:
    """
    Returns the currently authenticated user.
    Dependency require_auth raises 401 if cookie is missing/invalid.
    Frontend uses this as the primary auth check on app startup.
    """
    return MeResponse(authenticated=True, username=username)
