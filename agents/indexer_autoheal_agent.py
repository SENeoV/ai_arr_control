from core.logging import logger
from db.session import SessionLocal
from db.models import IndexerHealth

class IndexerAutoHealAgent:
    def __init__(self, radarr, sonarr, control_agent):
        self.radarr = radarr
        self.sonarr = sonarr
        self.control = control_agent

    async def run(self):
        logger.info("Autoheal cycle started")
        async with SessionLocal() as session:
            for service_name, service in [("radarr", self.radarr), ("sonarr", self.sonarr)]:
                for idx in await service.get_indexers():
                    try:
                        await service.test_indexer(idx["id"])
                        session.add(IndexerHealth(
                            service=service_name,
                            indexer_id=idx["id"],
                            name=idx["name"],
                            success=True,
                            error=None,
                        ))
                    except Exception as e:
                        session.add(IndexerHealth(
                            service=service_name,
                            indexer_id=idx["id"],
                            name=idx["name"],
                            success=False,
                            error=str(e),
                        ))
                        await self.control.disable_indexer(service, idx)
            await session.commit()
