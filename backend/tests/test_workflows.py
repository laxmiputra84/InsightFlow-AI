"""
Tests for Milestone 6: LangGraph Multi-Agent Workflow.
Verifies:
1. Graph compilation and structure
2. KPI Analyst Stage
3. Anomaly Detection Stage
4. Business Recommendations Stage
5. End-to-end graph execution across diverse queries
6. Conditional routing and bounded recursion limits
7. Node error handling and exception containment
8. Grounded recommendations without fabricated events
9. Integration with AnalyticsService and deterministic fallback
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.workflows import (
    create_analytics_workflow,
    kpi_analyst_node,
    anomaly_detection_node,
    recommendations_node,
    route_after_kpi,
    route_after_anomaly,
    DEFAULT_MAX_STEPS,
)
from app.workflows.state import AnalyticsWorkflowState
from app.services.analytics_service import AnalyticsService


# ==============================================================================
# 1. Graph Compilation & Structure
# ==============================================================================

def test_workflow_graph_compilation():
    """Verify that create_analytics_workflow compiles without error."""
    workflow = create_analytics_workflow()
    assert workflow is not None
    assert hasattr(workflow, "invoke")


# ==============================================================================
# 2. Stage 1: KPI Analyst Node
# ==============================================================================

def test_kpi_analyst_node_execution(db_session):
    """Verify KPI Analyst stage retrieves verified metrics from MySQL."""
    state: AnalyticsWorkflowState = {
        "query": "What are our revenue numbers?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "tools_called": [],
        "errors": [],
    }
    output = kpi_analyst_node(state)

    assert output["current_stage"] == "kpi_analyst"
    assert output["step_count"] == 1
    assert "get_kpi_summary" in output["tools_called"]
    assert len(output["kpi_metrics"]) == 4
    assert output["topline_revenue"] == "$1,284,520"
    assert output["order_velocity"] == "14,892"
    assert output["net_growth_rate"] == "+18.2%"


def test_kpi_analyst_node_period_comparison(db_session):
    """Verify KPI Analyst stage triggers compare_kpi_periods for comparison queries."""
    state: AnalyticsWorkflowState = {
        "query": "Compare 30d vs 7d revenue performance",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "tools_called": [],
        "errors": [],
    }
    output = kpi_analyst_node(state)

    assert "compare_kpi_periods" in output["tools_called"]
    assert output["period_comparison"] is not None
    assert output["period_comparison"]["comparisons_count"] == 4


def test_kpi_analyst_node_agent_telemetry(db_session):
    """Verify KPI Analyst stage triggers get_agent_status for agent status queries."""
    state: AnalyticsWorkflowState = {
        "query": "What is the status of our AI agents?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "tools_called": [],
        "errors": [],
    }
    output = kpi_analyst_node(state)

    assert "get_agent_status" in output["tools_called"]
    assert output["agent_telemetry"] is not None
    assert output["agent_telemetry"]["agent_count"] == 4


# ==============================================================================
# 3. Stage 2: Anomaly Detection Node
# ==============================================================================

def test_anomaly_detection_node_execution(db_session):
    """Verify Anomaly Detection stage identifies variances and root causes."""
    state: AnalyticsWorkflowState = {
        "query": "Why did sales decrease?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 1,
        "tools_called": ["get_kpi_summary"],
        "errors": [],
    }
    output = anomaly_detection_node(state)

    assert output["current_stage"] == "anomaly_detection"
    assert output["step_count"] == 2
    assert "detect_kpi_anomalies" in output["tools_called"]
    assert len(output["anomalies"]) >= 1
    assert len(output["root_causes"]) >= 1
    assert any("Frankfurt CDN" in rc for rc in output["root_causes"])


# ==============================================================================
# 4. Stage 3: Business Recommendations Node
# ==============================================================================

def test_recommendations_node_execution(db_session):
    """Verify Recommendations stage generates grounded recommendations."""
    state: AnalyticsWorkflowState = {
        "query": "Why did sales drop last month?",
        "range_type": "30d",
        "topline_revenue": "$1,284,520",
        "order_velocity": "14,892",
        "net_growth_rate": "+18.2%",
        "anomalies": [{"kpi_id": "regional_emea", "severity": "critical", "description": "Frankfurt CDN latency"}],
        "root_causes": ["420ms gateway latency surge in Frankfurt CDN node during peak checkout hours."],
        "step_count": 2,
        "tools_called": ["get_kpi_summary", "detect_kpi_anomalies"],
        "errors": [],
    }
    output = recommendations_node(state)

    assert output["current_stage"] == "business_recommendations"
    assert output["step_count"] == 3
    assert output["completed"] is True
    assert len(output["recommendations"]) >= 2
    assert len(output["key_findings"]) >= 3
    assert len(output["metric_highlights"]) >= 2
    assert output["chart_data"] is not None
    assert output["table_data"] is not None
    assert output["final_response"] is not None

    # Recommendations must be grounded in verified bottlenecks (CDN / contract delay)
    recs_text = " ".join(output["recommendations"])
    assert "CDN" in recs_text or "Frankfurt" in recs_text or "renewal" in recs_text


# ==============================================================================
# 5. End-to-End Workflow Execution
# ==============================================================================

def test_workflow_end_to_end_anomaly_flow(db_session):
    """Verify complete 3-stage execution for an anomaly query."""
    app_graph = create_analytics_workflow()
    initial_state: AnalyticsWorkflowState = {
        "query": "Why did sales decrease in EMEA last month?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "max_steps": 5,
        "tools_called": [],
        "errors": [],
    }
    final_state = app_graph.invoke(initial_state)

    assert final_state["completed"] is True
    assert final_state["step_count"] == 3
    assert "get_kpi_summary" in final_state["tools_called"]
    assert "detect_kpi_anomalies" in final_state["tools_called"]
    assert len(final_state["final_response"]["findings"]) >= 3
    assert len(final_state["final_response"]["metrics"]) >= 2
    assert final_state["final_response"]["chartData"] is not None


def test_workflow_end_to_end_comparison_flow(db_session):
    """Verify complete 3-stage execution for a comparison query."""
    app_graph = create_analytics_workflow()
    initial_state: AnalyticsWorkflowState = {
        "query": "Compare 30d vs 7d revenue performance",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "max_steps": 5,
        "tools_called": [],
        "errors": [],
    }
    final_state = app_graph.invoke(initial_state)

    assert final_state["completed"] is True
    assert "compare_kpi_periods" in final_state["tools_called"]
    assert final_state["period_comparison"] is not None
    assert "comparison" in final_state["final_response"]["content"].lower()


def test_workflow_end_to_end_agent_status_flow(db_session):
    """Verify complete 3-stage execution for an agent status query."""
    app_graph = create_analytics_workflow()
    initial_state: AnalyticsWorkflowState = {
        "query": "What is the status of our AI agents?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "max_steps": 5,
        "tools_called": [],
        "errors": [],
    }
    final_state = app_graph.invoke(initial_state)

    assert final_state["completed"] is True
    assert "get_agent_status" in final_state["tools_called"]
    assert final_state["agent_telemetry"] is not None
    assert "agent" in final_state["final_response"]["content"].lower()


# ==============================================================================
# 6. Conditional Routing & Bounded Recursion Limits
# ==============================================================================

def test_conditional_routing_bounds():
    """Verify route_after_kpi enforces bounded step limits to prevent infinite loops."""
    # Under limit: proceeds to anomaly_detection
    normal_state: AnalyticsWorkflowState = {"step_count": 1, "max_steps": 5}
    assert route_after_kpi(normal_state) == "anomaly_detection"

    # At or exceeding limit: bypasses to recommendations
    bounded_state: AnalyticsWorkflowState = {"step_count": 5, "max_steps": 5}
    assert route_after_kpi(bounded_state) == "recommendations"

    # route_after_anomaly always routes forward to recommendations
    assert route_after_anomaly(normal_state) == "recommendations"


# ==============================================================================
# 7. Node Error Handling & Exception Containment
# ==============================================================================

def test_kpi_analyst_node_database_error_handling(db_session):
    """Verify that KPI Analyst node safely contains database errors."""
    with patch.object(db_session, "query", side_effect=SQLAlchemyError("DB connection dropped")):
        state: AnalyticsWorkflowState = {
            "query": "Show KPI metrics",
            "range_type": "30d",
            "db_session": db_session,
            "step_count": 0,
            "tools_called": [],
            "errors": [],
        }
        output = kpi_analyst_node(state)

        assert output["step_count"] == 1
        assert len(output["errors"]) >= 1
        # Safe default baselines provided
        assert output["topline_revenue"] is not None


def test_anomaly_detection_node_database_error_handling(db_session):
    """Verify that Anomaly Detection node safely contains database errors."""
    with patch.object(db_session, "query", side_effect=SQLAlchemyError("DB query failed")):
        state: AnalyticsWorkflowState = {
            "query": "Check anomalies",
            "range_type": "30d",
            "db_session": db_session,
            "step_count": 1,
            "tools_called": [],
            "errors": [],
        }
        output = anomaly_detection_node(state)

        assert output["step_count"] == 2
        assert len(output["errors"]) >= 1
        assert output["safe_status"] is True


def test_nodes_without_database_session():
    """Verify nodes handle missing db_session gracefully without raising unhandled exceptions."""
    state: AnalyticsWorkflowState = {"query": "test", "step_count": 0, "errors": []}

    kpi_out = kpi_analyst_node(state)
    assert len(kpi_out["errors"]) >= 1
    assert kpi_out["topline_revenue"] is not None

    anom_out = anomaly_detection_node(state)
    assert len(anom_out["errors"]) >= 1
    assert anom_out["safe_status"] is True


# ==============================================================================
# 8. Integration with AnalyticsService & Fallback
# ==============================================================================

def test_analytics_service_run_langgraph_workflow(db_session):
    """Verify AnalyticsService.run_langgraph_workflow invokes the compiled graph."""
    res = AnalyticsService.run_langgraph_workflow(
        db=db_session,
        query="Why did sales decrease?",
        range_type="30d",
    )
    assert res["completed"] is True
    assert res["step_count"] == 3
    assert res["final_response"] is not None


def test_analytics_service_generate_response_uses_workflow(db_session):
    """Verify generate_analytics_response returns grounded response with LangGraph."""
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        response = AnalyticsService.generate_analytics_response(
            db=db_session,
            query="Why did sales decrease last month?",
            range_type="30d",
        )
        assert response.sender == "assistant"
        assert len(response.findings) >= 3
        assert len(response.metrics) >= 2
        assert response.dataSource.modelUsed == "mysql-grounded-analytics-engine"
