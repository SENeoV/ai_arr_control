from core.logging import logger

class IndexerControlAgent:
    def __init__(self, radarr, sonarr):
        self.radarr = radarr
        self.sonarr = sonarr

    async def disable_indexer(self, service, indexer):
        indexer["enable"] = False
        await service.client.put(f"/api/v3/indexer/{indexer['id']}", json=indexer)
        logger.warning(f"Disabled indexer: {indexer['name']}")
