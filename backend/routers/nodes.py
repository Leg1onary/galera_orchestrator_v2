from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import require_auth

router = APIRouter(prefix="/clusters", tags=["nodes"])

# ---------------------------------------------------------------------------
# STUB — Phase 2
# Node-specific endpoints live under /clusters/{cluster_id}/nodes/...
# They are defined here separately for modularity but share the prefix
# with clusters router. Phase 2 will split concerns properly.
#
# Endpoints to implement:
#   POST  /api/clusters/{cluster_id}/nodes/{id}/actions
#   PATCH /api/clusters/{cluster_id}/nodes/{id}
#   GET   /api/clusters/{cluster_id}/nodes/{id}/test-connection
#   GET   /api/clusters/{cluster_id}/nodes/{id}/innodb-status
# ---------------------------------------------------------------------------


@router.post("/{cluster_id}/nodes/{node_id}/actions", include_in_schema=True)
async def node_action(
        cluster_id: int,
        node_id: int,
        _: str = Depends(require_auth),
):
    """STUB: Node action endpoint. Implement in Phase 2."""
    return {"accepted": False, "message": "Not implemented yet"}