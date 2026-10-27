def test_get_agents_list(client):
    """Verify GET /api/agents returns 4 BI agents matching frontend schema contract."""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 4

    agent_names = {a["name"] for a in data}
    assert "Data Analyst Agent" in agent_names
    assert "Root Cause Agent" in agent_names
    assert "Forecasting Agent" in agent_names
    assert "Report Agent" in agent_names

    sample = data[0]
    required_keys = [
        "id",
        "name",
        "role",
        "description",
        "capabilities",
        "status",
        "color",
    ]
    for key in required_keys:
        assert key in sample, f"Missing key {key} in agent response"
    assert isinstance(sample["capabilities"], list)
