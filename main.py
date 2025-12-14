"""AI Arr Control - Autonomous indexer management and health monitoring.

Main application entry point. Initializes FastAPI application with:
- Async lifecycle management
- Database initialization
- Service and agent instantiation
- Scheduler for periodic health checks and autoheal cycles
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.logging import configure_debug_logging
from core.http import ArrHttpClient
from services.radarr import RadarrService
from services.sonarr import SonarrService
from services.prowlarr import ProwlarrService
from agents.indexer_health_agent import IndexerHealthAgent
from agents.indexer_control_agent import IndexerControlAgent
from agents.indexer_autoheal_agent import IndexerAutoHealAgent
from agents.indexer_discovery_agent import IndexerDiscoveryAgent
from agents.orchestrator import AgentOrchestrator
from agents.monitor import AgentMonitor, EventType
from db.session import init_db, close_db, SessionLocal
from db.models import IndexerHealth
from api.schemas import (
    HealthResponse,
    ServiceInfoResponse,
    ServiceIndexersResponse,
    TestIndexerResponse,
    IndexerActionResponse,
    IndexerStatsResponse,
    IndexerStatsItem,
    AgentRunResponse,
    HealthHistoryResponse,
    DetailedStatsResponse,
    AgentStatusResponse,
)
from core.monitoring import metrics_collector, event_log, startup_status


# Get current UTC time in a timezone-aware manner
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


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
    discovery_agent = IndexerDiscoveryAgent(prowlarr if settings.discovery_add_to_prowlarr else None)
    
    # Attach agents to app.state for endpoint access and tests
    app.state.health_agent = health_agent
    app.state.control_agent = control_agent
    app.state.autoheal_agent = autoheal_agent
    app.state.discovery_agent = discovery_agent

    # Create and initialize orchestrator with all agents
    logger.info("Initializing agent orchestrator")
    orchestrator = AgentOrchestrator(name="IndexerControlOrchestrator")
    monitor = AgentMonitor(max_event_history=5000)
    
    # Register agents with orchestrator and schedules
    orchestrator.register_agent(health_agent, interval_seconds=30 * 60)  # 30 minutes
    orchestrator.register_agent(autoheal_agent, interval_seconds=2 * 60 * 60)  # 2 hours
    orchestrator.register_agent(control_agent)  # On-demand only
    
    if settings.discovery_enabled:
        orchestrator.register_agent(
            discovery_agent,
            interval_seconds=settings.discovery_interval_hours * 60 * 60,
        )
    
    app.state.orchestrator = orchestrator
    app.state.monitor = monitor
    
    # Create and configure legacy scheduler for backwards compatibility
    logger.info("Initializing scheduler (legacy compatibility)")
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
    # Schedule discovery agent if enabled
    if settings.discovery_enabled:
        scheduler.add_job(
            discovery_agent.run,
            "interval",
            hours=settings.discovery_interval_hours,
            id="discovery_agent",
            name="Indexer Discovery",
            coalesce=True,
            max_instances=1,
        )
    scheduler.start()
    logger.info("Scheduler started with jobs configured")

    app.state.scheduler = scheduler
    
    # Mark startup as starting
    startup_status.mark_startup_start()
    
    # Run initial health check immediately on startup for professional responsiveness
    logger.info("Running initial health check on startup...")
    try:
        await health_agent.run()
        startup_status.mark_agent_run("health_check")
        logger.info("Initial health check completed")
    except Exception as e:
        startup_status.record_startup_error("health_check", str(e))
        logger.warning(f"Initial health check failed: {e}")
    
    # Run initial autoheal check to identify and remediate problems immediately
    logger.info("Running initial autoheal cycle on startup...")
    try:
        await autoheal_agent.run()
        startup_status.mark_agent_run("autoheal")
        logger.info("Initial autoheal cycle completed")
    except Exception as e:
        startup_status.record_startup_error("autoheal", str(e))
        logger.warning(f"Initial autoheal cycle failed: {e}")
    
    # Run discovery if enabled
    if settings.discovery_enabled:
        logger.info("Running initial discovery on startup...")
        try:
            await discovery_agent.run()
            startup_status.mark_agent_run("discovery")
            logger.info("Initial discovery completed")
        except Exception as e:
            startup_status.record_startup_error("discovery", str(e))
            logger.warning(f"Initial discovery failed: {e}")
    
    # Mark startup as complete
    startup_status.mark_startup_complete()
    logger.info(f"{settings.app_name} startup completed successfully - all agents initialized and first run complete")

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
async def health() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        Simple status indicator for monitoring and load balancer health checks
    """
    return HealthResponse(status="ok", service=settings.app_name)


