import httpx

class ArrHttpClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=30,
        )

    async def get(self, path: str):
        r = await self.client.get(path)
        r.raise_for_status()
        return r.json()

    async def post(self, path: str, json=None):
        r = await self.client.post(path, json=json)
        r.raise_for_status()
        return r.json()
