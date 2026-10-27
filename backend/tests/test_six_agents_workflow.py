import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.dataset import DatasetModel
from app.services.dataset_service import DatasetService
from app.services.dataset_agents import DatasetAgentService
from app.workflows.dataset_workflow import DatasetLangGraphWorkflow


import uuid

@pytest.fixture
def sample_retail_dataset(db_session: Session):
    """
    Creates a temporary verified retail CSV dataset with 30 days of data and cancellations.
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    records = []
    base_date = datetime(2026, 9, 1)
    for i in range(100):
        d = base_date + timedelta(days=(i % 25))
        is_cancel = (i % 20 == 0)
        qty = -2 if is_cancel else (i % 5 + 1)
        invoice = f"C{1000 + i}" if is_cancel else f"{1000 + i}"
        records.append({
            "InvoiceNo": invoice,
            "StockCode": f"SKU_{i % 8}",
            "Description": f"Product Category {i % 4} Item",
            "Quantity": qty,
            "InvoiceDate": d.strftime("%Y-%m-%d %H:%M"),
            "UnitPrice": 10.0 + (i % 3),
            "CustomerID": 12000 + (i % 10),
            "Country": "United Kingdom" if i % 2 == 0 else "Germany",
        })

    # Add 2 duplicate rows to verify cleaning preview
    records.append(records[0].copy())
    records.append(records[1].copy())

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)

    cols_schema, mappings, quality_rep = DatasetService.analyze_schema_and_mappings(df)

    ds_id = f"ds_retail_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Test Retail Dataset",
        filename="test_retail.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=True,
        columns_schema=cols_schema,
        detected_mappings=mappings,
        quality_report=quality_rep,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        row = db_session.query(DatasetModel).filter(DatasetModel.id == ds_id).first()
        if row:
            db_session.delete(row)
            db_session.commit()
    except Exception:
        db_session.rollback()

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def sample_no_date_dataset(db_session: Session):
    """
    Creates a temporary dataset with no date column to verify forecasting ineligibility routing.
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    df = pd.DataFrame({
        "ProductID": [f"P{i}" for i in range(20)],
        "Category": ["Electronics" if i % 2 == 0 else "Office" for i in range(20)],
        "Price": [15.5 * (i + 1) for i in range(20)],
        "StockQuantity": [50 + i for i in range(20)],
    })
    df.to_csv(path, index=False)

    cols_schema, mappings, quality_rep = DatasetService.analyze_schema_and_mappings(df)

    ds_id = f"ds_nodate_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Test No Date Dataset",
        filename="test_nodate.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=False,
        columns_schema=cols_schema,
        detected_mappings=mappings,
        quality_report=quality_rep,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        row = db_session.query(DatasetModel).filter(DatasetModel.id == ds_id).first()
        if row:
            db_session.delete(row)
            db_session.commit()
    except Exception:
        db_session.rollback()

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def test_agent_1_data_understanding(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Data Understanding Agent inspects schema and semantic roles."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-understanding/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-understanding"
    assert data["status"] == "completed"
    assert data["metrics"]["totalRows"] == 102
    assert data["metrics"]["totalColumns"] == 8
    assert len(data["findings"]) >= 2
    assert len(data["citations"]) >= 1


def test_agent_2_data_cleaning_safe_preview(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Data Cleaning Agent formulates a non-destructive preview and requires approval."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-cleaning/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-cleaning"
    assert data["status"] == "completed"
    assert data["metrics"]["approvalRequired"] is True
    assert data["metrics"]["duplicatesDetected"] == 2
    # Verify raw file was NOT mutated
    orig_df = pd.read_csv(sample_retail_dataset.file_path)
    assert len(orig_df) == 102


def test_agent_3_business_analyst(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Business Analyst computes verified KPIs from real records."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-analyst/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-analyst"
    assert data["status"] == "completed"
    assert data["metrics"]["totalRecords"] == 102
    assert data["metrics"]["totalRevenue"] > 0
    assert len(data["citations"]) >= 2


def test_agent_4_anomaly_quality(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Anomaly and Quality Agent distinguishes cancellations from corruption."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-quality/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-quality"
    assert data["status"] == "completed"
    assert "qualityScore" in data["metrics"]
    # Check that cancellation orders were noted in findings
    cancellation_finding = any("cancellation" in f.lower() or "return" in f.lower() for f in data["findings"])
    assert cancellation_finding is True


def test_agent_5_forecasting_eligible(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Forecasting Agent evaluates models when >=14 date points exist."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-forecaster/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-forecaster"
    assert data["status"] == "completed"
    assert data["metrics"]["isEligible"] is True
    assert "holdoutRmse" in data["metrics"]
    assert "naiveBaselineRmse" in data["metrics"]
    assert len(data["recommendations"]) > 0


def test_agent_5_forecasting_ineligible(client: TestClient, sample_no_date_dataset: DatasetModel):
    """Test Forecasting Agent reports limitations truthfully when no date exists."""
    res = client.post(f"/api/datasets/{sample_no_date_dataset.id}/agents/agent-forecaster/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-forecaster"
    assert data["status"] == "completed"
    assert data["metrics"]["isEligible"] is False
    assert "Missing date column" in data["metrics"]["reason"]


def test_agent_6_dashboard_recommendations(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test Dashboard Generation & Recommendations Agent synthesizes layout."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/agent-dashboard/run")
    assert res.status_code == 200
    data = res.json()
    assert data["agentId"] == "agent-dashboard"
    assert data["status"] == "completed"
    assert data["metrics"]["recommendedWidgetsCount"] >= 3
    assert len(data["recommendations"]) >= 1


def test_full_6_agent_workflow_langgraph(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test complete LangGraph 6-agent workflow orchestration with typed state."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/workflow/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["datasetId"] == sample_retail_dataset.id
    assert data["understandingAgent"]["status"] == "completed"
    assert data["cleaningAgent"]["status"] == "completed"
    assert data["businessAgent"]["status"] == "completed"
    assert data["anomalyAgent"]["status"] == "completed"
    assert data["forecastingAgent"]["status"] == "completed"
    assert data["forecastingAgent"]["metrics"]["isEligible"] is True
    assert data["dashboardAgent"]["status"] == "completed"
    assert len(data["recommendations"]) >= 1
    assert data["cleaningPreview"] is not None
    assert data["cleaningPreview"]["approvalRequired"] is True


def test_full_workflow_ineligible_routing(client: TestClient, sample_no_date_dataset: DatasetModel):
    """Test LangGraph conditional routing for ineligible time series dataset."""
    res = client.post(f"/api/datasets/{sample_no_date_dataset.id}/workflow/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["forecastingAgent"]["metrics"]["isEligible"] is False


def test_cleaning_preview_and_apply_flow(client: TestClient, db_session: Session, sample_retail_dataset: DatasetModel):
    """
    Test safe cleaning lifecycle:
    1. Generate preview without changing raw data.
    2. User submits approval to promote a cleaned dataset.
    3. New dataset is created, while original dataset is preserved.
    """
    # Step 1: Preview
    prev_res = client.get(f"/api/datasets/{sample_retail_dataset.id}/clean/preview")
    assert prev_res.status_code == 200
    preview_data = prev_res.json()
    assert preview_data["duplicatesRemoved"] == 2
    assert preview_data["totalOriginalRows"] == 102
    assert preview_data["totalCleanedRows"] == 100

    # Step 2: Apply user-approved cleaning
    apply_res = client.post(
        f"/api/datasets/{sample_retail_dataset.id}/clean/apply",
        json={"approvedRuleIds": ["deduplicate_records", "trim_whitespace"], "newDatasetName": "Cleaned Retail"},
    )
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["status"] == "success"
    assert apply_data["rowsRetained"] == 100
    assert apply_data["rowsRemoved"] == 2

    # Step 3: Verify original dataset is untouched in DB
    orig_in_db = db_session.query(DatasetModel).filter(DatasetModel.id == sample_retail_dataset.id).first()
    assert orig_in_db.row_count == 102

    # Step 4: Verify new cleaned dataset exists in DB
    cleaned_id = apply_data["cleanedDatasetId"]
    cleaned_in_db = db_session.query(DatasetModel).filter(DatasetModel.id == cleaned_id).first()
    assert cleaned_in_db is not None
    assert cleaned_in_db.row_count == 100
    assert cleaned_in_db.name == "Cleaned Retail"

    # Clean up file
    if os.path.exists(cleaned_in_db.file_path):
        try:
            os.remove(cleaned_in_db.file_path)
        except OSError:
            pass


def test_unknown_agent_returns_400(client: TestClient, sample_retail_dataset: DatasetModel):
    """Test invalid agent request returns 400 Bad Request."""
    res = client.post(f"/api/datasets/{sample_retail_dataset.id}/agents/invalid_agent_xyz/run")
    assert res.status_code == 400
    assert "Unknown agent" in res.json()["detail"]


def test_nonexistent_dataset_workflow_returns_404(client: TestClient):
    """Test 404 on nonexistent dataset ID."""
    res = client.post("/api/datasets/ds_nonexistent_999/workflow/run")
    assert res.status_code == 404
