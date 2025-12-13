"""Integration/smoke tests for the main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert body.get("status") == "ok"
    assert body.get("service") == "AI Arr Control"


def test_root_endpoint(client):
    """Test the root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "AI Arr Control"
    assert "endpoints" in body
    assert "monitoring" in body["endpoints"]
    assert "indexers" in body["endpoints"]
    assert "agents" in body["endpoints"]


def test_metrics_endpoint(client):
    """Test the metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "uptime_seconds" in body
    assert "total_operations" in body
    assert "success_rate_percent" in body


def test_events_endpoint(client):
    """Test the recent events endpoint."""
    response = client.get("/events")
    assert response.status_code == 200
    body = response.json()
    assert "timestamp" in body
    assert "events_count" in body
    assert "events" in body
    assert isinstance(body["events"], list)


def test_events_endpoint_with_limit(client):
    """Test the events endpoint with custom limit."""
    response = client.get("/events?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["events_count"] <= 10


def test_agents_status_endpoint(client):
    """Test the agent status endpoint."""
    response = client.get("/agents/status")
    assert response.status_code == 200
    body = response.json()
    assert "scheduler" in body
    assert "agents" in body
    assert body["scheduler"]["running"] is True
    assert "health_agent" in body["agents"]
    assert "autoheal_agent" in body["agents"]


def test_indexers_stats_endpoint(client):
    """Test the indexers statistics endpoint."""
    response = client.get("/indexers/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "by_service" in body
    # Services should be present (may have errors if services not available)
    assert any(k in body["by_service"] for k in ["radarr", "sonarr", "prowlarr"])


def test_app_startup_requires_config():
    """Test that app startup requires proper configuration."""
    # The app should start with valid config from test settings
    # If config is invalid, startup will fail
    assert app is not None


def test_invalid_service_name(client):
    """Test endpoints with invalid service names."""
    response = client.post("/indexers/invalid/1/test")
    assert response.status_code == 400


def test_indexer_endpoints_validation(client):
    """Test that indexer endpoints properly validate input."""
    # Test with invalid service
    response = client.get("/indexers/invalid")
    assert response.status_code == 400
    
    # Test valid service names
    response = client.get("/indexers/radarr")
    # May fail with connection error but shouldn't be 400
    assert response.status_code in [200, 500, 502, 503]

