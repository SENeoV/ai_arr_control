from typing import Any, Optional
import httpx
from loguru import logger


class ArrHttpClient:
    """Wrapper around httpx.AsyncClient for Arr family services (Radarr, Sonarr, etc).

    Provides convenience helpers for REST API calls and a proper async context manager.
    Includes automatic API key injection, error handling, and response parsing.
    
    Args:
        base_url: Base URL of the Arr service (e.g., http://radarr:7878)
        api_key: API key for authentication
        timeout: Request timeout in seconds (default: 30)
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=timeout,
        )
        logger.debug(f"Initialized HTTP client for {base_url}")

    async def _parse_response(self, resp: httpx.Response) -> Any:
        """Parse HTTP response, attempting JSON first, then falling back to text.
        
        Args:
            resp: The httpx.Response object
            
        Returns:
            Parsed JSON dict/list if content is JSON, otherwise text response
            
        Raises:
            httpx.HTTPStatusError: If response status is 4xx or 5xx
        """
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code}: {e.response.text[:200]}"
            )
            raise
        
        try:
            return resp.json()
        except ValueError:
            # Not JSON, return as text
            return resp.text

    async def get(self, path: str, params: Optional[dict] = None) -> Any:
        """Perform GET request.
        
        Args:
            path: API endpoint path (e.g., /api/v3/indexer)
            params: Optional query parameters
            
        Returns:
            Parsed response (JSON or text)
        """
        logger.debug(f"GET {path}")
        resp = await self.client.get(path, params=params)
        return await self._parse_response(resp)

    async def post(self, path: str, json: Optional[dict] = None) -> Any:
        """Perform POST request.
        
        Args:
            path: API endpoint path
            json: Optional JSON payload
            
        Returns:
            Parsed response
        """
        logger.debug(f"POST {path}")
        resp = await self.client.post(path, json=json)
        return await self._parse_response(resp)

    async def put(self, path: str, json: Optional[dict] = None) -> Any:
        """Perform PUT request.
        
        Args:
            path: API endpoint path
            json: Optional JSON payload
            
        Returns:
            Parsed response
        """
        logger.debug(f"PUT {path}")
        resp = await self.client.put(path, json=json)
        return await self._parse_response(resp)

    async def delete(self, path: str) -> Any:
        """Perform DELETE request.
        
        Args:
            path: API endpoint path
            
        Returns:
            Parsed response
        """
        logger.debug(f"DELETE {path}")
        resp = await self.client.delete(path)
        return await self._parse_response(resp)

    async def close(self) -> None:
        """Close the underlying HTTP client connection."""
        await self.client.aclose()
        logger.debug("HTTP client closed")

    async def __aenter__(self) -> "ArrHttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager exit - ensures connection is closed."""
        await self.close()
