"""
Tests for Milestone 5: LangChain Analytics Tools Integration.
Validates all 4 approved tools, argument validation, database error handling,
LangChain BaseTool invocation, and tool selection.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.tools.analytics_tools import (
    AnalyticsToolkit,
    KpiSummaryInput,
    CompareKpiPeriodsInput,
    DetectKpiAnomaliesInput,
    AgentStatusInput,
    parse_numeric_value,
)
from app.services.analytics_service import AnalyticsService


# ==============================================================================
# 1. Numeric Parser Tests
# ==============================================================================

def test_parse_numeric_value():
    assert parse_numeric_value("$1,284,520") == 1284520.0
    assert parse_numeric_value("14,892") == 14892.0
    assert parse_numeric_value("+18.2%") == 18.2
    assert parse_numeric_value("-14.2%") == -14.2
    assert parse_numeric_value("38 Generated") == 38.0
    assert parse_numeric_value(42) == 42.0
    assert parse_numeric_value(None) is None
    assert parse_numeric_value("InvalidString") is None


# ==============================================================================
# 2. Analytics Tool: get_kpi_summary
# ==============================================================================

def test_get_kpi_summary_valid(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.get_kpi_summary("30d")

    assert res["status"] == "success"
    assert res["range_type"] == "30d"
    assert res["count"] == 4
    assert res["data_source"] == "verified_mysql"
    assert res["is_seeded"] is True
    assert "Total Revenue" in res["summary"]

    kpi_ids = [k["id"] for k in res["kpis"]]
    assert "total_revenue" in kpi_ids
    assert "total_orders" in kpi_ids
    assert "growth_rate" in kpi_ids
    assert "ai_insights" in kpi_ids


def test_get_kpi_summary_unsupported_range(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.get_kpi_summary("invalid_range")

    assert res["status"] == "error"
    assert "Unsupported date range 'invalid_range'" in res["error"]


# ==============================================================================
# 3. Analytics Tool: compare_kpi_periods
# ==============================================================================

def test_compare_kpi_periods_valid(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.compare_kpi_periods(base_period="30d", target_period="7d")

    assert res["status"] == "success"
    assert res["base_period"] == "30d"
    assert res["target_period"] == "7d"
    assert res["comparisons_count"] == 4
    assert res["data_source"] == "verified_mysql"

    # Find total revenue comparison
    rev_comp = next((c for c in res["comparisons"] if c["kpi_id"] == "total_revenue"), None)
    assert rev_comp is not None
    assert rev_comp["base_numeric"] == 1284520.0
    assert rev_comp["target_numeric"] is not None
    assert rev_comp["absolute_difference"] is not None
    assert rev_comp["percentage_difference"] is not None


def test_compare_kpi_periods_filter_kpi_id(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.compare_kpi_periods(base_period="30d", target_period="7d", kpi_id="total_orders")

    assert res["status"] == "success"
    assert res["comparisons_count"] == 1
    assert res["comparisons"][0]["kpi_id"] == "total_orders"


def test_compare_kpi_periods_invalid_kpi_id(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.compare_kpi_periods(base_period="30d", target_period="7d", kpi_id="nonexistent_kpi")

    assert res["status"] == "error"
    assert "not found in database" in res["error"]


def test_compare_kpi_periods_unsupported_periods(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res_base = toolkit.compare_kpi_periods(base_period="unknown", target_period="30d")
    assert res_base["status"] == "error"
    assert "Unsupported base_period 'unknown'" in res_base["error"]

    res_target = toolkit.compare_kpi_periods(base_period="30d", target_period="unknown")
    assert res_target["status"] == "error"
    assert "Unsupported target_period 'unknown'" in res_target["error"]


def test_compare_kpi_periods_identical_periods(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.compare_kpi_periods(base_period="30d", target_period="30d")

    assert res["status"] == "success"
    assert "identical" in res["summary"]


# ==============================================================================
# 4. Analytics Tool: detect_kpi_anomalies
# ==============================================================================

def test_detect_kpi_anomalies_valid(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.detect_kpi_anomalies("30d", threshold_percent=10.0)

    assert res["status"] == "success"
    assert res["range_type"] == "30d"
    assert res["anomalies_detected"] >= 1
    assert res["data_source"] == "verified_mysql"

    # Verify EMEA CDN latency anomaly is present
    emea_anomaly = next((a for a in res["anomalies"] if a.get("kpi_id") == "regional_emea"), None)
    assert emea_anomaly is not None
    assert emea_anomaly["severity"] == "critical"
    assert "Frankfurt CDN" in emea_anomaly["description"]


def test_detect_kpi_anomalies_invalid_threshold(db_session):
    toolkit = AnalyticsToolkit(db_session)

    res_neg = toolkit.detect_kpi_anomalies("30d", threshold_percent=-1.0)
    assert res_neg["status"] == "error"
    assert "greater than 0" in res_neg["error"]

    res_high = toolkit.detect_kpi_anomalies("30d", threshold_percent=150.0)
    assert res_high["status"] == "error"
    assert "less than or equal to 100" in res_high["error"]


def test_detect_kpi_anomalies_unsupported_range(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.detect_kpi_anomalies("invalid_range")
    assert res["status"] == "error"
    assert "Unsupported date range" in res["error"]


# ==============================================================================
# 5. Analytics Tool: get_agent_status
# ==============================================================================

def test_get_agent_status_all(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.get_agent_status()

    assert res["status"] == "success"
    assert res["agent_count"] == 4
    assert res["system_health"]["all_healthy"] is True
    assert res["system_health"]["total_agents"] == 4
    assert res["system_health"]["error_count"] == 0

    agent_ids = [a["id"] for a in res["agents"]]
    assert "agent-analyst" in agent_ids
    assert "agent-rootcause" in agent_ids


def test_get_agent_status_specific_id(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.get_agent_status("agent-analyst")

    assert res["status"] == "success"
    assert res["agent_count"] == 1
    assert res["agents"][0]["name"] == "Data Analyst Agent"


def test_get_agent_status_invalid_id(db_session):
    toolkit = AnalyticsToolkit(db_session)
    res = toolkit.get_agent_status("unknown-agent-id")

    assert res["status"] == "error"
    assert "Agent 'unknown-agent-id' not found" in res["error"]
    assert "agent-analyst" in res["error"]


# ==============================================================================
# 6. LangChain BaseTool Protocol & Schema Validation
# ==============================================================================

def test_langchain_tools_generation(db_session):
    toolkit = AnalyticsToolkit(db_session)
    tools = toolkit.get_tools()

    assert len(tools) == 4
    tool_names = [t.name for t in tools]
    assert "get_kpi_summary" in tool_names
    assert "compare_kpi_periods" in tool_names
    assert "detect_kpi_anomalies" in tool_names
    assert "get_agent_status" in tool_names

    # Check descriptions and argument schemas
    for t in tools:
        assert len(t.description) > 10
        assert t.args_schema is not None


def test_langchain_tools_invoke_protocol(db_session):
    toolkit = AnalyticsToolkit(db_session)
    tools_map = {t.name: t for t in toolkit.get_tools()}

    # 1. get_kpi_summary invoke
    summary_res = tools_map["get_kpi_summary"].invoke({"range_type": "30d"})
    assert summary_res["status"] == "success"
    assert summary_res["count"] == 4

    # 2. compare_kpi_periods invoke
    cmp_res = tools_map["compare_kpi_periods"].invoke({"base_period": "30d", "target_period": "7d"})
    assert cmp_res["status"] == "success"
    assert cmp_res["comparisons_count"] == 4

    # 3. detect_kpi_anomalies invoke
    anom_res = tools_map["detect_kpi_anomalies"].invoke({"range_type": "30d", "threshold_percent": 10.0})
    assert anom_res["status"] == "success"

    # 4. get_agent_status invoke
    agent_res = tools_map["get_agent_status"].invoke({})
    assert agent_res["status"] == "success"


def test_pydantic_tool_input_validation():
    # Valid schemas
    KpiSummaryInput(range_type="30d")
    CompareKpiPeriodsInput(base_period="30d", target_period="7d")
    DetectKpiAnomaliesInput(range_type="30d", threshold_percent=15.0)
    AgentStatusInput(agent_id="agent-analyst")

    # Invalid range_type
    with pytest.raises(ValidationError):
        KpiSummaryInput(range_type="unsupported_range")  # type: ignore

    # Invalid threshold boundary (ge=0.1, le=100.0)
    with pytest.raises(ValidationError):
        DetectKpiAnomaliesInput(threshold_percent=-5.0)

    with pytest.raises(ValidationError):
        DetectKpiAnomaliesInput(threshold_percent=120.0)


# ==============================================================================
# 7. Database Error Containment
# ==============================================================================

def test_tools_database_error_handling(db_session):
    """
    Verify that if the database raises a SQLAlchemyError, tools safely return
    structured error dictionaries without crashing or leaking secrets.
    """
    toolkit = AnalyticsToolkit(db_session)

    with patch.object(db_session, "query", side_effect=SQLAlchemyError("Simulated DB connection drop")):
        summary_res = toolkit.get_kpi_summary("30d")
        assert summary_res["status"] == "error"
        assert "database error" in summary_res["error"].lower()

        cmp_res = toolkit.compare_kpi_periods("30d", "7d")
        assert cmp_res["status"] == "error"
        assert "database error" in cmp_res["error"].lower()

        anom_res = toolkit.detect_kpi_anomalies("30d")
        assert anom_res["status"] == "error"
        assert "database error" in anom_res["error"].lower()

        agent_res = toolkit.get_agent_status()
        assert agent_res["status"] == "error"
        assert "database error" in agent_res["error"].lower()


# ==============================================================================
# 8. Tool Selection and Execution
# ==============================================================================

def test_tool_selection_routing(db_session):
    toolkit = AnalyticsToolkit(db_session)

    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        # 1. Comparison query routes to compare_kpi_periods
        cmp_results = AnalyticsService.select_and_execute_tools(toolkit, "Compare 30d vs 7d metrics", "30d")
        assert any(t["tool"] == "compare_kpi_periods" for t in cmp_results)

        # 2. Anomaly query routes to detect_kpi_anomalies
        anom_results = AnalyticsService.select_and_execute_tools(toolkit, "Why did sales drop last month?", "30d")
        assert any(t["tool"] == "detect_kpi_anomalies" for t in anom_results)

        # 3. Agent query routes to get_agent_status
        agent_results = AnalyticsService.select_and_execute_tools(toolkit, "Check AI agent status and health", "30d")
        assert any(t["tool"] == "get_agent_status" for t in agent_results)

        # 4. Default overview routes to get_kpi_summary
        summary_results = AnalyticsService.select_and_execute_tools(toolkit, "What is our current revenue pace?", "30d")
        assert any(t["tool"] == "get_kpi_summary" for t in summary_results)


def test_llm_tool_selection_with_mock(db_session):
    """
    Verify that when Gemini LLM returns tool_calls, the tool router parses
    the tool calls and invokes the requested tools against MySQL.
    """
    from langchain_core.messages import AIMessage

    toolkit = AnalyticsToolkit(db_session)
    mock_ai_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "detect_kpi_anomalies",
                "args": {"range_type": "30d", "threshold_percent": 12.0},
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )

    mock_llm_instance = MagicMock()
    mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_ai_msg

    with patch("app.core.config.settings.GEMINI_API_KEY", "test-key"):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI", return_value=mock_llm_instance):
            results = AnalyticsService.select_and_execute_tools(
                toolkit,
                query="Any anomalies detected?",
                range_type="30d",
            )
            assert len(results) == 1
            assert results[0]["tool"] == "detect_kpi_anomalies"
            assert results[0]["selection_mode"] == "llm_tool_calling"
            assert results[0]["result"]["status"] == "success"
