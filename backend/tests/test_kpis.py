def test_get_dashboard_kpis_default(client):
    """Verify GET /api/dashboard/kpis returns 4 KPIs matching frontend schema contract."""
    response = client.get("/api/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 4

    expected_ids = {"total_revenue", "total_orders", "growth_rate", "ai_insights"}
    returned_ids = {item["id"] for item in data}
    assert expected_ids.issubset(returned_ids)

    # Validate exact frontend camelCase field names
    sample = data[0]
    required_keys = [
        "id",
        "label",
        "value",
        "changePercent",
        "trend",
        "periodLabel",
        "iconName",
    ]
    for key in required_keys:
        assert key in sample, f"Missing key {key} in KPI response"


def test_get_dashboard_kpis_range_filters(client):
    """Verify range filtering (7d, 30d, 90d, 1y)."""
    for r in ["7d", "30d", "90d", "1y"]:
        response = client.get(f"/api/dashboard/kpis?range={r}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4


def test_get_dashboard_kpis_invalid_range(client):
    """Verify input validation rejects invalid date ranges with HTTP 422."""
    response = client.get("/api/dashboard/kpis?range=invalid_range")
    assert response.status_code == 422
