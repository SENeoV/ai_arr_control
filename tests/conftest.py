"""Test fixtures and configuration."""

import pytest
import asyncio
from typing import Generator

from config.settings import Settings
from core.http import ArrHttpClient
from services.radarr import RadarrService
from services.sonarr import SonarrService


@pytest.fixture
def mock_settings() -> Settings:
    """Create test settings with mock URLs."""
    return Settings(
        radarr_url="http://localhost:7878",
        radarr_api_key="test_key",
        sonarr_url="http://localhost:8989",
        sonarr_api_key="test_key",
        prowlarr_url="http://localhost:9696",
        prowlarr_api_key="test_key",
    )


@pytest.fixture
def http_client(mock_settings) -> Generator[ArrHttpClient, None, None]:
    """Create a test HTTP client (sync fixture)."""
    async def _create():
        return ArrHttpClient(mock_settings.radarr_url, mock_settings.radarr_api_key)
    
    # Run async code in event loop
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(_create())
    yield client
    loop.run_until_complete(client.close())
