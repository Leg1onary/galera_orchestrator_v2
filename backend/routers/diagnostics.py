from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_current_user

router = APIRouter(prefix="/clusters", tags=["diagnostics"])

# ---------------------------------------------------------------------------
# STUB — Phase 4
# Endpoints to implement:
#   GET  /api/clusters/{cluster_id}/diagnostics/config-diff
#   GET  /api/clusters/{cluster_id}/diagnostics/variables
#   POST /api/clusters/{cluster_id}/diagnostics/check-all
#   POST /api/clusters/{cluster_id}/diagnostics/resources
# ---------------------------------------------------------------------------


@router.get(
    "/{cluster_id}/diagnostics/config-diff",
    include_in_schema=True,
)
async def config_diff(
        cluster_id: int,
        _: str = Depends(get_current_user),
):
    """STUB: Config diff endpoint. Implement in Phase 4."""
    return {"diff": [], "cluster_id": cluster_id}