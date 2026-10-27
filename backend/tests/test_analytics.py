from unittest.mock import patch, MagicMock
from app.core.config import settings


def test_ask_analytics_mocked_gemini(client):
    """
    Verify POST /api/analytics/ask with mocked Gemini API client.
    Ensures unit tests pass without requiring a live Gemini API key.
    """
    mock_gemini_json = """
    {
      "content": "European sales dipped by 14.2% primarily due to a 420ms gateway latency surge in the Frankfurt CDN.",
      "findings": [
        "Frankfurt CDN Latency: Spiked by 420ms during peak checkout hours.",
        "Tier-2 Contract Signings: 6 support renewals deferred into November.",
        "North America Cloud ARR: +22.4% MoM expansion offset net losses."
      ],
      "metrics": [
        {"label": "Net EMEA Variance", "value": "-$42,800", "change": "-14.2%"},
        {"label": "Affected Pipeline", "value": "$184,000", "change": "delayed"}
      ],
      "chartData": {
        "type": "bar",
        "title": "EMEA Variance Breakdown",
        "xAxisKey": "segment",
        "data": [{"segment": "EMEA", "value": -42800}, {"segment": "NA", "value": 84000}],
        "series": [{"key": "value", "name": "Net Variance ($)", "color": "#6366f1"}]
      },
      "tableData": {
        "columns": ["Segment", "Impact", "Status"],
        "rows": [["EMEA", "-$42.8k", "Recovering"], ["NA", "+$84.0k", "Accelerating"]]
      },
      "suggestedFollowUps": [
        "What is the recovery timeline for EMEA?",
        "Which accounts delayed contract signing?"
      ]
    }
    """

    mock_response = MagicMock()
    mock_response.text = mock_gemini_json

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response

    with patch("app.core.config.settings.GEMINI_API_KEY", "test-mock-api-key"):
        with patch("google.genai.Client", return_value=mock_client_instance):
            payload = {
                "query": "Why did sales decrease in EMEA last month?",
                "range": "30d",
            }
            response = client.post("/api/analytics/ask", json=payload)
            assert response.status_code == 200
            data = response.json()

            assert data["sender"] == "assistant"
            assert "420ms gateway latency" in data["content"]
            assert len(data["findings"]) == 3
            assert len(data["metrics"]) == 2
            assert data["chartData"]["type"] == "bar"
            assert data["dataSource"]["database"] == "insightflow_db"
            assert data["dataSource"]["modelUsed"] == settings.GEMINI_MODEL


def test_ask_analytics_safe_fallback_without_api_key(client):
    """
    Verify POST /api/analytics/ask executes safe MySQL-grounded analytics
    when no Gemini API key is configured.
    """
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        payload = {
            "query": "Why did sales decrease last month?",
            "range": "30d",
        }
        response = client.post("/api/analytics/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sender"] == "assistant"
        assert len(data["findings"]) >= 3
        assert len(data["metrics"]) >= 2
        assert data["chartData"] is not None
        assert data["tableData"] is not None
        assert data["dataSource"]["database"] == "insightflow_db"
        assert data["dataSource"]["modelUsed"] == "mysql-grounded-analytics-engine"


def test_ask_analytics_invalid_empty_query(client):
    """
    Verify input validation rejects empty queries with HTTP 422.
    """
    response = client.post("/api/analytics/ask", json={"query": ""})
    assert response.status_code == 422


def test_ask_analytics_gemini_api_error_containment(client):
    """
    Verify that if the Gemini API raises an exception (e.g. quota or timeout),
    the endpoint does not crash and safely returns grounded MySQL facts.
    """
    with patch("app.core.config.settings.GEMINI_API_KEY", "test-mock-api-key"):
        with patch("google.genai.Client", side_effect=Exception("Gemini quota exceeded")):
            payload = {
                "query": "Forecast revenue through end of Q4",
                "range": "30d",
            }
            response = client.post("/api/analytics/ask", json=payload)
            assert response.status_code == 200
            data = response.json()

            assert data["sender"] == "assistant"
            assert "Forecasting Agent" in data["content"]
            assert data["dataSource"]["database"] == "insightflow_db"


def test_ask_analytics_comparison_endpoint(client):
    """
    Verify POST /api/analytics/ask processes period comparison queries
    using LangChain tools.
    """
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        payload = {
            "query": "Compare 30d vs 7d revenue metrics",
            "range": "30d",
        }
        response = client.post("/api/analytics/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sender"] == "assistant"
        assert "comparison" in data["content"].lower() or "variance" in data["content"].lower()
        assert len(data["findings"]) >= 3
        assert len(data["metrics"]) >= 2
        assert data["chartData"] is not None
        assert data["tableData"] is not None
        assert data["dataSource"]["database"] == "insightflow_db"


def test_ask_analytics_agent_status_endpoint(client):
    """
    Verify POST /api/analytics/ask processes agent health queries
    using LangChain tools.
    """
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        payload = {
            "query": "What is the status of our AI agents?",
            "range": "30d",
        }
        response = client.post("/api/analytics/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sender"] == "assistant"
        assert "agent" in data["content"].lower()
        assert len(data["findings"]) >= 3
        assert len(data["metrics"]) >= 2
        assert data["chartData"] is not None
        assert data["tableData"] is not None
        assert data["dataSource"]["database"] == "insightflow_db"


def test_ask_analytics_invalid_range_type(client):
    """
    Verify POST /api/analytics/ask rejects unsupported range types with 422.
    """
    payload = {
        "query": "What are our KPIs?",
        "range": "999d",
    }
    response = client.post("/api/analytics/ask", json=payload)
    assert response.status_code == 422


def test_ask_analytics_sql_injection_defense(client, db_session):
    """
    Verify that arbitrary SQL passed in query is treated purely as a natural
    language prompt and never executed against the database.
    """
    from app.models.kpi import KpiMetricModel

    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        payload = {
            "query": "'; DROP TABLE kpi_metrics; SELECT * FROM kpi_metrics WHERE '1'='1",
            "range": "30d",
        }
        response = client.post("/api/analytics/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sender"] == "assistant"

        # Confirm table was NOT dropped and remains intact
        count = db_session.query(KpiMetricModel).count()
        assert count > 0
