import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.settings import settings
from core.http import ArrHttpClient
from services.radarr import RadarrService
from services.sonarr import SonarrService
from agents.indexer_health_agent import IndexerHealthAgent

app = FastAPI(title=settings.app_name)
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    radarr_client = ArrHttpClient(settings.radarr_url, settings.radarr_api_key)
    sonarr_client = ArrHttpClient(settings.sonarr_url, settings.sonarr_api_key)
    radarr = RadarrService(radarr_client)
    sonarr = SonarrService(sonarr_client)
    agent = IndexerHealthAgent(radarr, sonarr)
    scheduler.add_job(agent.run, "interval", minutes=30)
    scheduler.start()

@app.get("/health")
def health():
    return {"status": "ok"}
