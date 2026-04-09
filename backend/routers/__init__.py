# Routers package
# Import all routers here for convenient access in main.py
from routers.auth import router as auth_router
from routers.clusters import router as clusters_router
from routers.diagnostics import router as diagnostics_router
from routers.maintenance import router as maintenance_router
from routers.nodes import router as nodes_router
from routers.recovery import router as recovery_router
from routers.settings import router as settings_router
from routers.ws import router as ws_router

__all__ = [
    "auth_router",
    "clusters_router",
    "diagnostics_router",
    "maintenance_router",
    "nodes_router",
    "recovery_router",
    "settings_router",
    "ws_router",
]