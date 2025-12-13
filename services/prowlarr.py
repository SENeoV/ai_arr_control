from typing import List, Any

from core.http import ArrHttpClient


class ProwlarrService:
    """Client wrapper for Prowlarr endpoints currently used by the project."""

    def __init__(self, client: ArrHttpClient) -> None:
        self.client = client

    async def get_indexers(self) -> List[dict]:
        return await self.client.get("/api/v1/indexer")

    async def test_indexer(self, indexer_id: int) -> Any:
        # Prowlarr may not expose the same test endpoint; if not implemented
        # by the server this will raise and be handled by callers.
        return await self.client.post(f"/api/v1/indexer/{indexer_id}/test")
