from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from config import settings
from dependencies import get_current_user
from security import clear_auth_cookie, create_access_token, set_auth_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


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
async def login(body: LoginRequest, response: Response) -> MessageResponse:
    """
    Authenticate with username + password from env vars.
    On success, sets a JWT in an httpOnly cookie.

    Gap: single admin account defined via env vars (no users table).
    This matches the ТЗ specification exactly.
    """
    is_valid = (
            body.username == settings.ADMIN_USERNAME
            and body.password == settings.ADMIN_PASSWORD
    )

    if not is_valid:
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
async def me(username: str = Depends(get_current_user)) -> MeResponse:
    """
    Returns the currently authenticated user.
    Dependency get_current_user raises 401 if cookie is missing/invalid.
    Frontend uses this as the primary auth check on app startup.
    """
    return MeResponse(authenticated=True, username=username)