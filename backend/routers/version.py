import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])

# ---------------------------------------------------------------------------
# Docker image reference — adjust to your registry/image name
# ---------------------------------------------------------------------------
DOCKER_IMAGE = "ghcr.io/leg1onary/galera_orchestrator_v2:latest"

# ---------------------------------------------------------------------------
# In-memory cache for update check result (TTL = 24h)
# ---------------------------------------------------------------------------
_cache: dict = {
    "update_available": False,
    "latest_digest":    None,
    "current_digest":   None,
    "checked_at":       None,
    "error":            None,
}
_cache_lock = asyncio.Lock()


class VersionResponse(BaseModel):
    version: str


class UpdateCheckResponse(BaseModel):
    update_available: bool
    current_version:  str
    latest_digest:    Optional[str]
    current_digest:   Optional[str]
    checked_at:       Optional[str]
    error:            Optional[str]


def _get_current_digest() -> Optional[str]:
    """Get the image ID/digest of the running container via docker inspect."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.Image}}", "galera-orchestrator"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:19] or None
    except Exception as exc:
        logger.debug("docker inspect failed: %s", exc)
    return None


def _get_latest_digest() -> Optional[str]:
    """Fetch remote manifest digest without pulling the image."""
    try:
        result = subprocess.run(
            ["docker", "manifest", "inspect", "--verbose", DOCKER_IMAGE],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            # manifest inspect --verbose returns a list or a single object
            if isinstance(data, list):
                data = data[0]
            digest = (
                data.get("Descriptor", {}).get("digest")
                or data.get("config", {}).get("digest")
            )
            return str(digest)[:19] if digest else None
    except Exception as exc:
        logger.debug("docker manifest inspect failed: %s", exc)
    return None


async def _do_check() -> None:
    """Run the update check in a thread and populate the cache."""
    loop = asyncio.get_running_loop()
    current = await loop.run_in_executor(None, _get_current_digest)
    latest  = await loop.run_in_executor(None, _get_latest_digest)

    error: Optional[str] = None
    update_available = False

    if latest is None:
        error = "Could not reach registry — network may be isolated or docker not available"
    elif current is None:
        error = "Could not determine current digest (not running in Docker?)"
    else:
        update_available = current != latest

    async with _cache_lock:
        _cache["update_available"] = update_available
        _cache["latest_digest"]    = latest
        _cache["current_digest"]   = current
        _cache["checked_at"]       = datetime.now(timezone.utc).isoformat()
        _cache["error"]            = error

    logger.info(
        "Update check complete: update_available=%s current=%s latest=%s error=%s",
        update_available, current, latest, error,
    )


def _cache_is_fresh() -> bool:
    """Return True if cache was populated less than 24 hours ago."""
    if not _cache["checked_at"]:
        return False
    checked = datetime.fromisoformat(_cache["checked_at"])
    age = (datetime.now(timezone.utc) - checked).total_seconds()
    return age < 86_400  # 24 h


# ---------------------------------------------------------------------------
# GET /api/version
# ---------------------------------------------------------------------------
@router.get("", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """
    Returns the current application version (git SHA injected at build time
    via APP_VERSION env var, e.g. '59c14f8').
    """
    return VersionResponse(version=settings.APP_VERSION)


# ---------------------------------------------------------------------------
# GET /api/version/check
# ---------------------------------------------------------------------------
@router.get("/check", response_model=UpdateCheckResponse)
async def check_update() -> UpdateCheckResponse:
    """
    Check whether a newer Docker image is available.

    Uses `docker manifest inspect` to fetch the remote digest without
    pulling the image — works even without internet access if the
    internal registry (GHCR / private) is reachable.

    Result is cached for 24 hours. Subsequent calls return the cached
    value immediately.

    On error (registry unreachable, Docker not available) returns
    update_available=False and an error message — never raises 5xx.
    """
    if not _cache_is_fresh():
        await _do_check()

    return UpdateCheckResponse(
        update_available=_cache["update_available"],
        current_version=settings.APP_VERSION,
        latest_digest=_cache["latest_digest"],
        current_digest=_cache["current_digest"],
        checked_at=_cache["checked_at"],
        error=_cache["error"],
    )
