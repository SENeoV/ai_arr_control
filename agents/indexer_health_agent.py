from core.logging import logger

class IndexerHealthAgent:
    def __init__(self, radarr, sonarr):
        self.radarr = radarr
        self.sonarr = sonarr

    async def run(self):
        for idx in await self.radarr.get_indexers():
            try:
                await self.radarr.test_indexer(idx["id"])
                logger.info(f"Radarr OK: {idx['name']}")
            except Exception as e:
                logger.error(f"Radarr FAIL: {idx['name']} -> {e}")
