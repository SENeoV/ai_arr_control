"""Indexer control agent for indexer state manipulation.

Provides low-level control primitives for enabling and disabling indexers.
This agent is used by the autoheal agent to remediate failing indexers.
"""

from typing import Any
from loguru import logger


class IndexerControlAgent:
    """Provides primitive control actions for indexers (disable/enable).
    
    This agent intentionally keeps logic small and delegates API calls to
    the provided service wrappers (Radarr/Sonarr).
    
    Typical usage: Called by IndexerAutoHealAgent when an indexer fails
    health checks and needs to be disabled.
    
    Args:
        radarr: RadarrService instance
        sonarr: SonarrService instance
    """

    def __init__(self, radarr: Any, sonarr: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr
        logger.info("Initialized IndexerControlAgent")

    async def disable_indexer(self, service: Any, indexer: dict) -> None:
        """Disable an indexer via the service API and log the action.
        
        Creates a copy of the indexer dict, sets enable=False, and sends
        an update request to the service API.
        
        Args:
            service: Service instance (RadarrService or SonarrService)
            indexer: Indexer dictionary (as returned by get_indexers)
            
        Raises:
            httpx.HTTPStatusError: If the update request fails
        """
        indexer_copy = dict(indexer)
        indexer_copy["enable"] = False
        indexer_id = indexer_copy.get("id")
        indexer_name = indexer_copy.get("name", f"unknown (id={indexer_id})")
        
        try:
            # Prefer calling service wrapper if available
            if hasattr(service, "update_indexer"):
                await service.update_indexer(indexer_copy)
            else:
                # Fallback to direct HTTP call
                await service.client.put(
                    f"/api/v3/indexer/{indexer_id}",
                    json=indexer_copy
                )
            logger.warning(f"Disabled indexer: {indexer_name}")
        except Exception as e:
            logger.error(f"Failed to disable indexer {indexer_name}: {e}")
            raise

    async def enable_indexer(self, service: Any, indexer: dict) -> None:
        """Enable an indexer via the service API and log the action.
        
        Creates a copy of the indexer dict, sets enable=True, and sends
        an update request to the service API.
        
        Args:
            service: Service instance (RadarrService or SonarrService)
            indexer: Indexer dictionary (as returned by get_indexers)
            
        Raises:
            httpx.HTTPStatusError: If the update request fails
        """
        indexer_copy = dict(indexer)
        indexer_copy["enable"] = True
        indexer_id = indexer_copy.get("id")
        indexer_name = indexer_copy.get("name", f"unknown (id={indexer_id})")
        
        try:
            # Prefer calling service wrapper if available
            if hasattr(service, "update_indexer"):
                await service.update_indexer(indexer_copy)
            else:
                # Fallback to direct HTTP call
                await service.client.put(
                    f"/api/v3/indexer/{indexer_id}",
                    json=indexer_copy
                )
            logger.info(f"Enabled indexer: {indexer_name}")
        except Exception as e:
            logger.error(f"Failed to enable indexer {indexer_name}: {e}")
            raise
