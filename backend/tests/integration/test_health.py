"""
Integration test for health check endpoint.
"""
import pytest


@pytest.mark.integration
def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "app_name" in data
    assert data["app_name"] == "DocuMind"
