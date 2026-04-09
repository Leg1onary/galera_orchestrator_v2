from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import require_auth

router = APIRouter(prefix="/clusters", tags=["recovery"])

# ---------------------------------------------------------------------------
# STUB — Phase 3
# Endpoints to implement:
#   GET  /api/clusters/{cluster_id}/recovery/status
#   POST /api/clusters/{cluster_id}/recovery/bootstrap
#   POST /api/clusters/{cluster_id}/recovery/rejoin
#   POST /api/clusters/{cluster_id}/recovery/cancel
# ---------------------------------------------------------------------------


@router.get(
    "/{cluster_id}/recovery/status",
    include_in_schema=True,
)
async def recovery_status(
        cluster_id: int,
        _: str = Depends(require_auth),
):
    """STUB: Recovery status endpoint. Implement in Phase 3."""
    return {"active_operation": None}


@router.post(
    "/{cluster_id}/recovery/bootstrap",
    include_in_schema=True,
)
async def recovery_bootstrap(
        cluster_id: int,
        _: str = Depends(require_auth),
):
    """STUB: Recovery bootstrap. Implement in Phase 3."""
    return {"accepted": False, "message": "Not implemented yet"}


@router.post(
    "/{cluster_id}/recovery/rejoin",
    include_in_schema=True,
)
async def recovery_rejoin(
        cluster_id: int,
        _: str = Depends(require_auth),
):
    """STUB: Recovery rejoin. Implement in Phase 3."""
    return {"accepted": False, "message": "Not implemented yet"}


@router.post(
    "/{cluster_id}/recovery/cancel",
    include_in_schema=True,
)
async def recovery_cancel(
        cluster_id: int,
        _: str = Depends(require_auth),
):
    """STUB: Recovery cancel. Implement in Phase 3."""
    return {"cancelled": False, "message": "Not implemented yet"}