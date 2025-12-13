"""Unit tests for core.http module."""

import pytest

from core.http import ArrHttpClient


def test_arr_http_client_initialization():
    """Test ArrHttpClient initialization."""
    client = ArrHttpClient("http://test.local", "test_key")
    assert client.client.base_url == "http://test.local"
    assert client.client.headers["X-Api-Key"] == "test_key"
    import asyncio
    asyncio.run(client.close())


@pytest.mark.asyncio
async def test_arr_http_client_context_manager():
    """Test ArrHttpClient as async context manager."""
    async with ArrHttpClient("http://test.local", "test_key") as client:
        assert isinstance(client, ArrHttpClient)


def test_arr_http_client_instantiation():
    """Test basic ArrHttpClient creation with custom timeout."""
    client = ArrHttpClient("http://test.local", "test_key", timeout=60)
    assert client.client.timeout is not None
    import asyncio
    asyncio.run(client.close())


@pytest.mark.asyncio
async def test_arr_http_client_close():
    """Test that client closes cleanly."""
    client = ArrHttpClient("http://test.local", "test_key")
    await client.close()
    # After close, aclose is now a no-op
    await client.close()
