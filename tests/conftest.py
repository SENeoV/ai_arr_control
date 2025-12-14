"""Test fixtures and configuration."""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Set test mode environment variables BEFORE any imports
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('RADARR_URL', 'http://localhost:7878')
os.environ.setdefault('RADARR_API_KEY', 'test_key_123456789')
os.environ.setdefault('SONARR_URL', 'http://localhost:8989')
os.environ.setdefault('SONARR_API_KEY', 'test_key_987654321')
os.environ.setdefault('PROWLARR_URL', 'http://localhost:9696')
os.environ.setdefault('PROWLARR_API_KEY', 'test_key_abcdefghij')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')

from config.settings import Settings
from core.http import ArrHttpClient
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def mock_settings() -> Settings:
    """Create test settings with mock URLs."""
    return Settings(
        radarr_url="http://localhost:7878",
        radarr_api_key="test_key_123456789",
        sonarr_url="http://localhost:8989",
        sonarr_api_key="test_key_987654321",
        prowlarr_url="http://localhost:9696",
        prowlarr_api_key="test_key_abcdefghij",
        database_url="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
async def async_http_client(mock_settings) -> AsyncGenerator[ArrHttpClient, None]:
    """Create an async test HTTP client."""
    client = ArrHttpClient(mock_settings.radarr_url, mock_settings.radarr_api_key)
    yield client
    await client.close()


@pytest.fixture
def http_client(mock_settings) -> Generator[ArrHttpClient, None, None]:
    """Create a sync test HTTP client wrapper."""
    
    async def _create():
        return ArrHttpClient(mock_settings.radarr_url, mock_settings.radarr_api_key)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    client = loop.run_until_complete(_create())
    yield client
    loop.run_until_complete(client.close())


@pytest.fixture
def test_client() -> TestClient:
    """Create a TestClient for FastAPI app with proper lifespan handling.
    
    Note: TestClient runs the lifespan context manager automatically,
    so app state should be available during tests.
    """
    return TestClient(app)


def pytest_configure(config):
    """Configure pytest with mocks before any tests run."""
    
    # Mock ArrHttpClient methods for testing
    async def mock_get(self, path: str, params=None):
        """Mock GET request."""
        if "indexer" in path:
            return [
                {"id": 1, "name": "Test Indexer 1", "enable": True, "protocol": "usenet"},
                {"id": 2, "name": "Test Indexer 2", "enable": False, "protocol": "torrent"},
            ]
        elif "status" in path.lower():
            return {"appName": "Radarr", "appVersion": "5.0.0"}
        return {}
    
    async def mock_post(self, path: str, json=None):
        """Mock POST request."""
        if "test" in path:
            return {"status": "ok", "message": "Test successful"}
        return {"success": True}
    
    async def mock_put(self, path: str, json=None):
        """Mock PUT request."""
        return {"success": True}
    
    async def mock_delete(self, path: str):
        """Mock DELETE request."""
        return {"success": True}
    
    async def mock_close(self):
        """Mock close."""
        pass
    
    # Patch HTTP client methods
    ArrHttpClient.get = mock_get
    ArrHttpClient.post = mock_post
    ArrHttpClient.put = mock_put
    ArrHttpClient.delete = mock_delete
    ArrHttpClient.close = mock_close
    
    # Mock settings validation
    Settings.validate_at_startup = Mock(return_value=None)
