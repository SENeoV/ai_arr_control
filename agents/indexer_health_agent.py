from core.logging import logger

class IndexerHealthAgent:
    def __init__(self, radarr, sonarr):
        self.radarr = radarr
        self.sonarr = sonarr

    async def run(self):
        logger.info("Checking Radarr indexers")
        radarr_indexers = await self.radarr.get_indexers()
        for idx in radarr_indexers:
            try:
                await self.radarr.test_indexer(idx["id"])
                logger.info(f"Radarr indexer OK: {idx['name']}")
            except Exception as e:
                logger.error(f"Radarr indexer FAIL: {idx['name']} -> {e}")

        logger.info("Checking Sonarr indexers")
        sonarr_indexers = await self.sonarr.get_indexers()
        for idx in sonarr_indexers:
            try:
                await self.sonarr.test_indexer(idx["id"])
                logger.info(f"Sonarr indexer OK: {idx['name']}")
            except Exception as e:
                logger.error(f"Sonarr indexer FAIL: {idx['name']} -> {e}")