@app.get("/", tags=["info"])
async def root() -> ServiceInfoResponse:
    """Root endpoint with basic service information.
    
    Returns:
        Service metadata and available endpoints
    """
    return ServiceInfoResponse(
        service=settings.app_name,
        version="0.4.0",
        description="AI-powered autonomous indexer management and health monitoring",
        endpoints={
            "monitoring": {
                "health": "/health",
                "stats": "/indexers/stats",
                "detailed_stats": "/stats/detailed",
                "health_history": "/health-history",
                "agent_status": "/agents/status",
                "startup_status": "/startup-status"
            },
            "indexers": {
                "list_all": "/indexers",
                "list_by_service": "/indexers/{service}",
                "test_indexer": "POST /indexers/{service}/{indexer_id}/test",
                "disable_indexer": "POST /indexers/{service}/{indexer_id}/disable",
                "enable_indexer": "POST /indexers/{service}/{indexer_id}/enable"
            },
            "agents": {
                "run_health_check": "POST /agents/health/run",
                "run_autoheal": "POST /agents/autoheal/run",
                "run_discovery": "POST /agents/discovery/run"
            },
            "docs": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            }
        }
    )


@app.get("/indexers", tags=["indexers"])
async def get_indexers() -> dict:
    """Get all indexers from Radarr and Sonarr with their details.
    
    Returns:
        Dictionary with indexer information grouped by service
    """
    logger.debug("Fetching indexers from all services")
    
    indexers = {
        "radarr": [],
        "sonarr": [],
        "prowlarr": [],
    }
    
    try:
        radarr_service = app.state.radarr
        indexers["radarr"] = await radarr_service.get_indexers()
    except Exception as e:
        logger.error(f"Error fetching Radarr indexers: {e}")
        indexers["radarr_error"] = str(e)
    
    try:
        sonarr_service = app.state.sonarr
        indexers["sonarr"] = await sonarr_service.get_indexers()
    except Exception as e:
        logger.error(f"Error fetching Sonarr indexers: {e}")
        indexers["sonarr_error"] = str(e)
    
    try:
        prowlarr_service = app.state.prowlarr
        indexers["prowlarr"] = await prowlarr_service.get_indexers()
    except Exception as e:
        logger.error(f"Error fetching Prowlarr indexers: {e}")
        indexers["prowlarr_error"] = str(e)
    
    return indexers


@app.get("/indexers/stats", tags=["indexers"])
async def get_indexers_stats() -> dict:
    """Get statistics about all indexers across all services.
    
    Returns:
        Statistics including total count, online/offline breakdown by service
    """
    logger.debug("Computing indexer statistics")
    
    stats = {
        "timestamp": None,
        "total": 0,
        "by_service": {},
    }
    
    services = {
        "radarr": app.state.radarr,
        "sonarr": app.state.sonarr,
        "prowlarr": app.state.prowlarr,
    }
    
    for service_name, service in services.items():
        try:
            indexers = await service.get_indexers()
            enabled = sum(1 for idx in indexers if idx.get("enable", True))
            disabled = len(indexers) - enabled
            
            stats["by_service"][service_name] = {
                "total": len(indexers),
                "enabled": enabled,
                "disabled": disabled,
                "indexers": [
                    {
                        "id": idx.get("id"),
                        "name": idx.get("name"),
                        "enabled": idx.get("enable", True),
                    }
                    for idx in indexers
                ],
            }
            stats["total"] += len(indexers)
        except Exception as e:
            logger.error(f"Error fetching {service_name} stats: {e}")
            stats["by_service"][service_name] = {"error": str(e)}
    
    return stats


