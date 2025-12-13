from core.http import ArrHttpClient

class SonarrService:
    def __init__(self, client: ArrHttpClient):
        self.client = client

    async def get_indexers(self):
        return await self.client.get("/api/v3/indexer")

    async def test_indexer(self, indexer_id: int):
        return await self.client.post(f"/api/v3/indexer/{indexer_id}/test")
