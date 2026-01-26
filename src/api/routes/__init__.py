"""API route modules."""

from .agents import router as agents_router
from .deals import router as deals_router
from .documents import router as documents_router
from .fair import router as fair_router
from .synthesis import router as synthesis_router

__all__ = [
    "deals_router",
    "documents_router",
    "agents_router",
    "fair_router",
    "synthesis_router",
]
