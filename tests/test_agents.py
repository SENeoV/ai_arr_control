"""Tests for agent modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agents.indexer_health_agent import IndexerHealthAgent
from agents.indexer_control_agent import IndexerControlAgent
from agents.indexer_autoheal_agent import IndexerAutoHealAgent


@pytest.mark.asyncio
async def test_health_agent_initialization():
    """Test IndexerHealthAgent initialization."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    
    agent = IndexerHealthAgent(mock_radarr, mock_sonarr)
    
    assert agent.radarr == mock_radarr
    assert agent.sonarr == mock_sonarr


@pytest.mark.asyncio
async def test_health_agent_checks_both_services():
    """Test that health agent checks both services."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    
    mock_radarr.get_indexers.return_value = [
        {"id": 1, "name": "Radarr Index 1"}
    ]
    mock_sonarr.get_indexers.return_value = [
        {"id": 1, "name": "Sonarr Index 1"}
    ]
    
    mock_radarr.test_indexer.return_value = {"success": True}
    mock_sonarr.test_indexer.return_value = {"success": True}
    
    agent = IndexerHealthAgent(mock_radarr, mock_sonarr)
    await agent.run()
    
    # Verify both services were queried
    mock_radarr.get_indexers.assert_called_once()
    mock_sonarr.get_indexers.assert_called_once()


@pytest.mark.asyncio
async def test_health_agent_handles_service_failure():
    """Test that health agent handles service failures gracefully."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    
    # Radarr fails to respond
    mock_radarr.get_indexers.side_effect = Exception("Connection error")
    mock_sonarr.get_indexers.return_value = []
    
    agent = IndexerHealthAgent(mock_radarr, mock_sonarr)
    
    # Should not raise exception
    await agent.run()
    
    # Sonarr should still be checked
    mock_sonarr.get_indexers.assert_called_once()


@pytest.mark.asyncio
async def test_control_agent_disable_indexer():
    """Test IndexerControlAgent.disable_indexer()."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    
    agent = IndexerControlAgent(mock_radarr, mock_sonarr)
    
    indexer = {"id": 1, "name": "Test Indexer", "enable": True}
    mock_service = AsyncMock()
    mock_service.update_indexer = AsyncMock()
    
    await agent.disable_indexer(mock_service, indexer)
    
    # Verify the indexer was updated with enable=False
    mock_service.update_indexer.assert_called_once()
    call_args = mock_service.update_indexer.call_args
    updated_indexer = call_args[0][0]
    assert updated_indexer["enable"] is False
    assert updated_indexer["id"] == 1


@pytest.mark.asyncio
async def test_control_agent_enable_indexer():
    """Test IndexerControlAgent.enable_indexer()."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    
    agent = IndexerControlAgent(mock_radarr, mock_sonarr)
    
    indexer = {"id": 2, "name": "Test Indexer 2", "enable": False}
    mock_service = AsyncMock()
    mock_service.update_indexer = AsyncMock()
    
    await agent.enable_indexer(mock_service, indexer)
    
    # Verify the indexer was updated with enable=True
    mock_service.update_indexer.assert_called_once()
    call_args = mock_service.update_indexer.call_args
    updated_indexer = call_args[0][0]
    assert updated_indexer["enable"] is True


@pytest.mark.asyncio
async def test_autoheal_agent_disables_failed_indexers():
    """Test that autoheal agent disables failed indexers."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    mock_control = AsyncMock()
    
    # Radarr has one failing indexer
    mock_radarr.get_indexers.return_value = [
        {"id": 1, "name": "Good Indexer", "enable": True},
        {"id": 2, "name": "Bad Indexer", "enable": True},
    ]
    
    # Sonarr has no indexers
    mock_sonarr.get_indexers.return_value = []
    
    # First indexer succeeds, second fails
    mock_radarr.test_indexer.side_effect = [
        {"success": True},
        Exception("Connection timeout"),
    ]
    
    agent = IndexerAutoHealAgent(mock_radarr, mock_sonarr, mock_control)
    await agent.run()
    
    # Verify disable was called for the failing indexer
    assert mock_control.disable_indexer.called


@pytest.mark.asyncio
async def test_autoheal_agent_records_results():
    """Test that autoheal agent records health check results."""
    mock_radarr = AsyncMock()
    mock_sonarr = AsyncMock()
    mock_control = AsyncMock()
    
    mock_radarr.get_indexers.return_value = [
        {"id": 1, "name": "Test Indexer", "enable": True},
    ]
    mock_sonarr.get_indexers.return_value = []
    
    mock_radarr.test_indexer.return_value = {"success": True}
    
    agent = IndexerAutoHealAgent(mock_radarr, mock_sonarr, mock_control)
    
    # Run should complete without errors
    await agent.run()
    
    # Verify the agent ran the health check
    mock_radarr.get_indexers.assert_called_once()
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
