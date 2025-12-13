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

app = FastAPI(title=settings.app_name)
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    await init_db()

    radarr = RadarrService(ArrHttpClient(settings.radarr_url, settings.radarr_api_key))
    sonarr = SonarrService(ArrHttpClient(settings.sonarr_url, settings.sonarr_api_key))
    prowlarr = ProwlarrService(ArrHttpClient(settings.prowlarr_url, settings.prowlarr_api_key))

    health_agent = IndexerHealthAgent(radarr, sonarr)
    control_agent = IndexerControlAgent(radarr, sonarr)
    autoheal_agent = IndexerAutoHealAgent(radarr, sonarr, control_agent)

    scheduler.add_job(health_agent.run, "interval", minutes=30)
    scheduler.add_job(autoheal_agent.run, "interval", hours=2)
    scheduler.start()

@app.get("/health")
def health():
    return {"status": "ok"}
