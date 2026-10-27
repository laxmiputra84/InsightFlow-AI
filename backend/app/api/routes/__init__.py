from .health import router as health_router
from .dashboard import router as dashboard_router
from .agents import router as agents_router
from .analytics import router as analytics_router
from .documents import router as documents_router
from .rag import router as rag_router
from .forecast import router as forecast_router
from .reports import router as reports_router
from .datasets import router as datasets_router

__all__ = [
    "health_router",
    "dashboard_router",
    "agents_router",
    "analytics_router",
    "documents_router",
    "rag_router",
    "forecast_router",
    "reports_router",
    "datasets_router",
]
