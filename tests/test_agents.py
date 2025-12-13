"""Unit tests for agents module."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.indexer_control_agent import IndexerControlAgent
from agents.indexer_health_agent import IndexerHealthAgent


@pytest.mark.asyncio
async def test_indexer_control_agent_disable_indexer():
    """Test IndexerControlAgent.disable_indexer()."""
    mock_service = AsyncMock()
    mock_service.update_indexer = AsyncMock()

    agent = IndexerControlAgent(radarr=mock_service, sonarr=None)

    indexer = {"id": 1, "name": "Test Indexer", "enable": True}
    await agent.disable_indexer(mock_service, indexer)

    # Verify the indexer was updated with enable=False
    mock_service.update_indexer.assert_called_once()
    call_args = mock_service.update_indexer.call_args[0][0]
    assert call_args["enable"] is False
    assert call_args["name"] == "Test Indexer"


@pytest.mark.asyncio
async def test_indexer_health_agent_run():
    """Test IndexerHealthAgent.run() with successful indexers."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()

    mock_radarr.get_indexers.return_value = [
        {"id": 1, "name": "Radarr Index 1"},
    ]
    mock_sonarr.get_indexers.return_value = [
        {"id": 2, "name": "Sonarr Index 1"},
    ]

    mock_radarr.test_indexer.return_value = {"success": True}
    mock_sonarr.test_indexer.return_value = {"success": True}

    agent = IndexerHealthAgent(radarr=mock_radarr, sonarr=mock_sonarr)
    await agent.run()

    # Verify both services were called
    mock_radarr.get_indexers.assert_called_once()
    mock_sonarr.get_indexers.assert_called_once()
    mock_radarr.test_indexer.assert_called_once_with(1)
    mock_sonarr.test_indexer.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_indexer_health_agent_handles_failures():
    """Test IndexerHealthAgent handles failed indexers gracefully."""
    mock_radarr = AsyncMock()
    mock_radarr.get_indexers.return_value = [
        {"id": 1, "name": "Failing Index"},
    ]
    mock_radarr.test_indexer.side_effect = Exception("Connection timeout")

    agent = IndexerHealthAgent(radarr=mock_radarr, sonarr=None)
    # Should not raise, only log
    await agent.run()

    mock_radarr.test_indexer.assert_called_once()
