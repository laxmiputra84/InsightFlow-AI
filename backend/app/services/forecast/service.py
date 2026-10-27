import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.forecast import DailyMetricModel, ForecastRunModel
from app.schemas.forecast import (
    ForecastAvailabilityResponse,
    ForecastGenerateRequest,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastHistoryItem,
    ForecastEvaluateResponse,
    HistoricalPoint,
    ForecastPoint,
    ModelEvaluationMetric,
)
from .metrics import ForecastMetrics
from .models import (
    BaseForecaster,
    NaiveForecaster,
    MovingAverageForecaster,
    LinearTrendForecaster,
    HoltLinearForecaster,
)

MIN_REQUIRED_OBSERVATIONS = 14


class ForecastingService:
    """
    Modular, empirical forecasting service.
    Aggregates historical time-series, tests candidate models chronologically,
    selects the top out-of-sample performer, and produces prediction intervals
    with grounded business recommendations.
    """

    @classmethod
    def check_availability(
        cls,
        db: Session,
        metric_name: str = "revenue",
    ) -> ForecastAvailabilityResponse:
        """
        Validates whether sufficient historical observations exist in the database.
        """
        metric_clean = metric_name.strip().lower()
        records_query = (
            db.query(DailyMetricModel)
            .filter(DailyMetricModel.metric_name == metric_clean)
            .order_by(DailyMetricModel.record_date.asc())
        )
        count = records_query.count()

        if count < MIN_REQUIRED_OBSERVATIONS:
            return ForecastAvailabilityResponse(
                has_sufficient_data=False,
                message=(
                    f"Insufficient historical data for '{metric_clean}'. "
                    f"Found {count} observation(s); a minimum of {MIN_REQUIRED_OBSERVATIONS} "
                    f"daily observations is required for empirical time-series forecasting."
                ),
                total_observations=count,
                min_date=None,
                max_date=None,
                supported_metrics=["revenue", "orders"],
                required_observations=MIN_REQUIRED_OBSERVATIONS,
            )

        earliest = records_query.first().record_date.isoformat()
        latest = records_query.order_by(DailyMetricModel.record_date.desc()).first().record_date.isoformat()

        has_synthetic = (
            records_query.filter(
                (DailyMetricModel.data_provenance == "synthetic_seed") |
                (DailyMetricModel.data_provenance == None)
            ).first() is not None
        )
        prov = "synthetic_seed" if has_synthetic else "empirical_recorded"
        prov_label = "Synthetic Baseline (Demo Seed)" if has_synthetic else "Empirical Recorded Production Data"

        return ForecastAvailabilityResponse(
            has_sufficient_data=True,
            message=(
                f"Sufficient historical data available for '{metric_clean}': "
                f"{count} daily observations from {earliest} to {latest} ({prov_label})."
            ),
            total_observations=count,
            min_date=earliest,
            max_date=latest,
            supported_metrics=["revenue", "orders"],
            required_observations=MIN_REQUIRED_OBSERVATIONS,
            data_provenance=prov,
            provenance_label=prov_label,
        )

    @classmethod
    def prepare_clean_series(
        cls,
        db: Session,
        metric_name: str,
    ) -> List[Tuple[date, float, bool, str]]:
        """
        Retrieves, deduplicates, and gap-fills historical records into an unbroken daily time-series.
        Returns a list of (date, value, is_actual, data_provenance).
        """
        metric_clean = metric_name.strip().lower()
        records = (
            db.query(DailyMetricModel)
            .filter(DailyMetricModel.metric_name == metric_clean)
            .order_by(DailyMetricModel.record_date.asc())
            .all()
        )

        if len(records) < MIN_REQUIRED_OBSERVATIONS:
            raise ValueError(
                f"Insufficient historical observations for '{metric_clean}'. "
                f"Required at least {MIN_REQUIRED_OBSERVATIONS}, but found {len(records)}."
            )

        # 1. Deduplicate by date (keep last observed if duplicate)
        date_map: Dict[date, Tuple[float, bool, str]] = {}
        for r in records:
            prov = getattr(r, "data_provenance", None) or "synthetic_seed"
            date_map[r.record_date] = (float(r.value), bool(r.is_actual), str(prov))

        sorted_dates = sorted(date_map.keys())
        min_d = sorted_dates[0]
        max_d = sorted_dates[-1]

        # 2. Continuous calendar gap-filling
        clean_series: List[Tuple[date, float, bool, str]] = []
        curr_d = min_d
        last_val = date_map[min_d][0]
        last_prov = date_map[min_d][2]

        while curr_d <= max_d:
            if curr_d in date_map:
                val, is_act, prov = date_map[curr_d]
                last_val = val
                last_prov = prov
                clean_series.append((curr_d, val, is_act, prov))
            else:
                # Interpolate or forward-fill missing calendar date safely
                clean_series.append((curr_d, round(last_val, 2), False, last_prov))
            curr_d += timedelta(days=1)

        return clean_series

    @classmethod
    def generate_forecast(
        cls,
        db: Session,
        request: ForecastGenerateRequest,
    ) -> ForecastGenerateResponse:
        """
        Executes the full forecasting pipeline:
        1. Data prep and chronological train/test holdout split.
        2. Candidate model evaluation on holdout test set (no data leakage).
        3. Model selection based on minimum test RMSE.
        4. Horizon forecasting with prediction intervals.
        5. Trend decomposition and grounded business recommendations.
        6. Persistence to database.
        """
        metric_clean = request.metric_name.strip().lower()
        if metric_clean not in ["revenue", "orders"]:
            raise ValueError(f"Unsupported metric '{metric_clean}'. Supported metrics: 'revenue', 'orders'.")

        clean_series = cls.prepare_clean_series(db, metric_clean)
        n_total = len(clean_series)

        # Determine holdout test size (bounded between 3 and min(14, 25% of data))
        test_size = request.test_size or 7
        test_size = max(3, min(test_size, int(n_total * 0.25)))
        train_size = n_total - test_size

        values_full = [pt[1] for pt in clean_series]
        train_vals = values_full[:train_size]
        test_vals = values_full[train_size:]

        # 2. Initialize candidate models
        candidates: List[BaseForecaster] = [
            NaiveForecaster(),
            MovingAverageForecaster(window_size=7),
            LinearTrendForecaster(),
            HoltLinearForecaster(alpha=0.35, beta=0.15),
        ]

        candidate_results: List[Dict[str, Any]] = []
        best_model: Optional[BaseForecaster] = None
        lowest_rmse = float("inf")

        for model in candidates:
            try:
                # Train model ONLY on chronological training split
                model.fit(train_vals)
                # Predict holdout evaluation test set
                holdout_preds = model.predict(test_size)

                mae = ForecastMetrics.mae(test_vals, holdout_preds)
                rmse = ForecastMetrics.rmse(test_vals, holdout_preds)
                mape = ForecastMetrics.mape(test_vals, holdout_preds)

                candidate_results.append({
                    "model": model,
                    "name": model.name,
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                })

                if rmse < lowest_rmse:
                    lowest_rmse = rmse
                    best_model = model
            except Exception:
                continue

        if not best_model:
            best_model = NaiveForecaster().fit(values_full)

        # 3. Refit the selected best model on the complete historical series
        best_model.fit(values_full)
        point_forecasts = best_model.predict(request.horizon_days)
        intervals = best_model.get_prediction_intervals(
            point_forecasts,
            confidence=request.confidence_level,
        )

        # 4. Generate future dates for horizon
        last_date = clean_series[-1][0]
        forecast_points: List[ForecastPoint] = []
        for h, (fc, (lower, upper)) in enumerate(zip(point_forecasts, intervals), start=1):
            fc_date = last_date + timedelta(days=h)
            forecast_points.append(
                ForecastPoint(
                    date=fc_date.isoformat(),
                    forecast=fc,
                    lower_bound=lower,
                    upper_bound=upper,
                )
            )

        # 5. Trend Analysis & Projected Growth Rate
        # Compare average forecasted value vs average of last historical window of same size
        recent_hist_vals = values_full[-request.horizon_days :]
        recent_hist_avg = sum(recent_hist_vals) / len(recent_hist_vals) if recent_hist_vals else 1.0
        forecast_avg = sum(point_forecasts) / len(point_forecasts) if point_forecasts else 1.0

        growth_rate = round(((forecast_avg - recent_hist_avg) / max(recent_hist_avg, 1.0)) * 100.0, 2)
        if growth_rate > 1.5:
            trend_direction = "up"
        elif growth_rate < -1.5:
            trend_direction = "down"
        else:
            trend_direction = "flat"

        # 6. Formulate Grounded Executive Recommendations
        recommendations = cls._generate_recommendations(
            metric_name=metric_clean,
            trend_direction=trend_direction,
            growth_rate=growth_rate,
            horizon_days=request.horizon_days,
            selected_model=best_model.name,
            forecast_avg=forecast_avg,
        )

        # Candidate evaluations schema
        candidate_evaluations = [
            ModelEvaluationMetric(
                model_name=r["name"],
                mae=r["mae"],
                rmse=r["rmse"],
                mape=r["mape"],
                selected=(r["name"] == best_model.name),
            )
            for r in candidate_results
        ]

        winning_result = next(r for r in candidate_results if r["name"] == best_model.name)
        out_of_sample_metrics = {
            "mae": winning_result["mae"],
            "rmse": winning_result["rmse"],
            "mape": winning_result["mape"],
        }

        # 7. Persist Run to Database
        run_id = f"fc_{uuid.uuid4().hex[:12]}"
        has_synthetic = any(pt[3] == "synthetic_seed" for pt in clean_series)
        prov = "synthetic_seed" if has_synthetic else "empirical_recorded"
        prov_label = "Synthetic Baseline (Demo Seed)" if has_synthetic else "Empirical Recorded Production Data"

        hist_points_schema = [
            HistoricalPoint(date=pt[0].isoformat(), value=pt[1], is_actual=pt[2], data_provenance=pt[3])
            for pt in clean_series[-45:]  # Store last 45 historical points for visualization
        ]

        run_record = ForecastRunModel(
            id=run_id,
            metric_name=metric_clean,
            horizon_days=request.horizon_days,
            model_name=best_model.name,
            train_size=train_size,
            test_size=test_size,
            mae=winning_result["mae"],
            rmse=winning_result["rmse"],
            mape=winning_result["mape"],
            trend_direction=trend_direction,
            growth_rate=growth_rate,
            historical_points=[p.model_dump() for p in hist_points_schema],
            forecast_points=[p.model_dump() for p in forecast_points],
            model_metrics=[m.model_dump() for m in candidate_evaluations],
            recommendations=recommendations,
            created_at=datetime.utcnow(),
        )
        db.add(run_record)
        db.commit()

        return ForecastGenerateResponse(
            run_id=run_id,
            metric_name=metric_clean,
            horizon_days=request.horizon_days,
            selected_model=best_model.name,
            out_of_sample_metrics=out_of_sample_metrics,
            candidate_evaluations=candidate_evaluations,
            trend_direction=trend_direction,
            projected_growth_rate=growth_rate,
            historical_points=hist_points_schema,
            forecast_points=forecast_points,
            recommendations=recommendations,
            created_at=run_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            data_provenance=prov,
            provenance_label=prov_label,
        )

    @classmethod
    def get_history(cls, db: Session, limit: int = 20) -> ForecastHistoryResponse:
        """
        Retrieves recent forecast runs ordered by creation timestamp descending.
        """
        runs = (
            db.query(ForecastRunModel)
            .order_by(ForecastRunModel.created_at.desc())
            .limit(limit)
            .all()
        )
        items = [
            ForecastHistoryItem(
                id=r.id,
                metric_name=r.metric_name,
                horizon_days=r.horizon_days,
                model_name=r.model_name,
                mae=r.mae,
                rmse=r.rmse,
                mape=r.mape,
                trend_direction=r.trend_direction,
                growth_rate=r.growth_rate,
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
            for r in runs
        ]
        return ForecastHistoryResponse(runs=items, total_count=len(items))

    @classmethod
    def evaluate_past_run(cls, db: Session, run_id: str) -> ForecastEvaluateResponse:
        """
        Compares past forecast run projections with subsequently observed actual records
        in the database, determining realized forecast error.
        """
        run = db.query(ForecastRunModel).filter(ForecastRunModel.id == run_id).first()
        if not run:
            raise ValueError(f"Forecast run with ID '{run_id}' not found.")

        forecast_points = run.forecast_points or []
        if not forecast_points:
            raise ValueError(f"No forecast points stored for run '{run_id}'.")

        # Extract dates and predicted values
        forecast_dates = [p["date"] for p in forecast_points]
        min_fc_date = min(forecast_dates)
        max_fc_date = max(forecast_dates)

        # Query actual values for those dates
        actual_records = (
            db.query(DailyMetricModel)
            .filter(
                DailyMetricModel.metric_name == run.metric_name,
                DailyMetricModel.record_date >= date.fromisoformat(min_fc_date),
                DailyMetricModel.record_date <= date.fromisoformat(max_fc_date),
                DailyMetricModel.is_actual == True,
            )
            .all()
        )

        actual_map = {r.record_date.isoformat(): float(r.value) for r in actual_records}

        comparison_pairs = []
        actual_list = []
        pred_list = []

        for fp in forecast_points:
            d_str = fp["date"]
            if d_str in actual_map:
                actual_val = actual_map[d_str]
                pred_val = fp["forecast"]
                actual_list.append(actual_val)
                pred_list.append(pred_val)
                comparison_pairs.append({
                    "date": d_str,
                    "actual": actual_val,
                    "predicted": pred_val,
                    "error": round(actual_val - pred_val, 2),
                    "lower_bound": fp.get("lower_bound"),
                    "upper_bound": fp.get("upper_bound"),
                })

        if not comparison_pairs:
            return ForecastEvaluateResponse(
                run_id=run_id,
                metric_name=run.metric_name,
                evaluated_points_count=0,
                actual_vs_predicted=[],
                realized_mae=0.0,
                realized_rmse=0.0,
                realized_mape=0.0,
                accuracy_status="Pending: No subsequent actual records have been logged for the forecasted dates yet.",
            )

        realized_mae = ForecastMetrics.mae(actual_list, pred_list)
        realized_rmse = ForecastMetrics.rmse(actual_list, pred_list)
        realized_mape = ForecastMetrics.mape(actual_list, pred_list)

        if realized_mape < 8.0:
            status = "Excellent Calibration: realized MAPE is within 8%."
        elif realized_mape < 15.0:
            status = "Moderate Calibration: realized MAPE is between 8% and 15%."
        else:
            status = "High Variance: realized deviation exceeded 15% due to external volatility."

        return ForecastEvaluateResponse(
            run_id=run_id,
            metric_name=run.metric_name,
            evaluated_points_count=len(comparison_pairs),
            actual_vs_predicted=comparison_pairs,
            realized_mae=realized_mae,
            realized_rmse=realized_rmse,
            realized_mape=realized_mape,
            accuracy_status=status,
        )

    @classmethod
    def _generate_recommendations(
        cls,
        metric_name: str,
        trend_direction: str,
        growth_rate: float,
        horizon_days: int,
        selected_model: str,
        forecast_avg: float,
    ) -> List[str]:
        """
        Synthesizes practical, grounded business recommendations based on
        empirical forecast trajectory without hallucinated business facts.
        """
        recs = []
        metric_display = "Revenue" if metric_name == "revenue" else "Order Volume"
        formatted_avg = f"${int(forecast_avg):,}" if metric_name == "revenue" else f"{int(forecast_avg):,} units"

        if trend_direction == "up":
            recs.append(
                f"Sustained Upward Momentum: Projected {metric_display} trajectory is expanding at +{growth_rate}% "
                f"over the next {horizon_days} days (averaging {formatted_avg}/day via {selected_model})."
            )
            if metric_name == "revenue":
                recs.append("Infrastructure Capacity: Scale API gateway compute quotas and cloud database replicas ahead of projected peak load.")
                recs.append("Capital Allocation: Reinvest expanding gross margin into high-converting customer acquisition channels.")
            else:
                recs.append("Fulfillment Optimization: Expand logistics fulfillment slots to prevent delivery queue bottlenecks.")
                recs.append("Support Staffing: Provision Tier-1 support desk shifts to maintain <15 minute first-response time.")

        elif trend_direction == "down":
            recs.append(
                f"Headwind Warning: Projected {metric_display} indicates a {growth_rate}% contraction "
                f"over the next {horizon_days} days (averaging {formatted_avg}/day via {selected_model})."
            )
            if metric_name == "revenue":
                recs.append("Churn Mitigation: Trigger automated retention workflows for mid-tier accounts approaching renewal cycles.")
                recs.append("Promotional Campaign: Evaluate targeted discount incentives to stimulate off-peak purchasing.")
            else:
                recs.append("Cart Recovery: Review checkout drop-off rates and deploy cart abandonment email sequences.")
                recs.append("Latency Audit: Inspect regional payment gateways to ensure technical errors are not suppressing conversions.")

        else:
            recs.append(
                f"Stable Baseline: Projected {metric_display} remains steady (growth rate {growth_rate}%) "
                f"averaging {formatted_avg}/day across the {horizon_days}-day horizon."
            )
            recs.append("Efficiency Focus: Maintain operational baseline and conduct A/B price elasticity experiments to unlock margin.")
            recs.append("Forecasting Cadence: Refresh 14-day rolling forecast weekly to catch demand inflection points early.")

        return recs
