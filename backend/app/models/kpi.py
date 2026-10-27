from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, JSON
from app.db.session import Base


class KpiMetricModel(Base):
    __tablename__ = "kpi_metrics"

    # Composite primary identifier
    id = Column(String(64), primary_key=True)
    range_type = Column(String(16), primary_key=True, index=True, default="30d")
    label = Column(String(128), nullable=False)
    value = Column(String(64), nullable=False)
    change_percent = Column(Float, nullable=False, default=0.0)
    trend = Column(String(16), nullable=False, default="neutral")  # "up" | "down" | "neutral"
    period_label = Column(String(128), nullable=False)
    icon_name = Column(String(64), nullable=False, default="TrendingUp")
    ai_insight = Column(Text, nullable=True)
    sparkline_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
