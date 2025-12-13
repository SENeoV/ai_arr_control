from typing import Any

from core.logging import logger


class IndexerControlAgent:
    """Provides primitive control actions for indexers (disable/enable).

    This class intentionally keeps logic small; it delegates API calls to
    the provided service wrapper (Radarr/Sonarr).
    """

    def __init__(self, radarr: Any, sonarr: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr

    async def disable_indexer(self, service: Any, indexer: dict) -> None:
        """Disable an indexer via the service API and log the action."""
        indexer = dict(indexer)
        indexer["enable"] = False
        # prefer calling service wrapper if available
        if hasattr(service, "update_indexer"):
            await service.update_indexer(indexer)
        else:
            await service.client.put(f"/api/v3/indexer/{indexer['id']}", json=indexer)

        logger.warning("Disabled indexer: %s", indexer.get("name"))
