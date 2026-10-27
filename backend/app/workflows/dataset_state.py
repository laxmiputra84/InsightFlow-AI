"""
InsightFlow AI - Dataset LangGraph Shared Workflow State Definitions.
Defines the strongly-typed shared state passed across the 6 dataset agents:
1. Data Understanding Agent
2. Data Cleaning Agent
3. Business Analyst Agent
4. Anomaly and Data Quality Agent
5. Forecasting Agent
6. Dashboard Generation and Recommendations Agent
"""
from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd


class AgentExecutionMetadata(TypedDict, total=False):
    agent_id: str
    agent_name: str
    status: str
    execution_time_ms: int
    input_summary: str
    findings: List[str]
    metrics: Dict[str, Any]
    recommendations: Optional[List[str]]
    citations: List[str]
    errors: List[str]
    timestamp: str


class CleaningRule(TypedDict, total=False):
    rule_id: str
    rule_name: str
    description: str
    affected_rows: int
    target_columns: List[str]
    enabled: bool


class CleaningPreviewData(TypedDict, total=False):
    total_original_rows: int
    total_cleaned_rows: int
    duplicates_removed: int
    missing_cells_imputed: int
    whitespace_trimmed_cells: int
    anomalous_rows_adjusted: int
    proposed_rules: List[CleaningRule]
    before_sample: List[Dict[str, Any]]
    after_sample: List[Dict[str, Any]]
    approval_required: bool


class DatasetWorkflowState(TypedDict, total=False):
    """
    Shared typed state for the 6-agent dataset-driven BI workflow.
    Guarantees isolation, traceability, and validated data-passing between agents.
    """
    # Core Dataset Context
    dataset_id: str
    dataset_name: str
    file_path: str
    file_type: str
    row_count: int
    column_count: int
    query: Optional[str]
    
    # Internal execution context
    df: Any  # pd.DataFrame
    detected_mappings: Dict[str, Any]
    step_count: int
    max_steps: int
    errors: List[str]
    warnings: List[str]

    # Telemetry for all agents
    agent_telemetry: Dict[str, AgentExecutionMetadata]

    # Agent 1: Data Understanding
    understanding_result: Dict[str, Any]

    # Agent 2: Data Cleaning (Preview only, never destructive without approval)
    cleaning_plan: Dict[str, Any]
    cleaning_preview: CleaningPreviewData

    # Agent 3: Business Analyst
    business_result: Dict[str, Any]

    # Agent 4: Anomaly and Data Quality
    anomaly_result: Dict[str, Any]

    # Agent 5: Forecasting
    is_forecast_eligible: bool
    forecast_result: Dict[str, Any]

    # Agent 6: Dashboard Generation and Recommendations
    dashboard_layout: Dict[str, Any]
    recommendations: List[str]
    executive_summary: str
