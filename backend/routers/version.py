import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])

DOCKER_IMAGE = "ghcr.io/leg1onary/galera_orchestrator_v2:latest"


# ---------------------------------------------------------------------------
# Resolve current git SHA once at import time — no user config needed
# ---------------------------------------------------------------------------
def _resolve_git_sha() -> str:
    """Try git, then env fallback APP_VERSION, then 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3,
            cwd=subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip() or ".",
        )
        sha = result.stdout.strip()
        if result.returncode == 0 and sha:
            return sha
    except Exception:
        pass
    # Fallback: read APP_VERSION from env (set by Dockerfile ARG GIT_SHA)
    import os
    v = os.getenv("APP_VERSION", "").strip()
    return v if v and v != "2.0.0" else "unknown"


CURRENT_VERSION: str = _resolve_git_sha()
logger.info("Resolved application version: %s", CURRENT_VERSION)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class VersionResponse(BaseModel):
    version: str


class UpdateCheckResponse(BaseModel):
    status: str          # "update_available" | "up_to_date" | "registry_unavailable"
    current_version: str
    message: str
    checked_at: Optional[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_current_image_digest() -> Optional[str]:
    """Digest of the running container image via `docker inspect`."""
    try:
        r = subprocess.run(
            ["docker", "inspect", "--format", "{{.Image}}", "galera-orchestrator"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            val = r.stdout.strip()
            return val if val else None
    except Exception as exc:
        logger.debug("docker inspect failed: %s", exc)
    return None


def _get_remote_digest() -> Optional[str]:
    """Manifest digest of :latest from registry (no pull)."""
    try:
        r = subprocess.run(
            ["docker", "manifest", "inspect", "--verbose", DOCKER_IMAGE],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        if isinstance(data, list):
            data = data[0]
        return (
            data.get("Descriptor", {}).get("digest")
            or data.get("config", {}).get("digest")
        )
    except Exception as exc:
        logger.debug("docker manifest inspect failed: %s", exc)
    return None


async def _run_check() -> UpdateCheckResponse:
    loop = asyncio.get_running_loop()
    current_digest = await loop.run_in_executor(None, _get_current_image_digest)
    remote_digest  = await loop.run_in_executor(None, _get_remote_digest)
    now = datetime.now(timezone.utc).isoformat()

    if remote_digest is None:
        return UpdateCheckResponse(
            status="registry_unavailable",
            current_version=CURRENT_VERSION,
            message="Registry unavailable — network may be isolated or docker CLI not accessible",
            checked_at=now,
        )

    if current_digest is None or current_digest == remote_digest:
        # current_digest None means we can't compare — treat as up-to-date
        # (conservative: don't alarm if we simply can't read local digest)
        return UpdateCheckResponse(
            status="up_to_date",
            current_version=CURRENT_VERSION,
            message="Your version is up to date",
            checked_at=now,
        )

    return UpdateCheckResponse(
        status="update_available",
        current_version=CURRENT_VERSION,
        message="A new version is available — pull the latest image to update",
        checked_at=now,
    )


# ---------------------------------------------------------------------------
# GET /api/version
# ---------------------------------------------------------------------------
@router.get("", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """Returns current git SHA resolved at startup."""
    return VersionResponse(version=CURRENT_VERSION)


# ---------------------------------------------------------------------------
# POST /api/version/check   (POST — explicit user action, not cacheable)
# ---------------------------------------------------------------------------
@router.post("/check", response_model=UpdateCheckResponse)
async def check_update() -> UpdateCheckResponse:
    """
    Triggered by user clicking 'Check updates'.
    Runs `docker manifest inspect` against the registry.
    Always performs a fresh check — no server-side caching.
    Returns one of three statuses:
      - update_available
      - up_to_date
      - registry_unavailable
    """
    return await _run_check()
