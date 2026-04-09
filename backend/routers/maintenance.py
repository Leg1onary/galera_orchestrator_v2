from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_current_user

router = APIRouter(prefix="/clusters", tags=["maintenance"])

# ---------------------------------------------------------------------------
# STUB — Phase 3
# Endpoints to implement:
#   GET  /api/clusters/{cluster_id}/maintenance/status
#   POST /api/clusters/{cluster_id}/maintenance/rolling-restart
#   POST /api/clusters/{cluster_id}/maintenance/cancel
# ---------------------------------------------------------------------------


@router.get(
    "/{cluster_id}/maintenance/status",
    include_in_schema=True,
)
async def maintenance_status(
        cluster_id: int,
        _: str = Depends(get_current_user),
):
    """STUB: Maintenance status endpoint. Implement in Phase 3."""
    return {"active_operation": None}


@router.post(
    "/{cluster_id}/maintenance/rolling-restart",
    include_in_schema=True,
)
async def rolling_restart(
        cluster_id: int,
        _: str = Depends(get_current_user),
):
    """STUB: Rolling restart. Implement in Phase 3."""
    return {"accepted": False, "message": "Not implemented yet"}


@router.post(
    "/{cluster_id}/maintenance/cancel",
    include_in_schema=True,
)
async def maintenance_cancel(
        cluster_id: int,
        _: str = Depends(get_current_user),
):
    """STUB: Maintenance cancel. Implement in Phase 3."""
    return {"cancelled": False, "message": "Not implemented yet"}