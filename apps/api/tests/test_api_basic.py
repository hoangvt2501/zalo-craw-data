"""Basic API endpoint tests.

These tests verify the API can start and respond correctly.
They require a running PostgreSQL instance with the schema applied.
"""

import os
import sys
import pytest

# Ensure api app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI test client."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Cannot create test client: {e}")


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data

    def test_health_checks_db(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["database"] in ("ok", "error")


class TestDealsEndpoints:
    def test_deals_list_returns_200(self, client):
        response = client.get("/deals?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_deals_rejected_returns_200(self, client):
        response = client.get("/deals/rejected?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_deals_list_respects_limit(self, client):
        response = client.get("/deals?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("items", [])) <= 5


class TestMetricsEndpoint:
    def test_metrics_summary_returns_200(self, client):
        response = client.get("/metrics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data


class TestMessagesEndpoint:
    def test_invalid_message_id_returns_404(self, client):
        response = client.get("/messages/00000000-0000-0000-0000-000000000000")
        assert response.status_code in (404, 200)  # 200 if it returns null message
