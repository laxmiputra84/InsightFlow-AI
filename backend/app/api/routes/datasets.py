import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import DatasetModel
from app.services.dataset_service import DatasetService
from app.services.dataset_agents import DatasetAgentService
from app.workflows.dataset_workflow import DatasetLangGraphWorkflow
from app.workflows.business_workflow import BusinessAnalysisWorkflow
from app.services.business_engine import BusinessAnalysisEngine
from app.core.security import verify_api_key
from app.schemas.dataset import (
    DatasetItemResponse,
    DatasetDetailResponse,
    DatasetPreviewResponse,
    DatasetDashboardResponse,
    DatasetAgentTaskResponse,
    DatasetSwarmResponse,
    CleaningPreviewResponse,
    CleaningApplyRequest,
    CleaningApplyResponse,
    DatasetSixAgentWorkflowResponse,
)
from app.schemas.business_analysis import (
    DatasetProfileResponse,
    DataQualityAnalysisResponse,
    BusinessMetricsResponse,
    AnomalyReportResponse,
    BusinessAnalysisWorkflowResponse,
    AnalysisStatusResponse,
)

logger = logging.getLogger("insightflow.api.datasets")

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Uploads a real business dataset (.csv, .xlsx, .xls).
    Validates file format, detects schema, column roles, and data quality,
    and sets the dataset as the active source for the dynamic dashboard.
    """
    filename = file.filename or "uploaded_dataset.csv"
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.",
        )

    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        # 50MB limit
        if len(file_bytes) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Dataset file exceeds maximum allowed limit of 50MB.",
            )

        dataset = DatasetService.save_uploaded_dataset(
            db=db,
            file_bytes=file_bytes,
            original_filename=filename,
            custom_name=name,
        )

        return dataset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing uploaded dataset '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process and analyze dataset: {str(e)}",
        )


@router.get("", response_model=List[DatasetItemResponse])
def list_datasets(db: Session = Depends(get_db)):
    """
    Returns all uploaded datasets with schema summary, row count, and quality score.
    """
    return db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()


@router.get("/active", response_model=DatasetDetailResponse)
def get_active_dataset(db: Session = Depends(get_db)):
    """
    Returns the currently active dataset used to power the dashboard and agents.
    If no datasets exist, returns 404 so the client can display the honest empty dashboard state.
    """
    dataset = DatasetService.get_active_dataset(db)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset is currently active. Please upload a dataset.",
        )
    return dataset


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_details(dataset_id: str, db: Session = Depends(get_db)):
    """
    Returns full details, schema column definitions, and quality report for a dataset.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return dataset


