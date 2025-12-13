from typing import Any

from core.logging import logger


class IndexerHealthAgent:
    """Agent that performs periodic health checks against Radarr and Sonarr indexers."""

    def __init__(self, radarr: Any, sonarr: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr

    async def run(self) -> None:
        """Run health checks for Radarr and Sonarr indexers and log results."""
        logger.info("Checking Radarr indexers")
        try:
            radarr_indexers = await self.radarr.get_indexers()
        except Exception as e:
            logger.exception("Failed to fetch Radarr indexers: %s", e)
            radarr_indexers = []

        for idx in radarr_indexers:
            try:
                await self.radarr.test_indexer(idx["id"])
                logger.info("Radarr indexer OK: %s", idx.get("name"))
            except Exception:
                logger.exception("Radarr indexer FAIL: %s", idx.get("name"))

        logger.info("Checking Sonarr indexers")
        try:
            sonarr_indexers = await self.sonarr.get_indexers()
        except Exception as e:
            logger.exception("Failed to fetch Sonarr indexers: %s", e)
            sonarr_indexers = []

        for idx in sonarr_indexers:
            try:
                await self.sonarr.test_indexer(idx["id"])
                logger.info("Sonarr indexer OK: %s", idx.get("name"))
            except Exception:
                logger.exception("Sonarr indexer FAIL: %s", idx.get("name"))
