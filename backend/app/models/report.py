from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from app.db.session import Base


class ReportModel(Base):
    """
    Persisted business intelligence reports synthesized from verified MySQL metrics and forecasts.
    """
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False, default="Executive")
    agent = Column(String(64), nullable=False, default="Report Agent v2.4")
    status = Column(String(32), nullable=False, default="ready")  # "ready" | "processing" | "failed"
    summary = Column(Text, nullable=False)
    key_metrics = Column(JSON, nullable=False)  # List[{"label": "...", "value": "..."}]
    content = Column(Text, nullable=True)       # Full markdown/text content for download
    file_size = Column(String(32), default="1.2 MB")
    data_provenance = Column(String(32), default="verified_mysql")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
