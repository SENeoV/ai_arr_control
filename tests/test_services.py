"""Unit tests for services module."""

import pytest
from unittest.mock import AsyncMock

from services.radarr import RadarrService
from services.sonarr import SonarrService


@pytest.mark.asyncio
async def test_radarr_service_get_indexers():
    """Test RadarrService.get_indexers()."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {"id": 1, "name": "Indexer1", "enable": True},
        {"id": 2, "name": "Indexer2", "enable": False},
    ]

    service = RadarrService(mock_client)
    result = await service.get_indexers()

    assert len(result) == 2
    assert result[0]["name"] == "Indexer1"
    mock_client.get.assert_called_once_with("/api/v3/indexer")


@pytest.mark.asyncio
async def test_radarr_service_test_indexer():
    """Test RadarrService.test_indexer()."""
    mock_client = AsyncMock()
    mock_client.post.return_value = {"success": True}

    service = RadarrService(mock_client)
    result = await service.test_indexer(1)

    assert result == {"success": True}
    mock_client.post.assert_called_once_with("/api/v3/indexer/1/test")


@pytest.mark.asyncio
async def test_radarr_service_update_indexer():
    """Test RadarrService.update_indexer()."""
    mock_client = AsyncMock()
    mock_client.put.return_value = {"id": 1, "enable": False}

    service = RadarrService(mock_client)
    indexer = {"id": 1, "name": "Test", "enable": False}
    result = await service.update_indexer(indexer)

    assert result["enable"] is False
    mock_client.put.assert_called_once_with("/api/v3/indexer/1", json=indexer)


@pytest.mark.asyncio
async def test_sonarr_service_get_indexers():
    """Test SonarrService.get_indexers()."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {"id": 1, "name": "Sonarr Indexer", "enable": True},
    ]

    service = SonarrService(mock_client)
    result = await service.get_indexers()

    assert len(result) == 1
    assert result[0]["name"] == "Sonarr Indexer"
    mock_client.get.assert_called_once_with("/api/v3/indexer")
