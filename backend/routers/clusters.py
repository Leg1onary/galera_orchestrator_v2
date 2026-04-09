from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_current_user

router = APIRouter(prefix="/clusters", tags=["clusters"])


# ---------------------------------------------------------------------------
# STUB — Phase 1
# Endpoints to implement:
#   GET  /api/clusters
#   GET  /api/contours
#   GET  /api/clusters?contour_id=N
#   GET  /api/clusters/{cluster_id}/status
#   GET  /api/clusters/{cluster_id}/log
#   DELETE /api/clusters/{cluster_id}/log
#   GET  /api/clusters/{cluster_id}/nodes
#   GET  /api/clusters/{cluster_id}/nodes/{id}/details
#   PATCH /api/clusters/{cluster_id}/nodes/{id}
#   POST /api/clusters/{cluster_id}/nodes/{id}/actions
#   GET  /api/clusters/{cluster_id}/nodes/{id}/test-connection
#   GET  /api/clusters/{cluster_id}/nodes/{id}/innodb-status
#   GET  /api/clusters/{cluster_id}/arbitrators
#   GET  /api/clusters/{cluster_id}/arbitrators/{id}/test-connection
#   GET  /api/clusters/{cluster_id}/arbitrators/{id}/log?lines=N
# ---------------------------------------------------------------------------

@router.get("", include_in_schema=True)
async def list_clusters(_: str = Depends(get_current_user)):
    """STUB: Returns empty list. Implement in Phase 1."""
    return []


@router.get("/{cluster_id}/status", include_in_schema=True)
async def cluster_status(
        cluster_id: int,
        _: str = Depends(get_current_user),
):
    """STUB: Returns placeholder. Implement in Phase 1."""
    return {
        "cluster": None,
        "nodes": [],
        "arbitrators": [],
        "active_operation": None,
    }