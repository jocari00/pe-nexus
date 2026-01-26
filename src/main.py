"""FastAPI application entrypoint for PE-Nexus."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import agents_router, deals_router, documents_router, fair_router, synthesis_router
from src.core.config import settings
from src.core.events import init_event_bus, shutdown_event_bus
from src.db.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting PE-Nexus...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start event bus
    await init_event_bus()
    logger.info("Event bus started")

    yield

    # Shutdown
    logger.info("Shutting down PE-Nexus...")
    await shutdown_event_bus()
    logger.info("Event bus stopped")


# Create FastAPI application
app = FastAPI(
    title="PE-Nexus",
    description="""
    Full-Lifecycle Private Equity Deal Orchestrator

    PE-Nexus is a multi-agent autonomous system for private equity deal management,
    spanning from sourcing through exit. It provides:

    - **Deal Management**: Track deals through the full pipeline from sourcing to exit
    - **Document Processing**: Upload and analyze CIMs, financial statements, and VDR documents
    - **Financial Extraction**: AI-powered extraction with full source traceability
    - **Agent Framework**: Specialized AI agents for each stage of the deal lifecycle

    ## Key Features

    - Every extracted value is traced to its source (page, bounding box)
    - State machine-based deal pipeline with validation
    - Event-driven architecture for agent coordination
    - Vector search for semantic document querying
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
# WARNING: Do not use allow_origins=["*"] with allow_credentials=True in production
# Configure specific origins via CORS_ORIGINS environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(deals_router)
app.include_router(documents_router)
app.include_router(agents_router)
app.include_router(fair_router)
app.include_router(synthesis_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PE-Nexus",
        "version": "0.1.0",
        "description": "Full-Lifecycle Private Equity Deal Orchestrator",
        "docs": "/docs",
        "endpoints": {
            "deals": "/deals",
            "documents": "/documents",
            "agents": "/agents",
            "fair": "/fair",
            "synthesis": "/synthesis",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": settings.database_url.split("///")[0] if "///" in settings.database_url else "configured",
        "vector_store": "chromadb",
        "llm_provider": settings.active_llm_provider or "none",
        "llm_model": settings.active_model_name,
        "llm_display_name": settings.llm_display_name,
    }


@app.get("/config")
async def get_config():
    """Get non-sensitive configuration info."""
    return {
        "app_name": settings.app_name,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "llm_provider": settings.active_llm_provider or "none",
        "llm_model": settings.active_model_name,
        "llm_display_name": settings.llm_display_name,
        "database_type": "sqlite" if settings.is_sqlite else "postgresql",
        "pdf_confidence_threshold": settings.pdf_extraction_confidence_threshold,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
