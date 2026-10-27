from datetime import datetime
from sqlalchemy import Column, String, Float, Text, Integer, DateTime, JSON
from app.db.session import Base


class AgentModel(Base):
    __tablename__ = "ai_agents"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    role = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    capabilities = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="idle")  # idle, running, completed, error, offline
    last_run = Column(String(64), nullable=True)
    current_task = Column(String(255), nullable=True)
    progress_percent = Column(Float, nullable=True)
    metrics_processed = Column(Integer, nullable=True, default=0)
    color = Column(String(32), nullable=False, default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
