from typing import AsyncGenerator, Optional

from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from core.http import ArrHttpClient
from services.radarr import RadarrService
from services.sonarr import SonarrService
from services.prowlarr import ProwlarrService
from agents.indexer_health_agent import IndexerHealthAgent
from agents.indexer_control_agent import IndexerControlAgent
from agents.indexer_autoheal_agent import IndexerAutoHealAgent
from db.session import init_db


def _create_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    return sched


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application startup and shutdown events.

    This function handles:
    - Database initialization
    - Service instantiation
    - Scheduler creation and startup
    - Resource cleanup on shutdown
    """
    # Startup
    await init_db()

    # create HTTP clients and services
    radarr_client = ArrHttpClient(settings.radarr_url, settings.radarr_api_key)
    sonarr_client = ArrHttpClient(settings.sonarr_url, settings.sonarr_api_key)
    prowlarr_client = ArrHttpClient(settings.prowlarr_url, settings.prowlarr_api_key)

    radarr = RadarrService(radarr_client)
    sonarr = SonarrService(sonarr_client)
    prowlarr = ProwlarrService(prowlarr_client)

    # store on app.state for later use / tests
    app.state.radarr = radarr
    app.state.sonarr = sonarr
    app.state.prowlarr = prowlarr

    # agents
    health_agent = IndexerHealthAgent(radarr, sonarr)
    control_agent = IndexerControlAgent(radarr, sonarr)
    autoheal_agent = IndexerAutoHealAgent(radarr, sonarr, control_agent)

    # scheduler
    scheduler: AsyncIOScheduler = _create_scheduler()
    scheduler.add_job(health_agent.run, "interval", minutes=30, id="health_agent")
    scheduler.add_job(autoheal_agent.run, "interval", hours=2, id="autoheal_agent")
    scheduler.start()

    app.state.scheduler = scheduler

    yield

    # Shutdown
    scheduler: Optional[AsyncIOScheduler] = getattr(app.state, "scheduler", None)
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            # scheduler shutdown should not crash the app
            pass

    # close HTTP clients if present
    for svc_name in ("radarr", "sonarr", "prowlarr"):
        svc = getattr(app.state, svc_name, None)
        if svc and getattr(svc, "client", None):
            try:
                await svc.client.close()
            except Exception:
                pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
