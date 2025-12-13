from typing import Any, Optional

import httpx


class ArrHttpClient:
    """Small wrapper around `httpx.AsyncClient` used for Arr family services.

    Provides convenience helpers and a proper async context manager.
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=timeout,
        )

    async def _parse_response(self, resp: httpx.Response) -> Any:
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError:
            return resp.text

    async def get(self, path: str, params: Optional[dict] = None) -> Any:
        resp = await self.client.get(path, params=params)
        return await self._parse_response(resp)

    async def post(self, path: str, json: Optional[dict] = None) -> Any:
        resp = await self.client.post(path, json=json)
        return await self._parse_response(resp)

    async def put(self, path: str, json: Optional[dict] = None) -> Any:
        resp = await self.client.put(path, json=json)
        return await self._parse_response(resp)

    async def delete(self, path: str) -> Any:
        resp = await self.client.delete(path)
        return await self._parse_response(resp)

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "ArrHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