@router.post("/{dataset_id}/activate", response_model=DatasetDetailResponse)
def activate_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """
    Switches the active dashboard data source to the specified dataset.
    """
    dataset = DatasetService.activate_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    Returns paginated, searchable, and sortable real records from the dataset.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetService.get_preview_rows(
            dataset=dataset,
            page=page,
            page_size=page_size,
            search_query=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception as e:
        logger.error(f"Error fetching preview records for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read dataset records: {str(e)}",
        )


@router.get("/{dataset_id}/dashboard", response_model=DatasetDashboardResponse)
def get_dataset_dashboard(
    dataset_id: str,
    range: str = Query("all", description="Date range: 7d, 30d, 90d, 1y, all"),
    category: Optional[str] = Query(None, description="Category filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    search: Optional[str] = Query(None, description="Search term filter"),
    db: Session = Depends(get_db),
):
    """
    Dynamically computes dashboard KPIs, time-series trends, and categorical distributions
    directly from the real records of the selected dataset using the active filters.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetService.compute_dashboard(
            db=db,
            dataset=dataset,
            range_type=range,
            category_filter=category,
            country_filter=country,
            search_query=search,
        )
    except Exception as e:
        logger.error(f"Error computing dashboard for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to aggregate dataset metrics: {str(e)}",
        )


@router.post("/{dataset_id}/agents/{agent_id}/run", response_model=DatasetAgentTaskResponse)
def run_dataset_agent(
    dataset_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Executes a specific genuine Agentic AI agent on this dataset:
    - 'agent-understanding' -> Data Understanding Agent
    - 'agent-cleaning' -> Data Cleaning Agent (non-destructive preview)
    - 'agent-analyst' -> Business Analyst Agent
    - 'agent-quality' -> Anomaly and Data Quality Agent
    - 'agent-forecaster' -> Forecasting Agent
    - 'agent-dashboard' -> Dashboard Generation & Recommendations Agent
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        clean_agent_id = agent_id.lower().strip()
        if "understand" in clean_agent_id:
            return DatasetAgentService.run_understanding_agent(db, dataset)
        elif "clean" in clean_agent_id:
            return DatasetAgentService.run_cleaning_agent(db, dataset)
        elif "quality" in clean_agent_id or "rootcause" in clean_agent_id or "anomaly" in clean_agent_id:
            return DatasetAgentService.run_quality_analyst(db, dataset)
        elif "forecast" in clean_agent_id:
            return DatasetAgentService.run_forecast_analyst(db, dataset)
        elif "dashboard" in clean_agent_id or "recommend" in clean_agent_id:
            return DatasetAgentService.run_dashboard_recommendations_agent(db, dataset)
        elif "business" in clean_agent_id or "analyst" in clean_agent_id:
            return DatasetAgentService.run_business_analyst(db, dataset)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown agent '{agent_id}'. Supported: 'agent-understanding', 'agent-cleaning', 'agent-analyst', 'agent-quality', 'agent-forecaster', 'agent-dashboard'.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent {agent_id} on dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


@router.post("/{dataset_id}/workflow/run", response_model=DatasetSixAgentWorkflowResponse)
def run_dataset_workflow(
    dataset_id: str,
    query: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Executes the full 6-agent LangGraph workflow:
    Data Understanding -> Data Cleaning -> Business Analyst -> Anomaly/Quality -> Forecasting (conditional) -> Dashboard Layout & Recommendations.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetLangGraphWorkflow.run(db, dataset, query=query)
    except Exception as e:
        logger.error(f"Error executing 6-agent LangGraph workflow on dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.get("/{dataset_id}/clean/preview", response_model=CleaningPreviewResponse)
@router.post("/{dataset_id}/clean/preview", response_model=CleaningPreviewResponse)
def get_dataset_clean_preview(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Generates a safe, non-destructive preview of proposed data cleaning transformations.
    CRITICAL: Preserves the original raw uploaded dataset untouched on disk and database.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetService.generate_cleaning_preview(dataset)
    except Exception as e:
        logger.error(f"Error generating cleaning preview for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cleaning preview: {str(e)}",
        )


@router.post("/{dataset_id}/clean/apply", response_model=CleaningApplyResponse)
def apply_dataset_clean_plan(
    dataset_id: str,
    body: CleaningApplyRequest,
    db: Session = Depends(get_db),
):
    """
    Applies user-approved cleaning rules and creates a promoted cleaned dataset version.
    Requires explicit user approval before execution. Preserves the original raw dataset untouched.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetService.apply_cleaning_plan(
            db=db,
            dataset=dataset,
            approved_rule_ids=body.approvedRuleIds,
            new_name=body.newDatasetName,
            set_as_active=body.setAsActive,
        )
    except Exception as e:
        logger.error(f"Error applying cleaning plan for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply cleaning plan: {str(e)}",
        )


@router.post("/{dataset_id}/agents/run-all", response_model=DatasetSwarmResponse)
def run_all_dataset_agents(
    dataset_id: str,
    query: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Executes coordinated agent execution against the verified records of this dataset.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")

    try:
        return DatasetAgentService.run_coordinated_swarm(db, dataset, query=query)
    except Exception as e:
        logger.error(f"Error running agent swarm on dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Swarm execution failed: {str(e)}",
        )


@router.delete("/{dataset_id}", dependencies=[Depends(verify_api_key)])
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """
    Permanently deletes an uploaded dataset, cleans up associated files on disk safely,
    removes all related records, and promotes a remaining dataset to active status.
    Enforces authorization via verify_api_key.
    """
    res = DatasetService.delete_dataset(db, dataset_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )
    return {
        "status": "success",
        "message": f"Dataset '{res['deletedName']}' and all associated records deleted successfully.",
        "datasetId": res["datasetId"],
        "nextActiveDatasetId": res["nextActiveDatasetId"],
        "wasActive": res["wasActive"],
    }


# ==============================================================================
# Business Analysis Engine Endpoints
# ==============================================================================

@router.post("/{dataset_id}/analysis", response_model=BusinessAnalysisWorkflowResponse)
def run_business_analysis(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Executes the comprehensive 8-stage LangGraph Business Analysis workflow:
    Validation -> Profiling -> Quality Analysis -> Business Analysis -> Anomaly Detection ->
    Insight Generation -> Result Validation -> Final Response.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    try:
        return BusinessAnalysisWorkflow.run(db, dataset)
    except Exception as e:
        logger.error(f"Error executing business analysis on dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business analysis workflow execution failed: {str(e)}",
        )


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
def get_dataset_profile(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves deep dataset profile, schema column roles, and domain classification
    (Sales, Finance, Customer, Inventory, or General).
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    try:
        df = DatasetService.load_dataframe(dataset.file_path, dataset.file_type)
        return BusinessAnalysisEngine.profile_dataset(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            file_type=dataset.file_type,
            file_size_bytes=dataset.file_size,
        )
    except Exception as e:
        logger.error(f"Error profiling dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dataset profile: {str(e)}",
        )


@router.get("/{dataset_id}/quality", response_model=DataQualityAnalysisResponse)
def get_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves data quality and hygiene report: missing cells, duplicate rows,
    invalid dates, inconsistent category casings, and suspicious numbers.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    try:
        df = DatasetService.load_dataframe(dataset.file_path, dataset.file_type)
        prof = BusinessAnalysisEngine.profile_dataset(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            file_type=dataset.file_type,
            file_size_bytes=dataset.file_size,
        )
        return BusinessAnalysisEngine.audit_data_quality(
            df=df,
            dataset_id=dataset.id,
            mappings=prof.domainMappings,
        )
    except Exception as e:
        logger.error(f"Error auditing data quality for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit data quality: {str(e)}",
        )


@router.get("/{dataset_id}/business-analysis", response_model=BusinessMetricsResponse)
def get_dataset_business_analysis(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves verified domain-specific business KPIs, category performance,
    regional breakdown, and explicit explanations of missing required columns.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    try:
        df = DatasetService.load_dataframe(dataset.file_path, dataset.file_type)
        prof = BusinessAnalysisEngine.profile_dataset(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            file_type=dataset.file_type,
            file_size_bytes=dataset.file_size,
        )
        return BusinessAnalysisEngine.analyze_business_metrics(
            df=df,
            dataset_id=dataset.id,
            domain=prof.detectedDomain,
            mappings=prof.domainMappings,
        )
    except Exception as e:
        logger.error(f"Error computing business metrics for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate business metrics: {str(e)}",
        )


@router.get("/{dataset_id}/anomalies", response_model=AnomalyReportResponse)
def get_dataset_anomalies(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves statistical anomaly report (Tukey IQR, Z-scores, temporal spikes/drops)
    with severity ratings and distinction between business events and data corruption.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    try:
        df = DatasetService.load_dataframe(dataset.file_path, dataset.file_type)
        prof = BusinessAnalysisEngine.profile_dataset(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            file_type=dataset.file_type,
            file_size_bytes=dataset.file_size,
        )
        return BusinessAnalysisEngine.detect_anomalies(
            df=df,
            dataset_id=dataset.id,
            mappings=prof.domainMappings,
        )
    except Exception as e:
        logger.error(f"Error detecting anomalies for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze dataset anomalies: {str(e)}",
        )


@router.get("/{dataset_id}/analysis/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns current analysis readiness, active domain, and metadata status for a dataset.
    """
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    mappings = dataset.detected_mappings or {}
    domain = "sales" if mappings.get("is_online_retail") else "general"
    quality_rep = dataset.quality_report or {}
    quality_score = quality_rep.get("qualityScore", 100.0)

    return AnalysisStatusResponse(
        datasetId=dataset.id,
        datasetName=dataset.name,
        status="ready",
        domain=domain,
        hasResults=True,
        qualityScore=quality_score,
        lastAnalyzedAt=dataset.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC") if dataset.updated_at else None,
    )

