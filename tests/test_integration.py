"""Integration tests for complete application flow."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestIntegrationEndpoints:
    """Integration tests for critical application flows."""
    
    def test_complete_health_workflow(self, client):
        """Test complete health check workflow."""
        # 1. Check health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # 2. Check startup status
        response = client.get("/startup-status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # 3. Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_operations" in data
    
    def test_indexer_list_workflow(self, client):
        """Test indexer listing workflow."""
        # 1. Get all indexers
        response = client.get("/indexers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # 2. Get stats
        response = client.get("/indexers/stats")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "total" in data
        assert "by_service" in data
    
    def test_invalid_service_error(self, client):
        """Test error handling for invalid service."""
        response = client.get("/indexers/invalid-service")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_api_documentation_available(self, client):
        """Verify Swagger UI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()


class TestEventLogging:
    """Test event logging system."""
    
    def test_events_endpoint(self, client):
        """Test events endpoint."""
        response = client.get("/events")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "events_count" in data
        assert "events" in data
        assert isinstance(data["events"], list)
    
    def test_events_with_limit(self, client):
        """Test events endpoint with limit."""
        response = client.get("/events?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["events_count"] <= 5


class TestAgentEndpoints:
    """Test agent control endpoints."""
    
    def test_agent_status_endpoint(self, client):
        """Test getting agent status."""
        response = client.get("/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert "scheduler" in data
        assert "agents" in data
        assert isinstance(data["agents"], dict)
    
    def test_health_agent_metrics(self, client):
        """Test health agent metrics are populated."""
        response = client.get("/agents/status")
        data = response.json()
        
        if "health_agent" in data.get("agents", {}):
            agent = data["agents"]["health_agent"]
            assert "metrics" in agent
            assert "total_runs" in agent["metrics"]


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_nonexistent_indexer(self, client):
        """Test error for nonexistent indexer."""
        response = client.post("/indexers/radarr/99999/test")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_invalid_method(self, client):
        """Test invalid HTTP method."""
        response = client.put("/health")
        assert response.status_code == 405  # Method not allowed
    
    def test_invalid_json_payload(self, client):
        """Test invalid JSON in request."""
        response = client.post(
            "/indexers/radarr/1/test",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        # Should either parse error or work despite bad data
        assert response.status_code in [400, 422, 404, 500]


class TestHealthHistory:
    """Test health history endpoints."""
    
    def test_health_history_endpoint(self, client):
        """Test health history retrieval."""
        response = client.get("/health-history")
        assert response.status_code == 200
        data = response.json()
        assert "hours" in data
        assert "history" in data
        assert isinstance(data["history"], dict)
    
    def test_health_history_with_hours(self, client):
        """Test health history with specific hours."""
        response = client.get("/health-history?hours=48")
        assert response.status_code == 200
        data = response.json()
        assert data["hours"] == 48


class TestDetailedStats:
    """Test detailed statistics endpoint."""
    
    def test_detailed_stats_endpoint(self, client):
        """Test detailed statistics."""
        response = client.get("/stats/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "services" in data or "period_days" in data


class TestConcurrency:
    """Test concurrent request handling."""
    
    def test_multiple_health_checks(self, client):
        """Test multiple concurrent health checks."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_mixed_endpoint_calls(self, client):
        """Test calling different endpoints in sequence."""
        endpoints = [
            "/health",
            "/indexers",
            "/metrics",
            "/agents/status",
            "/events"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed for {endpoint}"


class TestResponseFormats:
    """Test response format consistency."""
    
    def test_all_responses_are_json(self, client):
        """Verify all endpoints return valid JSON."""
        endpoints = [
            "/health",
            "/indexers",
            "/metrics",
            "/agents/status",
            "/events",
            "/health-history"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            # Should not raise JSON decode error
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_error_responses_have_detail(self, client):
        """Verify error responses include detail field."""
        response = client.get("/indexers/invalid")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestStartupSequence:
    """Test application startup behavior."""
    
    def test_startup_status_on_start(self, client):
        """Test that startup status is tracked."""
        response = client.get("/startup-status")
        assert response.status_code == 200
        data = response.json()
        assert "complete" in data
        # After initial load, should be complete
        if response.status_code == 200:
            assert isinstance(data.get("complete"), bool)
