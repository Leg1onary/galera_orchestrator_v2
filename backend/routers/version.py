import asyncio
import json
import logging
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])

DOCKER_IMAGE = "ghcr.io/leg1onary/galera_orchestrator_v2:latest"
GHCR_TOKEN_URL = (
    "https://ghcr.io/token?scope=repository:leg1onary/galera_orchestrator_v2:pull&service=ghcr.io"
)
GHCR_MANIFEST_URL = (
    "https://ghcr.io/v2/leg1onary/galera_orchestrator_v2/manifests/latest"
)
GHCR_BLOBS_URL = "https://ghcr.io/v2/leg1onary/galera_orchestrator_v2/blobs/{digest}"


# ---------------------------------------------------------------------------
# Resolve current git SHA once at import time — no user config needed
# ---------------------------------------------------------------------------
def _resolve_git_sha() -> str:
    """Try git, then env fallback APP_VERSION (set by Dockerfile ARG GIT_SHA), then 'unknown'."""
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
    import os
    v = os.getenv("APP_VERSION", "").strip()
    return v if v and v != "unknown" else "unknown"


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
# Helpers — docker-based (primary, container mode)
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
    """Manifest digest of :latest from registry via docker CLI (no pull)."""
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


# ---------------------------------------------------------------------------
# Helpers — GHCR API fallback (local dev / no docker CLI)
# ---------------------------------------------------------------------------
def _ghcr_token() -> Optional[str]:
    """Obtain anonymous pull token from GHCR."""
    try:
        req = urllib.request.Request(
            GHCR_TOKEN_URL,
            headers={"User-Agent": "galera-orchestrator"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("token")
    except Exception as exc:
        logger.debug("GHCR token fetch failed: %s", exc)
    return None


def _get_latest_sha_from_ghcr() -> Optional[str]:
    """
    Fetch :latest manifest from GHCR and extract the git SHA from the
    org.opencontainers.image.revision label (injected by docker/metadata-action).

    docker/metadata-action sets this label to the full 40-char SHA.
    We return the first 7 characters to match CURRENT_VERSION (short SHA).

    Returns 7-char short SHA or None.
    """
    token = _ghcr_token()
    if not token:
        return None

    auth_header = {"Authorization": f"Bearer {token}", "User-Agent": "galera-orchestrator"}

    try:
        # Step 1: fetch OCI manifest → get config blob digest
        req = urllib.request.Request(
            GHCR_MANIFEST_URL,
            headers={
                **auth_header,
                "Accept": "application/vnd.oci.image.manifest.v1+json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            manifest = json.loads(resp.read())

        config_digest = manifest.get("config", {}).get("digest")
        if not config_digest:
            logger.debug("GHCR manifest: no config digest found")
            return None

        # Step 2: fetch config blob → extract Labels
        req2 = urllib.request.Request(
            GHCR_BLOBS_URL.format(digest=config_digest),
            headers=auth_header,
        )
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            config = json.loads(resp2.read())

        labels: dict = config.get("config", {}).get("Labels") or {}
        # docker/metadata-action sets org.opencontainers.image.revision = full 40-char SHA
        revision: str = labels.get("org.opencontainers.image.revision", "")
        if revision and len(revision) >= 7:
            return revision[:7]

        logger.debug("GHCR config labels: %s", labels)

    except Exception as exc:
        logger.debug("GHCR manifest/blob fetch failed: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Core check logic
# ---------------------------------------------------------------------------
async def _run_check() -> UpdateCheckResponse:
    loop = asyncio.get_running_loop()
    now = datetime.now(timezone.utc).isoformat()

    # --- Primary path: docker CLI available (running inside container) ---
    current_digest = await loop.run_in_executor(None, _get_current_image_digest)
    remote_digest  = await loop.run_in_executor(None, _get_remote_digest)

    if remote_digest is not None:
        # docker CLI works — compare digests directly
        if current_digest is not None and current_digest != remote_digest:
            return UpdateCheckResponse(
                status="update_available",
                current_version=CURRENT_VERSION,
                message="A new version is available — pull the latest image to update",
                checked_at=now,
            )
        return UpdateCheckResponse(
            status="up_to_date",
            current_version=CURRENT_VERSION,
            message="Your version is up to date",
            checked_at=now,
        )

    # --- Fallback path: no docker CLI (local dev / bare process) ---
    # Compare CURRENT_VERSION (7-char short SHA from git or APP_VERSION env)
    # against the revision label baked into the :latest image on GHCR.
    if CURRENT_VERSION == "unknown":
        return UpdateCheckResponse(
            status="registry_unavailable",
            current_version=CURRENT_VERSION,
            message="Cannot determine current version — APP_VERSION env not set and git unavailable",
            checked_at=now,
        )

    latest_sha = await loop.run_in_executor(None, _get_latest_sha_from_ghcr)

    if latest_sha is None:
        return UpdateCheckResponse(
            status="registry_unavailable",
            current_version=CURRENT_VERSION,
            message="Registry unavailable — network may be isolated or GHCR unreachable",
            checked_at=now,
        )

    if latest_sha != CURRENT_VERSION:
        return UpdateCheckResponse(
            status="update_available",
            current_version=CURRENT_VERSION,
            message="A new version is available — pull the latest image to update",
            checked_at=now,
        )

    return UpdateCheckResponse(
        status="up_to_date",
        current_version=CURRENT_VERSION,
        message="Your version is up to date",
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

    Primary path (container mode):
      docker inspect → current digest
      docker manifest inspect → remote digest
      Compare digests directly.

    Fallback path (local dev / no docker CLI):
      GHCR anonymous token → OCI manifest → config blob → Labels
      org.opencontainers.image.revision[:7] vs CURRENT_VERSION

    Always performs a fresh check — no server-side caching.
    Returns one of three statuses:
      - update_available
      - up_to_date
      - registry_unavailable
    """
    return await _run_check()
