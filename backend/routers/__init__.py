from .auth        import router as auth_router
from .clusters    import router as clusters_router
from .contours    import router as contours_router
from .diagnostics import router as diagnostics_router
from .maintenance import router as maintenance_router
from .nodes       import router as nodes_router
from .recovery    import router as recovery_router
from .settings    import router as settings_router
from .ws          import router as ws_router

__all__ = [
    "auth_router",
    "clusters_router",
    "contours_router",
    "diagnostics_router",
    "maintenance_router",
    "nodes_router",
    "recovery_router",
    "settings_router",
    "ws_router",
]