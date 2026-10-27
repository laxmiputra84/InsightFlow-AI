from unittest.mock import patch


def test_health_success(client):
    """Verify /health returns 200 and connected status when database is reachable."""
    with patch("app.api.routes.health.check_db_connection", return_value=(True, 12.5, "connected")):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["database_latency_ms"] == 12.5
        assert "version" in data
        assert "timestamp" in data


def test_health_database_failure(client):
    """Verify /health returns 503 and degraded status when database is disconnected."""
    with patch(
        "app.api.routes.health.check_db_connection",
        return_value=(False, 100.0, "disconnected: Connection refused"),
    ):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert "disconnected" in data["database"]
        assert data["database_latency_ms"] == 100.0
