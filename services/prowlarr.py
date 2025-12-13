from core.http import ArrHttpClient

class ProwlarrService:
    def __init__(self, client: ArrHttpClient):
        self.client = client

    async def get_indexers(self):
        return await self.client.get("/api/v1/indexer")
