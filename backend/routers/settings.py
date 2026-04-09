from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

# ---------------------------------------------------------------------------
# STUB — Phase 2
# Endpoints to implement:
#   GET    /api/settings/clusters
#   POST   /api/settings/clusters
#   PATCH  /api/settings/clusters/{id}
#   DELETE /api/settings/clusters/{id}
#   GET    /api/settings/nodes
#   POST   /api/settings/nodes
#   PATCH  /api/settings/nodes/{id}
#   DELETE /api/settings/nodes/{id}
#   GET    /api/settings/arbitrators
#   POST   /api/settings/arbitrators
#   PATCH  /api/settings/arbitrators/{id}
#   DELETE /api/settings/arbitrators/{id}
#   GET    /api/settings/datacenters
#   POST   /api/settings/datacenters
#   PATCH  /api/settings/datacenters/{id}
#   DELETE /api/settings/datacenters/{id}
#   GET    /api/settings/system
#   PATCH  /api/settings/system
# ---------------------------------------------------------------------------


@router.get("/system", include_in_schema=True)
async def get_system_settings(_: str = Depends(get_current_user)):
    """STUB: Returns default system settings. Implement in Phase 2."""
    return {
        "polling_interval_sec": 5,
        "event_log_limit": 200,
        "timezone": "UTC",
    }