from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from app.db.session import Base


class DatasetModel(Base):
    """
    SQLAlchemy model representing an uploaded business dataset (CSV / Excel).
    Stores metadata, detected schema, column roles, and data quality metrics.
    """
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(32), nullable=False)  # csv, xlsx, xls
    file_size = Column(Integer, nullable=False, default=0)
    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)

    # Inferred schema: List of {name, data_type, detected_role, missing_count, unique_count, sample_values}
    columns_schema = Column(JSON, nullable=False, default=list)

    # Inferred business mappings: {date_column, amount_column, quantity_column, category_column, country_column, customer_column, is_online_retail}
    detected_mappings = Column(JSON, nullable=False, default=dict)

    # Data quality report: {quality_score, missing_total, duplicate_rows, invalid_rows, anomaly_count, issues}
    quality_report = Column(JSON, nullable=False, default=dict)

    # Whether this dataset is currently selected as active dashboard source
    is_active = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
