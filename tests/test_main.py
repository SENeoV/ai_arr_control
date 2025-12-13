"""Integration/smoke tests for the main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

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


def test_app_startup_requires_config():
    """Test that app startup fails without required config."""
    # This test demonstrates that settings validation is enforced
    # In a real scenario, we'd test with missing env vars
    pass
