"""AI Arr Control - Autonomous indexer management and health monitoring.

Main application entry point. Initializes FastAPI application with:
- Async lifecycle management
- Database initialization
- Service and agent instantiation
- Scheduler for periodic health checks and autoheal cycles
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from config.settings import settings
from core.logging import configure_debug_logging
from core.http import ArrHttpClient
from services.radarr import RadarrService
from services.sonarr import SonarrService
from services.prowlarr import ProwlarrService
from agents.indexer_health_agent import IndexerHealthAgent
from agents.indexer_control_agent import IndexerControlAgent
from agents.indexer_autoheal_agent import IndexerAutoHealAgent
from db.session import init_db, close_db


def _create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler scheduler.
    
    Returns:
        Configured AsyncIOScheduler instance ready for job registration
    """
    sched = AsyncIOScheduler()
    return sched


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application startup and shutdown events.

    This context manager handles:
    - Configuration validation at startup
    - Debug logging configuration
    - Database initialization
    - Service instantiation (HTTP clients and service wrappers)
    - Agent creation
    - Scheduler creation and startup
    - Resource cleanup on shutdown
    
    All services and resources are attached to app.state for use
    by request handlers and during testing.
    """
    # Startup
    logger.info(f"Starting {settings.app_name}")
    
    # Configure logging based on debug setting
    if settings.debug:
        logger.info("Debug mode enabled")
        configure_debug_logging(enabled=True)
    
    # Validate configuration at startup
    try:
        settings.validate_at_startup()
    except Exception as e:
        logger.critical(f"Configuration validation failed: {e}")
        raise
    
    # Initialize database
    try:
        await init_db()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise

    # Create HTTP clients with API authentication
    logger.info("Initializing HTTP clients for Arr services")
    radarr_client = ArrHttpClient(settings.radarr_url, settings.radarr_api_key)
    sonarr_client = ArrHttpClient(settings.sonarr_url, settings.sonarr_api_key)
    prowlarr_client = ArrHttpClient(settings.prowlarr_url, settings.prowlarr_api_key)

    # Create service wrappers
    logger.info("Initializing service wrappers")
    radarr = RadarrService(radarr_client)
    sonarr = SonarrService(sonarr_client)
    prowlarr = ProwlarrService(prowlarr_client)

    # Store on app.state for later use by handlers and tests
    app.state.radarr = radarr
    app.state.sonarr = sonarr
    app.state.prowlarr = prowlarr

    # Create agents
    logger.info("Initializing autonomous agents")
    health_agent = IndexerHealthAgent(radarr, sonarr)
    control_agent = IndexerControlAgent(radarr, sonarr)
    autoheal_agent = IndexerAutoHealAgent(radarr, sonarr, control_agent)

    # Create and configure scheduler
    logger.info("Initializing scheduler")
    scheduler: AsyncIOScheduler = _create_scheduler()
    scheduler.add_job(
        health_agent.run,
        "interval",
        minutes=30,
        id="health_agent",
        name="Indexer Health Check (every 30 minutes)",
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        autoheal_agent.run,
        "interval",
        hours=2,
        id="autoheal_agent",
        name="Indexer Autoheal (every 2 hours)",
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started with jobs configured")

    app.state.scheduler = scheduler
    logger.info(f"{settings.app_name} startup completed successfully")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    
    scheduler_instance: Optional[AsyncIOScheduler] = getattr(app.state, "scheduler", None)
    if scheduler_instance:
        try:
            scheduler_instance.shutdown(wait=False)
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}")

    # Close HTTP clients if present
    for svc_name in ("radarr", "sonarr", "prowlarr"):
        svc = getattr(app.state, svc_name, None)
        if svc and getattr(svc, "client", None):
            try:
                await svc.client.close()
                logger.debug(f"Closed {svc_name} HTTP client")
            except Exception as e:
                logger.error(f"Error closing {svc_name} client: {e}")
    
    # Close database connection
    try:
        await close_db()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    logger.info(f"{settings.app_name} shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI agent platform for intelligent indexer management",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["monitoring"])
def health() -> dict:
    """Health check endpoint.
    
    Returns:
        Simple status indicator for monitoring and load balancer health checks
    """
    return {"status": "ok", "service": settings.app_name}


@app.get("/", tags=["info"])
def root() -> dict:
    """Root endpoint with basic service information.
    
    Returns:
        Service metadata and available endpoints
    """
    return {
        "service": settings.app_name,
        "version": "0.3.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }
