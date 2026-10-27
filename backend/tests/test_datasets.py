import io
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import DatasetModel
from app.models.report import ReportModel
from app.models.agent import AgentModel


SAMPLE_CSV_CONTENT = """InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country
536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,2026-10-01 08:26:00,2.55,17850,United Kingdom
536365,71053,WHITE METAL LANTERN,6,2026-10-01 08:26:00,3.39,17850,United Kingdom
536366,22633,HAND WARMER UNION JACK,32,2026-10-02 09:12:00,1.85,17850,United Kingdom
C536379,D,Discount,-1,2026-10-03 09:41:00,27.50,14527,United Kingdom
536381,22792,FRONT  DOOR NUMBER 7,10,2026-10-04 10:15:00,1.25,15311,Germany
536382,22803,IVORY EMBROIDERED QUILT,2,2026-10-05 11:20:00,35.75,16098,France
"""

SECONDARY_CSV_CONTENT = """ProductID,Category,Sales,Date
PROD_A,Electronics,120.50,2026-10-10
PROD_B,Appliances,85.00,2026-10-11
"""


def test_upload_and_inspect_dataset(client: TestClient):
    file_bytes = io.BytesIO(SAMPLE_CSV_CONTENT.encode("utf-8"))
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("online_retail_test.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "online_retail_test.csv"
    assert data["rowCount"] == 6
    assert data["columnCount"] == 8
    assert data["detectedMappings"]["isOnlineRetail"] is True
    assert data["detectedMappings"]["dateColumn"] == "InvoiceDate"
    assert data["detectedMappings"]["amountColumn"] == "UnitPrice"
    assert data["detectedMappings"]["quantityColumn"] == "Quantity"
    assert data["qualityReport"]["qualityScore"] > 0
    assert len(data["columnsSchema"]) == 8

    dataset_id = data["id"]

    # 1. Test get all datasets
    get_res = client.get("/api/datasets")
    assert get_res.status_code == 200
    datasets = get_res.json()
    assert any(d["id"] == dataset_id for d in datasets)

    # 2. Test get active dataset
    active_res = client.get("/api/datasets/active")
    assert active_res.status_code == 200
    assert active_res.json()["id"] == dataset_id

    # 3. Test dataset preview
    prev_res = client.get(f"/api/datasets/{dataset_id}/preview?page=1&page_size=5")
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["totalRows"] == 6
    assert len(prev_data["rows"]) == 5

    # 4. Test dataset dashboard aggregation
    dash_res = client.get(f"/api/datasets/{dataset_id}/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["datasetId"] == dataset_id
    assert len(dash_data["kpis"]) >= 3
    canc_kpi = next((k for k in dash_data["kpis"] if k["id"] == "cancellations"), None)
    if canc_kpi:
        assert canc_kpi["rawValue"] == 1.0

    # 5. Test Business Analyst Agent
    ba_res = client.post(f"/api/datasets/{dataset_id}/agents/business_analyst/run", json={})
    assert ba_res.status_code == 200
    ba_data = ba_res.json()
    assert ba_data["agentId"] == "agent-analyst"
    assert len(ba_data["findings"]) > 0
    assert len(ba_data["citations"]) > 0

    # 6. Test Quality Analyst Agent
    qa_res = client.post(f"/api/datasets/{dataset_id}/agents/quality_analyst/run", json={})
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["agentId"] == "agent-quality"
    assert "qualityScore" in qa_data["metrics"]

    # 7. Test Forecasting Analyst Agent
    fa_res = client.post(f"/api/datasets/{dataset_id}/agents/forecast_analyst/run", json={})
    assert fa_res.status_code == 200
    fa_data = fa_res.json()
    assert fa_data["agentId"] == "agent-forecaster"
    assert any("insufficient" in f.lower() or "minimum" in f.lower() for f in fa_data["findings"])

    # 8. Test Coordinated Multi-Agent Swarm
    swarm_res = client.post(f"/api/datasets/{dataset_id}/agents/run-all", json={"query": "Evaluate UK performance"})
    assert swarm_res.status_code == 200
    swarm_data = swarm_res.json()
    assert "businessAnalyst" in swarm_data
    assert "qualityAnalyst" in swarm_data
    assert "forecastAnalyst" in swarm_data
    assert len(swarm_data["combinedExecutiveSummary"]) > 20

    # 9. Test Delete Dataset
    del_res = client.delete(f"/api/datasets/{dataset_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
    assert del_res.json()["datasetId"] == dataset_id


def test_delete_nonexistent_dataset_id(client: TestClient):
    """Deleting a non-existent dataset ID returns HTTP 404 Not Found."""
    res = client.delete("/api/datasets/ds_nonexistent_99999")
    assert res.status_code == 404
    assert "not found" in res.json().get("detail", "").lower()


def test_unauthorized_deletion_blocked(client: TestClient):
    """When API Key Auth is enforced, requests without key return HTTP 401 Unauthorized."""
    test_key = "secure-production-api-key-test"
    with patch.object(settings, "ENABLE_API_KEY_AUTH", True), \
         patch.object(settings, "API_AUTH_KEY", test_key):

        # 1. Delete without auth header -> 401
        res = client.delete("/api/datasets/ds_test_unauth")
        assert res.status_code == 401
        assert "Missing required API key" in res.json().get("detail", "")

        # 2. Delete with wrong auth header -> 401
        res_bad = client.delete("/api/datasets/ds_test_unauth", headers={"X-API-Key": "wrong-key"})
        assert res_bad.status_code == 401
        assert "Invalid API key" in res_bad.json().get("detail", "")


def test_related_records_cleanup_on_deletion(client: TestClient, db_session: Session):
    """
    Verifies that deleting a dataset purges its related reports,
    resets associated agent tasks to Standby, and deletes physical files on disk.
    """
    # 1. Upload a dataset
    file_bytes = io.BytesIO(SAMPLE_CSV_CONTENT.encode("utf-8"))
    res = client.post(
        "/api/datasets/upload",
        files={"file": ("dataset_for_cleanup.csv", file_bytes, "text/csv")},
    )
    assert res.status_code == 201
    ds_data = res.json()
    ds_id = ds_data["id"]

    # Verify file exists on disk
    ds_record = db_session.query(DatasetModel).filter(DatasetModel.id == ds_id).first()
    assert ds_record is not None
    assert os.path.exists(ds_record.file_path)

    # 2. Insert a dataset-specific report
    report = ReportModel(
        id=f"rep_{ds_id}",
        title=f"Executive Audit for {ds_record.name}",
        category="Executive",
        agent="Business Analyst",
        status="ready",
        summary=f"Synthesized report for {ds_record.name}",
        key_metrics=[{"label": "Revenue", "value": "$1,000"}],
        data_provenance=f"real_dataset:{ds_record.filename}",
    )
    db_session.add(report)

    # 3. Associate an agent task with this dataset
    agent = db_session.query(AgentModel).first()
    if agent:
        agent.current_task = f"Analyzing records for {ds_record.name}"
        agent.status = "completed"
    db_session.commit()

    # 4. Perform DELETE
    del_res = client.delete(f"/api/datasets/{ds_id}")
    assert del_res.status_code == 200

    # 5. Verify dataset record is gone
    assert db_session.query(DatasetModel).filter(DatasetModel.id == ds_id).first() is None

    # 6. Verify dataset file on disk is removed
    assert not os.path.exists(ds_record.file_path)

    # 7. Verify related report is deleted
    assert db_session.query(ReportModel).filter(ReportModel.id == f"rep_{ds_id}").first() is None

    # 8. Verify agent task was reset to Standby
    if agent:
        db_session.refresh(agent)
        assert agent.current_task == "Standby"
        assert agent.status == "idle"


def test_deletion_of_active_dataset_promotes_next(client: TestClient, db_session: Session):
    """
    When deleting the active dataset, the backend automatically selects and promotes
    another remaining dataset to active. When the last dataset is deleted, no dataset remains active.
    """
    # 1. Upload first dataset
    res1 = client.post(
        "/api/datasets/upload",
        files={"file": ("first_dataset.csv", io.BytesIO(SECONDARY_CSV_CONTENT.encode("utf-8")), "text/csv")},
    )
    assert res1.status_code == 201
    id1 = res1.json()["id"]

    # 2. Upload second dataset (becomes active)
    res2 = client.post(
        "/api/datasets/upload",
        files={"file": ("second_dataset.csv", io.BytesIO(SAMPLE_CSV_CONTENT.encode("utf-8")), "text/csv")},
    )
    assert res2.status_code == 201
    id2 = res2.json()["id"]

    # Verify id2 is active
    active = client.get("/api/datasets/active").json()
    assert active["id"] == id2

    # 3. Delete active dataset (id2)
    del_res = client.delete(f"/api/datasets/{id2}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["wasActive"] is True
    assert del_data["nextActiveDatasetId"] == id1

    # 4. Verify id1 is now active
    active_after = client.get("/api/datasets/active").json()
    assert active_after["id"] == id1

    # 5. Delete remaining dataset (id1)
    del_res2 = client.delete(f"/api/datasets/{id1}")
    assert del_res2.status_code == 200
    assert del_res2.json()["nextActiveDatasetId"] is None

    # 6. Verify no dataset is active (404)
    active_final = client.get("/api/datasets/active")
    assert active_final.status_code == 404
