from typing import Any, List

from core.http import ArrHttpClient


class SonarrService:
    """Client wrapper for Sonarr HTTP API endpoints used by the agents."""

    def __init__(self, client: ArrHttpClient) -> None:
        self.client = client

    async def get_indexers(self) -> List[dict]:
        return await self.client.get("/api/v3/indexer")

    async def test_indexer(self, indexer_id: int) -> Any:
        return await self.client.post(f"/api/v3/indexer/{indexer_id}/test")

    async def update_indexer(self, indexer: dict) -> Any:
        return await self.client.put(f"/api/v3/indexer/{indexer['id']}", json=indexer)