@app.get("/indexers/{service}", tags=["indexers"])
async def get_service_indexers(service: str) -> dict:
    """Get all indexers from a specific service with detailed information.
    
    Args:
        service: Service name (radarr, sonarr, or prowlarr)
        
    Returns:
        Detailed indexer information
    """
    if service not in ("radarr", "sonarr", "prowlarr"):
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    
    try:
        svc = getattr(app.state, service)
        indexers = await svc.get_indexers()
        logger.info(f"Retrieved {len(indexers)} indexers from {service}")
        return {
            "service": service,
            "count": len(indexers),
            "indexers": indexers
        }
    except Exception as e:
        logger.error(f"Error fetching {service} indexers: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching {service} indexers: {str(e)}")


@app.post("/indexers/{service}/{indexer_id}/test", tags=["indexers"])
async def test_indexer(service: str, indexer_id: int) -> TestIndexerResponse:
    """Test a specific indexer's connectivity.
    
    Args:
        service: Service name (radarr, sonarr)
        indexer_id: ID of the indexer to test
        
    Returns:
        Test result with success status and any error message
    """
    if service not in ("radarr", "sonarr"):
        raise HTTPException(status_code=400, detail=f"Cannot test indexers on {service}")
    
    try:
        svc, _ = await _get_and_validate_indexer(service, indexer_id)
        await svc.test_indexer(indexer_id)
        logger.info(f"Successfully tested indexer {indexer_id} on {service}")
        return TestIndexerResponse(success=True, service=service, indexer_id=indexer_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to test indexer {indexer_id} on {service}: {e}")
        return TestIndexerResponse(
            success=False,
            service=service,
            indexer_id=indexer_id,
            error=str(e)
        )


async def _get_and_validate_indexer(service_name: str, indexer_id: int) -> tuple:
    """Helper to validate service and get indexer object.
    
    Args:
        service_name: Service name (radarr, sonarr, prowlarr)
        indexer_id: ID of the indexer
        
    Returns:
        Tuple of (service, indexer_dict)
        
    Raises:
        HTTPException: If service invalid or indexer not found
    """
    if service_name not in ("radarr", "sonarr", "prowlarr"):
        raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
    
    try:
        svc = getattr(app.state, service_name)
        indexers = await svc.get_indexers()
        indexer = next((i for i in indexers if i.get("id") == indexer_id), None)
        if not indexer:
            raise HTTPException(
                status_code=404,
                detail=f"Indexer {indexer_id} not found on {service_name}"
            )
        return svc, indexer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching indexers from {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching {service_name} indexers: {str(e)}")


@app.post("/indexers/{service}/{indexer_id}/disable", tags=["indexers"])
async def disable_indexer(service: str, indexer_id: int) -> IndexerActionResponse:
    """Disable a specific indexer.
    
    Args:
        service: Service name (radarr or sonarr)
        indexer_id: ID of the indexer to disable
        
    Returns:
        Result of disable operation
    """
    if service not in ("radarr", "sonarr"):
        raise HTTPException(status_code=400, detail="Indexer management only supported for radarr and sonarr")
    
    try:
        svc, indexer = await _get_and_validate_indexer(service, indexer_id)
        control_agent = app.state.control_agent
        await control_agent.disable_indexer(svc, indexer)
        logger.info(f"Disabled indexer {indexer_id} on {service}")
        return IndexerActionResponse(
            success=True,
            service=service,
            indexer_id=indexer_id,
            action="disabled"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling indexer {indexer_id} on {service}: {e}")
        raise HTTPException(status_code=500, detail=f"Error disabling indexer: {str(e)}")


@app.post("/indexers/{service}/{indexer_id}/enable", tags=["indexers"])
async def enable_indexer(service: str, indexer_id: int) -> IndexerActionResponse:
    """Enable a specific indexer.
    
    Args:
        service: Service name (radarr or sonarr)
        indexer_id: ID of the indexer to enable
        
    Returns:
        Result of enable operation
    """
    if service not in ("radarr", "sonarr"):
        raise HTTPException(status_code=400, detail="Indexer management only supported for radarr and sonarr")
    
    try:
        svc, indexer = await _get_and_validate_indexer(service, indexer_id)
        control_agent = app.state.control_agent
        await control_agent.enable_indexer(svc, indexer)
        logger.info(f"Enabled indexer {indexer_id} on {service}")
        return IndexerActionResponse(
            success=True,
            service=service,
            indexer_id=indexer_id,
            action="enabled"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling indexer {indexer_id} on {service}: {e}")
        raise HTTPException(status_code=500, detail=f"Error enabling indexer: {str(e)}")


@app.post("/agents/health/run", tags=["agents"])
async def run_health_agent() -> AgentRunResponse:
    """Manually trigger the health check agent to run immediately.
    
    Returns:
        Status of the health check run
    """
    try:
        health_agent = app.state.health_agent
        logger.info("Manually triggering health agent")
        await health_agent.run()
        return AgentRunResponse(
            success=True,
            agent="health_agent",
            message="Health check completed"
        )
    except Exception as e:
        logger.error(f"Error running health agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error running health agent: {str(e)}")


@app.post("/agents/autoheal/run", tags=["agents"])
async def run_autoheal_agent() -> AgentRunResponse:
    """Manually trigger the autoheal agent to run immediately.
    
    Returns:
        Status of the autoheal run
    """
    try:
        autoheal_agent = app.state.autoheal_agent
        logger.info("Manually triggering autoheal agent")
        await autoheal_agent.run()
        return AgentRunResponse(
            success=True,
            agent="autoheal_agent",
            message="Autoheal completed"
        )
    except Exception as e:
        logger.error(f"Error running autoheal agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error running autoheal agent: {str(e)}")


@app.post("/agents/discovery/run", tags=["agents"])
async def run_discovery_agent() -> AgentRunResponse:
    """Manually trigger the discovery agent to run immediately."""
    try:
        discovery_agent = app.state.discovery_agent
        logger.info("Manually triggering discovery agent")
        await discovery_agent.run()
        return AgentRunResponse(
            success=True,
            agent="discovery_agent",
            message="Discovery run completed"
        )
    except Exception as e:
        logger.error(f"Error running discovery agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error running discovery agent: {str(e)}")


@app.get("/health-history", tags=["monitoring"])
async def get_health_history(hours: int = 24, limit: int = 100) -> dict:
    """Get health check history from the database.
    
    Args:
        hours: Number of hours of history to retrieve (default 24)
        limit: Maximum number of records to return (default 100)
        
    Returns:
        Health records grouped by service
    """
    try:
        async with SessionLocal() as session:
            # Calculate time range
            cutoff_time = utc_now() - timedelta(hours=hours)
            
            # Query health records
            stmt = (
                select(IndexerHealth)
                .where(IndexerHealth.timestamp >= cutoff_time)
                .order_by(desc(IndexerHealth.timestamp))
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            # Group by service
            history = {
                "radarr": [],
                "sonarr": [],
                "prowlarr": [],
            }
            
            for record in records:
                history[record.service].append({
                    "id": record.id,
                    "indexer_id": record.indexer_id,
                    "name": record.name,
                    "success": record.success,
                    "error": record.error,
                    "timestamp": record.timestamp.isoformat(),
                })
            
            logger.debug(f"Retrieved {len(records)} health records from last {hours} hours")
            
            return {
                "hours": hours,
                "records_returned": len(records),
                "query_time": utc_now().isoformat(),
                "history": history
            }
    except Exception as e:
        logger.error(f"Error fetching health history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching health history: {str(e)}")


@app.get("/stats/detailed", tags=["monitoring"])
async def get_detailed_stats() -> dict:
    """Get detailed statistics including health trends and success rates.
    
    Returns:
        Comprehensive statistics including:
        - Total indexers by service
        - Health check success rates
        - Disabled indexers and reasons
        - Recent failures
    """
    try:
        async with SessionLocal() as session:
            # Get last 7 days of data
            cutoff_time = utc_now() - timedelta(days=7)
            
            stmt = (
                select(IndexerHealth)
                .where(IndexerHealth.timestamp >= cutoff_time)
                .order_by(desc(IndexerHealth.timestamp))
            )
            
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            # Calculate stats by service
            services = {
                "radarr": app.state.radarr,
                "sonarr": app.state.sonarr,
                "prowlarr": app.state.prowlarr,
            }
            
            detailed_stats = {
                "generated_at": utc_now().isoformat(),
                "total_records": len(records),
                "by_service": {}
            }
            
            for service_name, service in services.items():
                try:
                    indexers = await service.get_indexers()
                    service_records = [r for r in records if r.service == service_name]
                    
                    # Calculate success rate
                    successful = sum(1 for r in service_records if r.success)
                    total_checks = len(service_records) if service_records else 1
                    success_rate = (successful / total_checks * 100) if total_checks > 0 else 0
                    
                    # Find recent failures
                    failures = [
                        {
                            "indexer_id": r.indexer_id,
                            "name": r.name,
                            "error": r.error,
                            "timestamp": r.timestamp.isoformat()
                        }
                        for r in service_records if not r.success
                    ][:10]  # Last 10 failures
                    
                    enabled_count = sum(1 for idx in indexers if idx.get("enable", True))
                    disabled_count = len(indexers) - enabled_count
                    
                    detailed_stats["by_service"][service_name] = {
                        "total_indexers": len(indexers),
                        "enabled": enabled_count,
                        "disabled": disabled_count,
                        "health_checks": {
                            "total": total_checks,
                            "successful": successful,
                            "failed": total_checks - successful,
                            "success_rate_percent": round(success_rate, 2)
                        },
                        "recent_failures": failures,
                    }
                except Exception as e:
                    logger.error(f"Error computing stats for {service_name}: {e}")
                    detailed_stats["by_service"][service_name] = {"error": str(e)}
            
            return detailed_stats
    except Exception as e:
        logger.error(f"Error computing detailed stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error computing stats: {str(e)}")


@app.get("/agents/status", tags=["agents"])
async def get_agents_status() -> AgentStatusResponse:
    """Get status of all agents and scheduler.
    
    Returns:
        Current agent and scheduler status
    """
    try:
        scheduler = app.state.scheduler
        
        jobs = []
        if scheduler.running:
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                })
        
        return AgentStatusResponse(
            scheduler={
                "running": scheduler.running,
                "jobs_count": len(jobs),
                "jobs": jobs
            },
            agents={
                "health_agent": "active",
                "control_agent": "active",
                "autoheal_agent": "active"
            }
        )
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting agent status: {str(e)}")


@app.get("/metrics", tags=["monitoring"])
async def get_metrics() -> dict:
    """Get application metrics and health indicators.
    
    Returns:
        Current metrics including uptime, operation counts, and success rates
    """
    return metrics_collector.get_metrics()


@app.get("/events", tags=["monitoring"])
async def get_recent_events(limit: int = 50) -> dict:
    """Get recent system events from audit log.
    
    Args:
        limit: Maximum number of events to return
        
    Returns:
        Recent events from the event log
    """
    events = event_log.get_recent_events(limit=limit)
    return {
        "timestamp": utc_now().isoformat(),
        "events_count": len(events),
        "events": events
    }


@app.get("/startup-status", tags=["monitoring"])
async def get_startup_status() -> dict:
    """Get application startup status and initialization progress.
    
    Returns:
        Startup status including completion state, agent initialization, and any errors
    """
    return startup_status.get_status()

@app.get("/orchestrator/status", tags=["orchestrator"])
async def get_orchestrator_status() -> dict:
    """Get comprehensive orchestrator status and metrics.
    
    Returns:
        Orchestrator status including:
        - Running state
        - All registered agents and their status
        - Schedule information
        - Performance metrics
    """
    try:
        orchestrator = app.state.orchestrator
        return orchestrator.get_status()
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting orchestrator status: {str(e)}")


@app.get("/monitor/health", tags=["orchestrator"])
async def get_monitor_health() -> dict:
    """Get agent health monitoring status.
    
    Returns:
        Comprehensive health status including:
        - Overall health percentage
        - Individual agent health status
        - Consecutive failure counts
        - Recent events
    """
    try:
        monitor = app.state.monitor
        return monitor.get_status_summary()
    except Exception as e:
        logger.error(f"Error getting monitor health: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting monitor health: {str(e)}")


@app.get("/monitor/events", tags=["orchestrator"])
async def get_monitor_events(
    agent_name: Optional[str] = None,
    limit: int = 50
) -> dict:
    """Query monitored events with optional filtering.
    
    Args:
        agent_name: Optional filter by agent name
        limit: Maximum events to return
        
    Returns:
        List of events matching the query criteria
    """
    try:
        monitor = app.state.monitor
        events = monitor.get_events(agent_name=agent_name, limit=limit)
        return {
            "count": len(events),
            "agent_filter": agent_name,
            "events": [
                {
                    "type": e.event_type.value,
                    "agent": e.agent_name,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata,
                }
                for e in events
            ]
        }
    except Exception as e:
        logger.error(f"Error getting monitor events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting monitor events: {str(e)}")


@app.post("/orchestrator/agent/{agent_name}/run", tags=["orchestrator"])
async def trigger_agent_on_demand(agent_name: str) -> dict:
    """Trigger a registered agent to run on-demand.
    
    Args:
        agent_name: Name of the agent to execute
        
    Returns:
        Execution result with success status and metrics
    """
    try:
        orchestrator = app.state.orchestrator
        monitor = app.state.monitor
        
        logger.info(f"Triggering on-demand execution of agent: {agent_name}")
        
        result = await orchestrator.execute_agent(agent_name)
        
        if result:
            # Record event in monitor
            monitor.record_event(
                EventType.AGENT_COMPLETED if result.success else EventType.AGENT_FAILED,
                agent_name=agent_name,
                message=result.message,
                metadata=result.metrics or {},
            )
            
            # Update health status
            monitor.update_agent_health(agent_name, success=result.success, error=result.error)
            
            return {
                "agent": agent_name,
                "success": result.success,
                "message": result.message,
                "metrics": result.metrics or {},
                "error": result.error,
                "timestamp": result.timestamp.isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found or already running")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering agent: {str(e)}")


@app.post("/orchestrator/agent/{agent_name}/enable", tags=["orchestrator"])
async def enable_agent_endpoint(agent_name: str) -> dict:
    """Enable a registered agent.
    
    Args:
        agent_name: Name of the agent to enable
        
    Returns:
        Success status
    """
    try:
        orchestrator = app.state.orchestrator
        if orchestrator.enable_agent(agent_name):
            return {"agent": agent_name, "enabled": True}
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error enabling agent: {str(e)}")


@app.post("/orchestrator/agent/{agent_name}/disable", tags=["orchestrator"])
async def disable_agent_endpoint(agent_name: str) -> dict:
    """Disable a registered agent.
    
    Args:
        agent_name: Name of the agent to disable
        
    Returns:
        Success status
    """
    try:
        orchestrator = app.state.orchestrator
        if orchestrator.disable_agent(agent_name):
            return {"agent": agent_name, "enabled": False}
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error disabling agent: {str(e)}")