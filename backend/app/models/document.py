"""
SQLAlchemy models for RAG Document Ingestion and Vector Storage.
Implements DocumentModel and DocumentChunkModel with cascade deletion.
Vectors are stored as JSON arrays of floats for clean, persistent storage
in both MySQL 8 and SQLite without extra external infrastructure.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    content_type = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="processing")  # processing, indexed, error
    chunk_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Cascade delete all chunks when document is deleted
    chunks = relationship(
        "DocumentChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False, index=True)
    page_number = Column(Integer, nullable=True)  # Page for PDF, row batch for CSV, null for TXT
    content = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)
    embedding = Column(JSON, nullable=False)  # Stored normalized float vector
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="chunks")
