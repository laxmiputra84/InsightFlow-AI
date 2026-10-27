"""
InsightFlow AI - LangGraph Shared State Definitions.
Defines the strongly-typed shared state passed across specialized workflow nodes:
1. KPI Analyst Node
2. Anomaly Detection Node
3. Business Recommendations Node
"""
from typing import TypedDict, List, Dict, Any, Optional


class AnalyticsWorkflowState(TypedDict, total=False):
    """
    Typed shared state dictionary for the LangGraph multi-agent analytics workflow.
    Guarantees consistent data passing between stages without arbitrary mutation.
    """
    # 1. Inputs & Execution Parameters
    query: str
    range_type: str
    db_session: Any  # SQLAlchemy Session for approved tool execution
    step_count: int
    max_steps: int
    current_stage: str
    errors: List[str]
    tools_called: List[str]

    # 2. Stage 1: KPI Analyst Outputs
    kpi_metrics: List[Dict[str, Any]]
    kpi_summary: Dict[str, Any]
    period_comparison: Optional[Dict[str, Any]]
    agent_telemetry: Optional[Dict[str, Any]]
    topline_revenue: str
    order_velocity: str
    net_growth_rate: str

    # Controlled RAG Document Evidence
    requires_document_knowledge: bool
    has_document_evidence: bool
    document_evidence: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]

    # Predictive Forecasting Capability
    is_forecast_query: bool
    has_forecast: bool
    forecast_data: Optional[Dict[str, Any]]


    # 3. Stage 2: Anomaly Detection Outputs
    anomalies: List[Dict[str, Any]]
    critical_anomalies_count: int
    has_critical_anomaly: bool
    safe_status: bool
    root_causes: List[str]
    anomaly_summary: str

    # 4. Stage 3: Business Recommendations & Synthesis Outputs
    recommendations: List[str]
    key_findings: List[str]
    metric_highlights: List[Dict[str, Any]]
    chart_data: Optional[Dict[str, Any]]
    table_data: Optional[Dict[str, Any]]
    suggested_follow_ups: List[str]
    narrative_content: str
    final_response: Dict[str, Any]
    model_used: str
    completed: bool
