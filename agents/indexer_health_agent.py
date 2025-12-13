"""Indexer health checking agent.

Performs periodic health checks against Radarr and Sonarr indexers.
This agent is read-only and only logs results without making changes.
"""

from typing import Any
from loguru import logger


class IndexerHealthAgent:
    """Agent that performs periodic health checks against indexers.
    
    This agent:
    - Fetches all indexers from Radarr and Sonarr
    - Tests each indexer's connectivity
    - Logs results without making any changes
    - Runs periodically (e.g., every 30 minutes) for monitoring
    
    This is a read-only agent suitable for health monitoring dashboards
    and alerting systems. Actual remediation is handled by IndexerAutoHealAgent.
    
    Args:
        radarr: RadarrService instance
        sonarr: SonarrService instance
    """

    def __init__(self, radarr: Any, sonarr: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr
        logger.info("Initialized IndexerHealthAgent")

    async def run(self) -> None:
        """Run health checks for Radarr and Sonarr indexers and log results.
        
        Iterates through all configured indexers in both services,
        attempts to test connectivity, and logs the results.
        Failures are logged but do not cause the agent to fail.
        """
        logger.info("Starting health check cycle")
        
        radarr_success = await self._check_service("Radarr", self.radarr)
        sonarr_success = await self._check_service("Sonarr", self.sonarr)
        
        if radarr_success and sonarr_success:
            logger.info("Health check cycle completed successfully")
        else:
            logger.warning("Health check cycle completed with some failures")

    async def _check_service(self, service_name: str, service: Any) -> bool:
        """Check health of all indexers in a service.
        
        Args:
            service_name: Display name of the service (e.g., "Radarr")
            service: Service instance with get_indexers() and test_indexer() methods
            
        Returns:
            True if all indexers were checked (regardless of result),
            False if the service itself failed to respond
        """
        logger.info(f"Checking {service_name} indexers")
        
        try:
            indexers = await service.get_indexers()
        except Exception as e:
            logger.error(f"Failed to fetch {service_name} indexers: {e}")
            return False

        logger.debug(f"Testing {len(indexers)} {service_name} indexers")
        success_count = 0
        fail_count = 0
        
        for idx in indexers:
            indexer_id = idx.get("id")
            indexer_name = idx.get("name", f"unknown (id={indexer_id})")
            
            try:
                await service.test_indexer(indexer_id)
                logger.info(f"{service_name} indexer '{indexer_name}' OK")
                success_count += 1
            except Exception as e:
                logger.warning(f"{service_name} indexer '{indexer_name}' FAILED: {str(e)[:100]}")
                fail_count += 1

        logger.info(f"{service_name} health check: {success_count} passed, {fail_count} failed")
        return True
