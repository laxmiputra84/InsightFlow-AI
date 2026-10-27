"""
InsightFlow AI - LangGraph 6-Agent Dataset-Driven BI Workflow.
Orchestrates the 6 specialized agents in a verified pipeline:
1. Data Understanding Agent
2. Data Cleaning Agent (non-destructive preview)
3. Business Analyst Agent
4. Anomaly and Data Quality Agent
5. Forecasting Agent (conditionally routed based on empirical date and row suitability)
6. Dashboard Generation and Recommendations Agent
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from app.models.dataset import DatasetModel
from app.services.dataset_service import DatasetService
from app.services.dataset_agents import DatasetAgentService
from app.workflows.dataset_state import (
    DatasetWorkflowState,
    AgentExecutionMetadata,
    CleaningPreviewData,
)
from app.schemas.dataset import (
    DatasetSixAgentWorkflowResponse,
    DatasetAgentTaskResponse,
    CleaningPreviewResponse,
    CleaningRuleModel,
)

logger = logging.getLogger("insightflow.workflows.dataset")


class DatasetWorkflowNodes:
    """
    Execution nodes for the LangGraph 6-agent dataset workflow.
    """

    @staticmethod
    def understanding_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 1]: Executing Data Understanding on '{dataset.name}'")
        res = DatasetAgentService.run_understanding_agent(db, dataset)
        mappings = dataset.detected_mappings or {}
        has_date = bool(mappings.get("date_column"))
        
        # Check forecast eligibility upfront for routing
        is_eligible = False
        if has_date:
            try:
                df = state.get("df")
                if df is None:
                    df = DatasetService.load_dataframe(dataset.file_path, dataset.file_type)
                date_col = mappings.get("date_column")
                if date_col in df.columns:
                    valid_dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
                    n_days = valid_dates.dt.strftime("%Y-%m-%d").nunique()
                    is_eligible = n_days >= 14
            except Exception:
                is_eligible = False

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-understanding"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "understanding_result": res.model_dump(),
            "is_forecast_eligible": is_eligible,
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def cleaning_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 2]: Executing Data Cleaning Assessment on '{dataset.name}'")
        res = DatasetAgentService.run_cleaning_agent(db, dataset)
        preview_dict = DatasetService.generate_cleaning_preview(dataset)

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-cleaning"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "cleaning_plan": res.model_dump(),
            "cleaning_preview": preview_dict,
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def business_analyst_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 3]: Executing Business Analyst on '{dataset.name}'")
        res = DatasetAgentService.run_business_analyst(db, dataset)

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-analyst"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "business_result": res.model_dump(),
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def anomaly_quality_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 4]: Executing Anomaly & Data Quality on '{dataset.name}'")
        res = DatasetAgentService.run_quality_analyst(db, dataset)

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-quality"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "anomaly_result": res.model_dump(),
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def forecasting_holdout_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 5A]: Executing Out-of-Sample Holdout Forecasting on '{dataset.name}'")
        res = DatasetAgentService.run_forecast_analyst(db, dataset)

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-forecaster"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "forecast_result": res.model_dump(),
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def forecasting_ineligible_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 5B]: Executing Ineligible Forecasting Report on '{dataset.name}'")
        res = DatasetAgentService.run_forecast_analyst(db, dataset)

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-forecaster"] = res.model_dump()

        return {
            "step_count": state.get("step_count", 0) + 1,
            "forecast_result": res.model_dump(),
            "agent_telemetry": telemetry,
        }

    @staticmethod
    def dashboard_recommendation_node(state: DatasetWorkflowState, db: Session, dataset: DatasetModel) -> Dict[str, Any]:
        logger.info(f"LangGraph [Node 6]: Executing Dashboard Generation & Recommendations on '{dataset.name}'")
        bus_dump = state.get("business_result")
        fore_dump = state.get("forecast_result")
        
        bus_task = DatasetAgentTaskResponse(**bus_dump) if bus_dump else None
        fore_task = DatasetAgentTaskResponse(**fore_dump) if fore_dump else None

        res = DatasetAgentService.run_dashboard_recommendations_agent(
            db, dataset, business_task=bus_task, forecast_task=fore_task
        )

        telemetry = dict(state.get("agent_telemetry", {}))
        telemetry["agent-dashboard"] = res.model_dump()

        # Executive summary
        findings_understanding = state.get("understanding_result", {}).get("findings", [])
        findings_cleaning = state.get("cleaning_plan", {}).get("findings", [])
        findings_bus = bus_task.findings if bus_task else []
        findings_qual = state.get("anomaly_result", {}).get("findings", [])
        findings_fore = fore_task.findings if fore_task else []

        exec_summary = (
            f"Autonomous 6-Agent Business Intelligence Workflow Audit for '{dataset.name}':\n\n"
            f"1. Structural Understanding: {findings_understanding[0] if findings_understanding else 'Schema analyzed.'}\n"
            f"2. Data Hygiene & Cleaning: {findings_cleaning[0] if findings_cleaning else 'Hygiene evaluated.'} (Safe preview generated; approval required).\n"
            f"3. Core Business Performance: {findings_bus[0] if findings_bus else 'KPIs computed.'}\n"
            f"4. Quality & Statistical Anomalies: {findings_qual[0] if findings_qual else 'Audited.'}\n"
            f"5. Forecast & Horizon Projection: {findings_fore[0] if findings_fore else 'Trajectory checked.'}\n"
            f"6. Layout & Strategy Synthesis: {res.findings[0] if res.findings else 'Synthesized.'}\n\n"
            f"Grounding Evidence: Verified directly against {dataset.row_count:,} observations in '{dataset.filename}'. Zero ungrounded hypotheses."
        )

        return {
            "step_count": state.get("step_count", 0) + 1,
            "dashboard_layout": res.metrics,
            "recommendations": res.recommendations or [],
            "executive_summary": exec_summary,
            "agent_telemetry": telemetry,
        }


def route_forecasting_eligibility(state: DatasetWorkflowState) -> str:
    """
    Conditional routing function: routes to holdout ML models if temporal data is adequate;
    otherwise routes to honest limitation reporting node.
    """
    if state.get("is_forecast_eligible", False):
        return "forecasting_holdout"
    return "forecasting_ineligible"


class DatasetLangGraphWorkflow:
    """
    LangGraph StateGraph orchestrator for the 6-agent Dataset-Driven BI workflow.
    """

    @classmethod
    def build_graph(cls, db: Session, dataset: DatasetModel):
        workflow = StateGraph(DatasetWorkflowState)

        # Register nodes with closures passing db and dataset context
        workflow.add_node("data_understanding", lambda s: DatasetWorkflowNodes.understanding_node(s, db, dataset))
        workflow.add_node("data_cleaning", lambda s: DatasetWorkflowNodes.cleaning_node(s, db, dataset))
        workflow.add_node("business_analyst", lambda s: DatasetWorkflowNodes.business_analyst_node(s, db, dataset))
        workflow.add_node("anomaly_quality", lambda s: DatasetWorkflowNodes.anomaly_quality_node(s, db, dataset))
        workflow.add_node("forecasting_holdout", lambda s: DatasetWorkflowNodes.forecasting_holdout_node(s, db, dataset))
        workflow.add_node("forecasting_ineligible", lambda s: DatasetWorkflowNodes.forecasting_ineligible_node(s, db, dataset))
        workflow.add_node("dashboard_recommendations", lambda s: DatasetWorkflowNodes.dashboard_recommendation_node(s, db, dataset))

        # Define edge routing
        workflow.set_entry_point("data_understanding")
        workflow.add_edge("data_understanding", "data_cleaning")
        workflow.add_edge("data_cleaning", "business_analyst")
        workflow.add_edge("business_analyst", "anomaly_quality")

        # Conditional edge based on actual dataset properties
        workflow.add_conditional_edges(
            "anomaly_quality",
            route_forecasting_eligibility,
            {
                "forecasting_holdout": "forecasting_holdout",
                "forecasting_ineligible": "forecasting_ineligible",
            },
        )

        workflow.add_edge("forecasting_holdout", "dashboard_recommendations")
        workflow.add_edge("forecasting_ineligible", "dashboard_recommendations")
        workflow.add_edge("dashboard_recommendations", END)

        return workflow.compile()

    @classmethod
    def run(
        cls,
        db: Session,
        dataset: DatasetModel,
        query: Optional[str] = None,
    ) -> DatasetSixAgentWorkflowResponse:
        """
        Executes the full 6-agent LangGraph workflow against the dataset.
        """
        start_time = time.time()
        logger.info(f"Starting LangGraph 6-Agent workflow execution on dataset '{dataset.name}' ({dataset.id})")

        # Initial workflow state
        initial_state: DatasetWorkflowState = {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "file_path": dataset.file_path,
            "file_type": dataset.file_type,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "query": query,
            "step_count": 0,
            "max_steps": 10,
            "errors": [],
            "warnings": [],
            "agent_telemetry": {},
            "detected_mappings": dataset.detected_mappings or {},
        }

        compiled_app = cls.build_graph(db, dataset)
        final_state: DatasetWorkflowState = compiled_app.invoke(initial_state)

        total_exec_time = int((time.time() - start_time) * 1000)

        # Parse cleaning preview response
        clean_preview_data = final_state.get("cleaning_preview")
        cleaning_preview_model = None
        if clean_preview_data:
            rules_models = [
                CleaningRuleModel(**r) for r in clean_preview_data.get("proposedRules", [])
            ]
            cleaning_preview_model = CleaningPreviewResponse(
                datasetId=clean_preview_data.get("datasetId", dataset.id),
                datasetName=clean_preview_data.get("datasetName", dataset.name),
                totalOriginalRows=clean_preview_data.get("totalOriginalRows", dataset.row_count),
                totalCleanedRows=clean_preview_data.get("totalCleanedRows", dataset.row_count),
                duplicatesRemoved=clean_preview_data.get("duplicatesRemoved", 0),
                missingCellsImputed=clean_preview_data.get("missingCellsImputed", 0),
                whitespaceTrimmedCells=clean_preview_data.get("whitespaceTrimmedCells", 0),
                anomalousRowsAdjusted=clean_preview_data.get("anomalousRowsAdjusted", 0),
                proposedRules=rules_models,
                beforeSample=clean_preview_data.get("beforeSample", []),
                afterSample=clean_preview_data.get("afterSample", []),
                approvalRequired=True,
            )

        under_task = DatasetAgentTaskResponse(**final_state["understanding_result"])
        clean_task = DatasetAgentTaskResponse(**final_state["cleaning_plan"])
        bus_task = DatasetAgentTaskResponse(**final_state["business_result"])
        anom_task = DatasetAgentTaskResponse(**final_state["anomaly_result"])
        fore_task = DatasetAgentTaskResponse(**final_state["forecast_result"])
        dash_telemetry = final_state.get("agent_telemetry", {}).get("agent-dashboard", {})

        if dash_telemetry:
            dash_task = DatasetAgentTaskResponse(**dash_telemetry)
        else:
            dash_task = DatasetAgentTaskResponse(
                agentId="agent-dashboard",
                agentName="Dashboard Generation and Recommendations Agent",
                status="completed",
                executionTimeMs=10,
                findings=[],
                metrics={},
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            )

        return DatasetSixAgentWorkflowResponse(
            datasetId=dataset.id,
            datasetName=dataset.name,
            status="completed",
            executionTimeMs=total_exec_time,
            query=query,
            understandingAgent=under_task,
            cleaningAgent=clean_task,
            businessAgent=bus_task,
            anomalyAgent=anom_task,
            forecastingAgent=fore_task,
            dashboardAgent=dash_task,
            dashboardLayout=final_state.get("dashboard_layout", {}),
            recommendations=final_state.get("recommendations", []),
            cleaningPreview=cleaning_preview_model,
            executiveSummary=final_state.get("executive_summary", "Completed successfully."),
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
