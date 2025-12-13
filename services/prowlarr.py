"""Prowlarr service client for unified indexer management.

Wraps Prowlarr REST API endpoints for querying and managing indexers.
Prowlarr is the unified indexer management application in the Arr ecosystem,
allowing centralized indexer configuration across Radarr and Sonarr.

Note: This service uses API v1 which differs from Radarr/Sonarr's v3.
"""

from typing import List, Any
from loguru import logger
from core.http import ArrHttpClient


class ProwlarrService:
    """Client wrapper for Prowlarr REST API endpoints.
    
    Provides methods for:
    - Listing all configured indexers
    - Testing indexer connectivity (if supported by Prowlarr version)
    
    Args:
        client: Configured ArrHttpClient pointing to Prowlarr instance
    """

    def __init__(self, client: ArrHttpClient) -> None:
        self.client = client
        logger.info("Initialized ProwlarrService")

    async def get_indexers(self) -> List[dict]:
        """Fetch list of all indexers managed by Prowlarr.
        
        Returns:
            List of indexer dictionaries containing id, name, enable status, etc.
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.debug("Fetching Prowlarr indexers")
        indexers = await self.client.get("/api/v1/indexer")
        logger.debug(f"Found {len(indexers)} Prowlarr indexers")
        return indexers

    async def test_indexer(self, indexer_id: int) -> Any:
        """Test connectivity of a specific indexer in Prowlarr.
        
        Note: The Prowlarr API may not support this endpoint on all versions.
        If not supported, this will raise an HTTPStatusError.
        
        Args:
            indexer_id: ID of the indexer to test
            
        Returns:
            Response from Prowlarr (typically success indicator)
            
        Raises:
            httpx.HTTPStatusError: If test fails or endpoint not supported
        """
        logger.debug(f"Testing Prowlarr indexer {indexer_id}")
        return await self.client.post(f"/api/v1/indexer/{indexer_id}/test")
