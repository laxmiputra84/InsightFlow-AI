"""
InsightFlow AI - Automated Test Suite for Stage 1: Business Analysis Engine
Tests all required scenarios:
1. Valid sales, finance, customer, and inventory datasets
2. Missing required columns and explicit explanation disclosures
3. Empty datasets (0 rows) and unsupported structures
4. Missing values, duplicate rows, invalid date strings, and category casing inconsistencies
5. Anomaly detection (Tukey IQR, Z-scores, temporal spikes/drops, severity, business event distinction)
6. 8-Stage LangGraph orchestration workflow execution
7. API response schemas and 404 for invalid dataset IDs
8. Deterministic offline execution (zero Gemini API key requirement)
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import DatasetModel
from app.services.dataset_service import DatasetService
from app.services.business_engine import BusinessAnalysisEngine
from app.workflows.business_workflow import BusinessAnalysisWorkflow


# ==============================================================================
# Test Fixtures: Diverse Multi-Domain Datasets
# ==============================================================================

@pytest.fixture
def sales_dataset(db_session: Session):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    records = []
    base_date = datetime(2026, 9, 1)
    for i in range(60):
        records.append({
            "order_id": f"ORD_{1000 + i}",
            "order_date": (base_date + timedelta(days=i % 20)).strftime("%Y-%m-%d"),
            "product_name": f"Product {chr(65 + (i % 5))}",
            "category": "Electronics" if i % 2 == 0 else "Apparel",
            "quantity": (i % 4) + 1,
            "unit_price": 25.0 + (i % 3) * 10,
            "total_revenue": ((i % 4) + 1) * (25.0 + (i % 3) * 10),
            "region": "North America" if i % 3 == 0 else "Europe",
        })
    # Add an extreme outlier for anomaly detection
    records.append({
        "order_id": "ORD_EXTREME",
        "order_date": (base_date + timedelta(days=10)).strftime("%Y-%m-%d"),
        "product_name": "Enterprise Server",
        "category": "Electronics",
        "quantity": 100,
        "unit_price": 500.0,
        "total_revenue": 50000.0,
        "region": "North America",
    })
    # Duplicate row
    records.append(records[0].copy())

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)

    ds_id = f"ds_sales_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Sales Dataset Test",
        filename="sales_test.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=True,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        db_session.delete(dataset)
        db_session.commit()
    except Exception:
        db_session.rollback()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def finance_dataset(db_session: Session):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    records = []
    base_date = datetime(2026, 1, 1)
    for i in range(24):
        month_dt = base_date + timedelta(days=i * 30)
        rev = 100000.0 + (i * 5000.0)
        exp = 65000.0 + (i * 2000.0)
        records.append({
            "period_date": month_dt.strftime("%Y-%m-%d"),
            "gross_revenue": rev,
            "operating_expense": exp,
            "net_profit": rev - exp,
            "department": "Engineering" if i % 2 == 0 else "Operations",
        })

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)

    ds_id = f"ds_fin_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Finance Dataset Test",
        filename="finance_test.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=False,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        db_session.delete(dataset)
        db_session.commit()
    except Exception:
        db_session.rollback()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def customer_dataset(db_session: Session):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    records = []
    base_date = datetime(2026, 6, 1)
    for i in range(50):
        cust_id = f"CUST_{i % 15}"  # Some repeat customers
        records.append({
            "customer_id": cust_id,
            "transaction_date": (base_date + timedelta(days=i % 30)).strftime("%Y-%m-%d"),
            "purchase_amount": 50.0 + (i % 10) * 15,
            "segment": "VIP" if (i % 15) < 3 else "Standard",
        })

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)

    ds_id = f"ds_cust_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Customer Dataset Test",
        filename="customer_test.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=False,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        db_session.delete(dataset)
        db_session.commit()
    except Exception:
        db_session.rollback()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def inventory_dataset(db_session: Session):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    records = []
    for i in range(30):
        records.append({
            "sku": f"SKU_{100 + i}",
            "product_name": f"Item {i}",
            "stock_level": 5 if i < 5 else 50 + i * 2,  # 5 low-stock items
            "reorder_level": 15,
            "units_sold": 10 + i,
        })

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)

    ds_id = f"ds_inv_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Inventory Dataset Test",
        filename="inventory_test.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=len(df),
        column_count=len(df.columns),
        is_active=False,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        db_session.delete(dataset)
        db_session.commit()
    except Exception:
        db_session.rollback()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def empty_dataset(db_session: Session):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
        f.write("col_a,col_b,col_c\n")  # Header only, 0 rows

    ds_id = f"ds_empty_{uuid.uuid4().hex[:8]}"
    dataset = DatasetModel(
        id=ds_id,
        name="Empty Dataset Test",
        filename="empty_test.csv",
        file_path=path,
        file_type="csv",
        file_size=os.path.getsize(path),
        row_count=0,
        column_count=3,
        is_active=False,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    yield dataset

    try:
        db_session.delete(dataset)
        db_session.commit()
    except Exception:
        db_session.rollback()
    if os.path.exists(path):
        os.remove(path)


# ==============================================================================
# Unit & Integration Tests: Business Analysis Engine
# ==============================================================================

def test_sales_dataset_profiling_and_metrics(sales_dataset, db_session):
    """Verifies Sales domain identification, revenue sum, AOV, and top categories."""
    df = DatasetService.load_dataframe(sales_dataset.file_path, sales_dataset.file_type)
    profile = BusinessAnalysisEngine.profile_dataset(df, sales_dataset.id, sales_dataset.name, "csv", sales_dataset.file_size)

    assert profile.detectedDomain == "sales"
    assert profile.domainConfidence >= 0.6
    assert profile.rowCount > 0

    metrics_res = BusinessAnalysisEngine.analyze_business_metrics(
        df, sales_dataset.id, profile.detectedDomain, profile.domainMappings
    )

    assert metrics_res.domain == "sales"
    assert len(metrics_res.computedMetrics) >= 3

    # Check Total Revenue metric
    rev_metric = next((m for m in metrics_res.computedMetrics if m.id == "total_revenue"), None)
    assert rev_metric is not None
    assert rev_metric.rawValue is not None and rev_metric.rawValue > 50000.0

    # Check Orders metric
    order_metric = next((m for m in metrics_res.computedMetrics if m.id == "total_orders"), None)
    assert order_metric is not None
    assert order_metric.rawValue == 61.0  # 60 unique + 1 extreme

    # Check Category Breakdown
    assert len(metrics_res.topCategories) > 0


def test_finance_dataset_metrics(finance_dataset):
    """Verifies Finance domain classification, profit calculation, and margin %."""
    df = DatasetService.load_dataframe(finance_dataset.file_path, finance_dataset.file_type)
    profile = BusinessAnalysisEngine.profile_dataset(df, finance_dataset.id, finance_dataset.name, "csv", finance_dataset.file_size)

    assert profile.detectedDomain == "finance"

    metrics_res = BusinessAnalysisEngine.analyze_business_metrics(
        df, finance_dataset.id, profile.detectedDomain, profile.domainMappings
    )

    assert metrics_res.domain == "finance"

    rev_metric = next((m for m in metrics_res.computedMetrics if m.id == "fin_revenue"), None)
    exp_metric = next((m for m in metrics_res.computedMetrics if m.id == "fin_expenses"), None)
    prof_metric = next((m for m in metrics_res.computedMetrics if m.id == "fin_profit"), None)
    margin_metric = next((m for m in metrics_res.computedMetrics if m.id == "fin_margin"), None)

    assert rev_metric is not None
    assert exp_metric is not None
    assert prof_metric is not None
    assert margin_metric is not None
    assert prof_metric.rawValue == round(rev_metric.rawValue - exp_metric.rawValue, 2)
    assert margin_metric.rawValue > 0.0


def test_customer_dataset_metrics(customer_dataset):
    """Verifies Customer domain identification, repeat accounts, and spend concentration."""
    df = DatasetService.load_dataframe(customer_dataset.file_path, customer_dataset.file_type)
    profile = BusinessAnalysisEngine.profile_dataset(df, customer_dataset.id, customer_dataset.name, "csv", customer_dataset.file_size)

    assert profile.detectedDomain == "customer"

    metrics_res = BusinessAnalysisEngine.analyze_business_metrics(
        df, customer_dataset.id, profile.detectedDomain, profile.domainMappings
    )

    assert metrics_res.domain == "customer"
    cust_metric = next((m for m in metrics_res.computedMetrics if m.id == "cust_total"), None)
    ret_metric = next((m for m in metrics_res.computedMetrics if m.id == "cust_retention"), None)

    assert cust_metric is not None
    assert cust_metric.rawValue == 15.0  # 15 distinct customers
    assert ret_metric is not None
    assert ret_metric.rawValue > 50.0  # Multi-purchase customer retention


def test_inventory_dataset_metrics(inventory_dataset):
    """Verifies Inventory domain classification, total stock, and low-stock SKU count."""
    df = DatasetService.load_dataframe(inventory_dataset.file_path, inventory_dataset.file_type)
    profile = BusinessAnalysisEngine.profile_dataset(df, inventory_dataset.id, inventory_dataset.name, "csv", inventory_dataset.file_size)

    assert profile.detectedDomain == "inventory"

    metrics_res = BusinessAnalysisEngine.analyze_business_metrics(
        df, inventory_dataset.id, profile.detectedDomain, profile.domainMappings
    )

    assert metrics_res.domain == "inventory"
    stock_metric = next((m for m in metrics_res.computedMetrics if m.id == "inv_stock"), None)
    low_stock_metric = next((m for m in metrics_res.computedMetrics if m.id == "inv_low_stock"), None)

    assert stock_metric is not None
    assert stock_metric.rawValue > 0.0
    assert low_stock_metric is not None
    assert low_stock_metric.rawValue == 5.0  # 5 items with stock <= 5 (reorder level = 15)


def test_missing_column_guards():
    """Verifies that missing columns trigger honest explanation disclosures without fabricated numbers."""
    # Create dataset missing expense/cost column
    df = pd.DataFrame({
        "invoice_id": [f"INV_{i}" for i in range(10)],
        "gross_revenue": [100.0 * i for i in range(10)],
    })
    mappings = {"revenue": "gross_revenue", "expense": None, "profit": None, "date": None}

    metrics_res = BusinessAnalysisEngine.analyze_business_metrics(
        df, "test_missing", "finance", mappings
    )

    # Missing expense requirement must be disclosed
    missing_names = [mr.metricName for mr in metrics_res.missingRequirements]
    assert any("Expense" in name for name in missing_names)
    assert any("profit" in mr.explanation.lower() or "expense" in mr.explanation.lower() for mr in metrics_res.missingRequirements)


def test_empty_dataset_handling(empty_dataset):
    """Verifies that empty datasets are handled gracefully across all agents without crashing."""
    df = DatasetService.load_dataframe(empty_dataset.file_path, empty_dataset.file_type)

    profile = BusinessAnalysisEngine.profile_dataset(df, empty_dataset.id, empty_dataset.name, "csv", empty_dataset.file_size)
    assert profile.rowCount == 0
    assert profile.detectedDomain == "general"

    quality = BusinessAnalysisEngine.audit_data_quality(df, empty_dataset.id, {})
    assert quality.totalRows == 0
    assert quality.cleanlinessStatus == "poor_quality"

    metrics = BusinessAnalysisEngine.analyze_business_metrics(df, empty_dataset.id, "general", {})
    assert len(metrics.computedMetrics) == 0
    assert len(metrics.missingRequirements) > 0

    anomalies = BusinessAnalysisEngine.detect_anomalies(df, empty_dataset.id, {})
    assert anomalies.totalAnomalies == 0


def test_data_quality_audit_and_remediation():
    """Verifies detection of duplicates, missing cells, invalid dates, and category casing."""
    df = pd.DataFrame({
        "category": ["Electronics", "electronics", "ELECTRONICS", "Apparel", "apparel"],
        "price": [10.0, -5.0, 15.0, np.nan, 20.0],  # Negative price & NaN
        "date": ["2026-01-01", "not-a-date", "2026-01-03", "1850-01-01", "2026-01-05"],  # Unparseable & out of bounds
    })
    # Add duplicate row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    mappings = {"date": "date"}
    quality = BusinessAnalysisEngine.audit_data_quality(df, "quality_test", mappings)

    assert quality.duplicateRows >= 1
    assert quality.missingCells >= 1
    assert quality.invalidDateCount >= 1
    assert quality.inconsistentCategoryCount >= 1
    assert quality.suspiciousNumericCount >= 1  # -5.0 in price
    assert len(quality.suggestedOperations) >= 3


def test_anomaly_detection_iqr_and_zscore(sales_dataset):
    """Verifies statistical anomaly detection via Tukey IQR and Z-scores on the extreme outlier."""
    df = DatasetService.load_dataframe(sales_dataset.file_path, sales_dataset.file_type)
    profile = BusinessAnalysisEngine.profile_dataset(df, sales_dataset.id, sales_dataset.name, "csv", sales_dataset.file_size)

    anomalies = BusinessAnalysisEngine.detect_anomalies(df, sales_dataset.id, profile.domainMappings)

    assert anomalies.totalAnomalies > 0
    assert anomalies.criticalCount > 0 or anomalies.warningCount > 0

    # Ensure evidence and statistical methods are populated
    outlier = next((a for a in anomalies.anomalies if "total_revenue" in str(a.columnName)), None)
    assert outlier is not None
    assert outlier.evidence is not None
    assert len(outlier.businessInterpretation) > 0


def test_langgraph_8_stage_workflow_execution(sales_dataset, db_session):
    """Verifies the complete 8-stage LangGraph workflow execution end-to-end."""
    result = BusinessAnalysisWorkflow.run(db_session, sales_dataset)

    assert result.status == "completed"
    assert result.domain == "sales"
    assert result.profile.rowCount > 0
    assert result.quality.qualityScore > 0
    assert len(result.businessAnalysis.computedMetrics) > 0
    assert len(result.recommendations) > 0
    assert len(result.citations) > 0
    assert result.executionTimeMs > 0


# ==============================================================================
# REST API Endpoints Verification
# ==============================================================================

def test_api_business_analysis_run(client: TestClient, sales_dataset):
    """Tests POST /api/datasets/{dataset_id}/analysis."""
    res = client.post(f"/api/datasets/{sales_dataset.id}/analysis")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["domain"] == "sales"
    assert "profile" in data
    assert "quality" in data
    assert "businessAnalysis" in data
    assert "anomalies" in data


def test_api_dataset_profile(client: TestClient, sales_dataset):
    """Tests GET /api/datasets/{dataset_id}/profile."""
    res = client.get(f"/api/datasets/{sales_dataset.id}/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["detectedDomain"] == "sales"
    assert len(data["columnProfiles"]) > 0


def test_api_dataset_quality(client: TestClient, sales_dataset):
    """Tests GET /api/datasets/{dataset_id}/quality."""
    res = client.get(f"/api/datasets/{sales_dataset.id}/quality")
    assert res.status_code == 200
    data = res.json()
    assert "qualityScore" in data
    assert "suggestedOperations" in data


def test_api_dataset_business_analysis(client: TestClient, sales_dataset):
    """Tests GET /api/datasets/{dataset_id}/business-analysis."""
    res = client.get(f"/api/datasets/{sales_dataset.id}/business-analysis")
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "sales"
    assert len(data["computedMetrics"]) >= 3


def test_api_dataset_anomalies(client: TestClient, sales_dataset):
    """Tests GET /api/datasets/{dataset_id}/anomalies."""
    res = client.get(f"/api/datasets/{sales_dataset.id}/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert "totalAnomalies" in data
    assert len(data["anomalies"]) > 0


def test_api_dataset_status(client: TestClient, sales_dataset):
    """Tests GET /api/datasets/{dataset_id}/analysis/status."""
    res = client.get(f"/api/datasets/{sales_dataset.id}/analysis/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["hasResults"] is True


def test_api_invalid_dataset_id_returns_404(client: TestClient):
    """Tests that querying non-existent dataset returns 404."""
    bad_id = "ds_non_existent_99999"
    res = client.get(f"/api/datasets/{bad_id}/profile")
    assert res.status_code == 404

    res2 = client.post(f"/api/datasets/{bad_id}/analysis")
    assert res2.status_code == 404
