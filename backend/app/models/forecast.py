from datetime import datetime, date
from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Boolean, JSON, UniqueConstraint
from app.db.session import Base


class DailyMetricModel(Base):
    """
    Historical daily business metrics (e.g. daily revenue, order volume).
    Serves as the empirical ground truth for time-series forecasting.
    """
    __tablename__ = "daily_metrics"

    id = Column(String(64), primary_key=True)
    record_date = Column(Date, nullable=False, index=True)
    metric_name = Column(String(64), nullable=False, index=True)  # e.g. "revenue", "orders"
    value = Column(Float, nullable=False)
    is_actual = Column(Boolean, nullable=False, default=True)  # True = observed real, False = imputed/sample
    data_provenance = Column(String(32), default="synthetic_seed", nullable=False)  # "synthetic_seed" | "empirical_recorded"
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("record_date", "metric_name", name="uq_record_date_metric"),
    )


class ForecastRunModel(Base):
    """
    Persistent log of generated time-series forecast runs,
    tracking out-of-sample error metrics, projections, and evaluation over time.
    """
    __tablename__ = "forecast_runs"

    id = Column(String(64), primary_key=True)  # e.g. "fc_9b3e1..."
    metric_name = Column(String(64), nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)
    model_name = Column(String(64), nullable=False)
    train_size = Column(Integer, nullable=False)
    test_size = Column(Integer, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    trend_direction = Column(String(16), nullable=False)  # "up" | "down" | "flat"
    growth_rate = Column(Float, nullable=False)  # Percentage growth over horizon
    historical_points = Column(JSON, nullable=False)  # list of {date: str, value: float}
    forecast_points = Column(JSON, nullable=False)    # list of {date: str, forecast: float, lower: float, upper: float}
    model_metrics = Column(JSON, nullable=True)       # comparison table of candidate models
    recommendations = Column(JSON, nullable=True)     # list of string recommendations
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
