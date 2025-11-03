"""Basic API tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_input():
    """Test creating an input."""
    response = client.post(
        "/api/inputs",
        json={"name": "Test Input", "udp_port": 5050},
        headers={"X-API-Key": settings.api_key}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Input"
    assert data["udp_port"] == 5050


def test_list_inputs():
    """Test listing inputs."""
    response = client.get(
        "/api/inputs",
        headers={"X-API-Key": settings.api_key}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unauthorized_access():
    """Test API without authentication."""
    response = client.get("/api/inputs")
    assert response.status_code == 401


def test_invalid_api_key():
    """Test API with invalid key."""
    response = client.get(
        "/api/inputs",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401


def test_system_status():
    """Test system status endpoint."""
    response = client.get(
        "/api/system/status",
        headers={"X-API-Key": settings.api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert "healthy" in data
    assert "version" in data
    assert "inputs_count" in data
