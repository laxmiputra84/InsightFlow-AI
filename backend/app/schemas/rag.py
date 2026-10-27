"""
Pydantic v2 Schemas for RAG Document Ingestion, Retrieval, and Question Answering.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., alias="documentId", validation_alias="document_id")
    filename: str
    content_type: str = Field(..., alias="contentType", validation_alias="content_type")
    file_size: int = Field(..., alias="fileSize", validation_alias="file_size")
    chunk_count: int = Field(..., alias="chunkCount", validation_alias="chunk_count")
    status: Literal["indexed", "processing", "error"]
    message: str

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DocumentItemResponse(BaseModel):
    id: str
    filename: str
    content_type: str = Field(..., alias="contentType", validation_alias="content_type")
    file_size: int = Field(..., alias="fileSize", validation_alias="file_size")
    chunk_count: int = Field(..., alias="chunkCount", validation_alias="chunk_count")
    status: Literal["indexed", "processing", "error"]
    created_at: str = Field(..., alias="createdAt", validation_alias="created_at")
    error_message: Optional[str] = Field(None, alias="errorMessage", validation_alias="error_message")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: List[DocumentItemResponse]
    total_count: int = Field(..., alias="totalCount", validation_alias="total_count")

    model_config = ConfigDict(populate_by_name=True)


class DocumentDeleteResponse(BaseModel):
    document_id: str = Field(..., alias="documentId", validation_alias="document_id")
    filename: str
    deleted: bool
    message: str

    model_config = ConfigDict(populate_by_name=True)


class CitationItem(BaseModel):
    document_id: str = Field(..., alias="documentId", validation_alias="document_id")
    document_name: str = Field(..., alias="documentName", validation_alias="document_name")
    page_number: Optional[int] = Field(None, alias="pageNumber", validation_alias="page_number")
    chunk_index: int = Field(..., alias="chunkIndex", validation_alias="chunk_index")
    snippet: str
    relevance_score: float = Field(..., alias="relevanceScore", validation_alias="relevance_score")

    model_config = ConfigDict(populate_by_name=True)


class RagAskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000, description="User question to answer using document evidence")
    top_k: int = Field(default=4, ge=1, le=20, alias="topK", validation_alias="top_k", description="Number of evidence chunks to retrieve")
    document_ids: Optional[List[str]] = Field(None, alias="documentIds", validation_alias="document_ids", description="Optional filter by document IDs")
    include_kpi_context: bool = Field(default=False, alias="includeKpiContext", validation_alias="include_kpi_context", description="Whether to include verified KPI telemetry")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class RagAskResponse(BaseModel):
    id: str
    query: str
    answer: str
    citations: List[CitationItem]
    grounded: bool
    confidence_score: float = Field(..., alias="confidenceScore", validation_alias="confidence_score")
    chunks_retrieved_count: int = Field(..., alias="chunksRetrievedCount", validation_alias="chunks_retrieved_count")
    latency_ms: float = Field(..., alias="latencyMs", validation_alias="latency_ms")
    model_used: str = Field(..., alias="modelUsed", validation_alias="model_used")
    kpi_context_included: bool = Field(default=False, alias="kpiContextIncluded", validation_alias="kpi_context_included")

    model_config = ConfigDict(populate_by_name=True)


class RagHealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unavailable"]
    documents_indexed: int = Field(..., alias="documentsIndexed", validation_alias="documents_indexed")
    total_chunks: int = Field(..., alias="totalChunks", validation_alias="total_chunks")
    vector_store: str = Field("sql_persistent_vectors", alias="vectorStore", validation_alias="vector_store")
    embedding_provider: str = Field(..., alias="embeddingProvider", validation_alias="embedding_provider")
    supported_formats: List[str] = Field(default=["pdf", "txt", "csv"], alias="supportedFormats", validation_alias="supported_formats")

    model_config = ConfigDict(populate_by_name=True)
