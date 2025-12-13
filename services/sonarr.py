"""Sonarr service client for media indexer management.

Wraps Sonarr REST API endpoints for querying and managing indexers.
Sonarr is the TV show download management application in the Arr ecosystem.
"""

from typing import Any, List
from loguru import logger
from core.http import ArrHttpClient


class SonarrService:
    """Client wrapper for Sonarr HTTP API endpoints.
    
    Provides methods for:
    - Listing all configured indexers
    - Testing indexer connectivity
    - Updating indexer configuration (enable/disable, etc.)
    
    Args:
        client: Configured ArrHttpClient pointing to Sonarr instance
    """

    def __init__(self, client: ArrHttpClient) -> None:
        self.client = client
        logger.info("Initialized SonarrService")

    async def get_indexers(self) -> List[dict]:
        """Fetch list of all indexers configured in Sonarr.
        
        Returns:
            List of indexer dictionaries containing id, name, enable status, etc.
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.debug("Fetching Sonarr indexers")
        indexers = await self.client.get("/api/v3/indexer")
        logger.debug(f"Found {len(indexers)} Sonarr indexers")
        return indexers

    async def test_indexer(self, indexer_id: int) -> Any:
        """Test connectivity and functionality of a specific indexer.
        
        Sends a test request to the indexer to verify it's reachable
        and responding correctly.
        
        Args:
            indexer_id: ID of the indexer to test
            
        Returns:
            Response from Sonarr (typically success indicator)
            
        Raises:
            httpx.HTTPStatusError: If the test fails
        """
        logger.debug(f"Testing Sonarr indexer {indexer_id}")
        return await self.client.post(f"/api/v3/indexer/{indexer_id}/test")

    async def update_indexer(self, indexer: dict) -> Any:
        """Update indexer configuration.
        
        Sends the complete indexer object with modifications (typically
        setting enable=True/False to enable or disable the indexer).
        
        Args:
            indexer: Complete indexer dictionary (as returned by get_indexers)
                     with modifications applied
                     
        Returns:
            Updated indexer object
            
        Raises:
            httpx.HTTPStatusError: If update fails
        """
        indexer_id = indexer.get("id")
        logger.debug(f"Updating Sonarr indexer {indexer_id}")
        return await self.client.put(f"/api/v3/indexer/{indexer_id}", json=indexer)
