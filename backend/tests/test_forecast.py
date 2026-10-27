"""
Comprehensive Automated Tests for Milestone 8: Predictive Analytics and Sales Forecasting.
Verifies:
1. Data preparation, deduplication, and continuous gap filling.
2. Error handling when historical observations are insufficient (< 14 points).
3. Candidate statistical forecasting models (Naive, Moving Average, Linear Trend, Holt's Exponential Smoothing).
4. Prediction interval bounds expansion with forecast horizon.
5. Chronological holdout train/test splitting without data leakage.
6. Accuracy metrics (MAE, RMSE, MAPE with zero-value safeguards).
7. Forecast reproducibility.
8. FastAPI endpoints: /api/forecast/availability, /api/forecast/generate, /api/forecast/history, /api/forecast/evaluate.
9. LangGraph workflow forecasting query detection and dynamic recommendation synthesis.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.models.forecast import DailyMetricModel, ForecastRunModel
from app.services.forecast.metrics import ForecastMetrics
from app.services.forecast.models import (
    NaiveForecaster,
    MovingAverageForecaster,
    LinearTrendForecaster,
    HoltLinearForecaster,
)
from app.services.forecast.service import ForecastingService, MIN_REQUIRED_OBSERVATIONS
from app.schemas.forecast import ForecastGenerateRequest
from app.workflows import create_analytics_workflow
from app.workflows.state import AnalyticsWorkflowState


@pytest.fixture(autouse=True)
def mock_gemini():
    """Ensure all tests run completely offline without live Google API keys."""
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        yield


# ==============================================================================
# 1. Error Metrics & Zero-Value Safeguard Tests
# ==============================================================================

def test_metrics_calculation_standard():
    actual = [100.0, 110.0, 120.0, 130.0]
    pred = [95.0, 112.0, 118.0, 135.0]

    mae = ForecastMetrics.mae(actual, pred)
    rmse = ForecastMetrics.rmse(actual, pred)
    mape = ForecastMetrics.mape(actual, pred)

    assert mae == 3.5
    assert rmse == 3.81
    assert 2.0 < mape < 4.0


def test_metrics_zero_value_safeguard():
    """Verifies that actual values of zero do not raise ZeroDivisionError in MAPE."""
    actual = [0.0, 0.0, 50.0]
    pred = [10.0, 5.0, 50.0]

    mape = ForecastMetrics.mape(actual, pred, epsilon=1.0)
    assert isinstance(mape, float)
    assert mape > 0.0


def test_metrics_empty_series():
    assert ForecastMetrics.mae([], []) == 0.0
    assert ForecastMetrics.rmse([], []) == 0.0
    assert ForecastMetrics.mape([], []) == 0.0


# ==============================================================================
# 2. Candidate Model Tests
# ==============================================================================

def test_naive_forecaster():
    series = [40.0, 45.0, 50.0, 55.0, 60.0]
    model = NaiveForecaster().fit(series)
    preds = model.predict(3)

    assert len(preds) == 3
    assert all(p == 60.0 for p in preds)

    intervals = model.get_prediction_intervals(preds, confidence=0.95)
    assert len(intervals) == 3
    for lower, upper in intervals:
        assert lower <= 60.0 <= upper


def test_moving_average_forecaster():
    series = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    model = MovingAverageForecaster(window_size=3).fit(series)
    preds = model.predict(2)

    # Average of last 3: (50 + 60 + 70) / 3 = 60.0
    assert len(preds) == 2
    assert preds[0] == 60.0
    assert preds[1] == 60.0


def test_linear_trend_forecaster():
    # Exactly linear: y = 10 + 5*t -> t=1..5 -> [15, 20, 25, 30, 35]
    series = [15.0, 20.0, 25.0, 30.0, 35.0]
    model = LinearTrendForecaster().fit(series)
    preds = model.predict(2)

    assert preds[0] == 40.0
    assert preds[1] == 45.0


def test_holt_linear_forecaster():
    series = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
    model = HoltLinearForecaster(alpha=0.5, beta=0.2).fit(series)
    preds = model.predict(3)

    assert len(preds) == 3
    assert preds[0] > series[-1]
    assert preds[1] > preds[0]


def test_prediction_intervals_expand_with_horizon():
    series = [30.0, 32.0, 35.0, 34.0, 38.0, 42.0, 45.0, 48.0]
    model = HoltLinearForecaster().fit(series)
    preds = model.predict(10)
    intervals = model.get_prediction_intervals(preds, confidence=0.95)

    spread_early = intervals[0][1] - intervals[0][0]
    spread_late = intervals[-1][1] - intervals[-1][0]
    assert spread_late > spread_early


# ==============================================================================
# 3. Data Preparation, Gap Filling & Availability Tests
# ==============================================================================

def test_insufficient_historical_data_check(db_session):
    # Clear daily metrics table in this isolated test session
    db_session.query(DailyMetricModel).delete()
    db_session.commit()

    # Add only 3 observations (below MIN_REQUIRED_OBSERVATIONS = 14)
    for i in range(3):
        d = date(2026, 10, 1) + timedelta(days=i)
        db_session.add(DailyMetricModel(
            id=f"test_rev_{i}",
            record_date=d,
            metric_name="revenue",
            value=45000.0,
            is_actual=True,
        ))
    db_session.commit()

    availability = ForecastingService.check_availability(db_session, "revenue")
    assert availability.has_sufficient_data is False
    assert availability.total_observations == 3
    assert "minimum of 14" in availability.message

    # Generate request must raise ValueError explaining insufficiency
    with pytest.raises(ValueError) as exc_info:
        req = ForecastGenerateRequest(metric_name="revenue", horizon_days=7)
        ForecastingService.generate_forecast(db_session, req)
    assert "Insufficient historical observations" in str(exc_info.value)


def test_gap_filling_in_data_preparation(db_session):
    db_session.query(DailyMetricModel).delete()
    db_session.commit()

    # Seed 15 days with missing day on Oct 5 and Oct 10
    dates_to_add = [date(2026, 10, 1) + timedelta(days=i) for i in range(16) if i not in [4, 9]]
    for idx, d in enumerate(dates_to_add):
        db_session.add(DailyMetricModel(
            id=f"gap_rev_{idx}",
            record_date=d,
            metric_name="revenue",
            value=40000.0 + idx * 500.0,
            is_actual=True,
        ))
    db_session.commit()

    clean_series = ForecastingService.prepare_clean_series(db_session, "revenue")
    # All intermediate dates must be present
    assert len(clean_series) == 16
    imputed_points = [pt for pt in clean_series if pt[2] is False]
    assert len(imputed_points) == 2  # The 2 missing days were filled safely


# ==============================================================================
# 4. End-to-End Forecast Generation & Reproducibility Tests
# ==============================================================================

def seed_test_time_series(db_session, metric="revenue", count=30):
    db_session.query(DailyMetricModel).filter(DailyMetricModel.metric_name == metric).delete()
    start = date(2026, 9, 1)
    for i in range(count):
        d = start + timedelta(days=i)
        val = 35000.0 + i * 400.0 + (1000.0 if i % 2 == 0 else -1000.0)
        db_session.add(DailyMetricModel(
            id=f"seed_{metric}_{i}",
            record_date=d,
            metric_name=metric,
            value=val,
            is_actual=True,
        ))
    db_session.commit()


def test_generate_forecast_service(db_session):
    seed_test_time_series(db_session, metric="revenue", count=35)

    req = ForecastGenerateRequest(metric_name="revenue", horizon_days=14, confidence_level=0.95)
    resp = ForecastingService.generate_forecast(db_session, req)

    assert resp.run_id.startswith("fc_")
    assert resp.metric_name == "revenue"
    assert resp.horizon_days == 14
    assert len(resp.forecast_points) == 14
    assert resp.trend_direction == "up"
    assert resp.projected_growth_rate > 0.0
    assert len(resp.candidate_evaluations) == 4
    assert any(c.selected for c in resp.candidate_evaluations)
    assert len(resp.recommendations) >= 2


def test_forecast_reproducibility(db_session):
    seed_test_time_series(db_session, metric="orders", count=30)

    req = ForecastGenerateRequest(metric_name="orders", horizon_days=7)
    resp1 = ForecastingService.generate_forecast(db_session, req)
    resp2 = ForecastingService.generate_forecast(db_session, req)

    # Predictions must be identical for identical input data
    pts1 = [p.forecast for p in resp1.forecast_points]
    pts2 = [p.forecast for p in resp2.forecast_points]
    assert pts1 == pts2
    assert resp1.selected_model == resp2.selected_model


# ==============================================================================
# 5. FastAPI Endpoints Tests
# ==============================================================================

def test_api_forecast_availability_endpoint(client, db_session):
    seed_test_time_series(db_session, metric="revenue", count=20)

    response = client.get("/api/forecast/availability?metric=revenue")
    assert response.status_code == 200
    data = response.json()
    assert data["hasSufficientData"] is True
    assert data["totalObservations"] >= 20
    assert "revenue" in data["supportedMetrics"]


def test_api_forecast_generate_endpoint(client, db_session):
    seed_test_time_series(db_session, metric="revenue", count=30)

    payload = {
        "metricName": "revenue",
        "horizonDays": 14,
        "confidenceLevel": 0.95,
    }
    response = client.post("/api/forecast/generate", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["metricName"] == "revenue"
    assert data["horizonDays"] == 14
    assert len(data["forecastPoints"]) == 14
    assert "outOfSampleMetrics" in data
    assert "rmse" in data["outOfSampleMetrics"]
    run_id = data["runId"]

    # Test history endpoint
    hist_resp = client.get("/api/forecast/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["totalCount"] >= 1
    assert any(r["id"] == run_id for r in hist_data["runs"])

    # Test evaluate endpoint
    eval_resp = client.get(f"/api/forecast/evaluate?run_id={run_id}")
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["runId"] == run_id
    assert "accuracyStatus" in eval_data


def test_api_forecast_generate_invalid_metric(client):
    payload = {"metricName": "invalid_kpi_name", "horizonDays": 14}
    response = client.post("/api/forecast/generate", json=payload)
    assert response.status_code == 400
    assert "Unsupported metric" in response.json()["detail"]


# ==============================================================================
# 6. LangGraph Workflow Forecasting Integration Test
# ==============================================================================

def test_langgraph_workflow_with_forecasting(db_session):
    seed_test_time_series(db_session, metric="revenue", count=30)

    workflow = create_analytics_workflow()
    state: AnalyticsWorkflowState = {
        "query": "What is our forward revenue forecast for next month?",
        "range_type": "30d",
        "db_session": db_session,
        "step_count": 0,
        "max_steps": 5,
        "tools_called": [],
        "errors": [],
    }

    final_state = workflow.invoke(state)
    assert final_state["completed"] is True
    assert "time_series_forecasting" in final_state["tools_called"]
    assert final_state["has_forecast"] is True
    assert final_state["forecast_data"] is not None

    findings = final_state["final_response"]["findings"]
    assert any("Top Performer Selected" in f or "Forecast" in f for f in findings)
    assert len(final_state["recommendations"]) >= 1
