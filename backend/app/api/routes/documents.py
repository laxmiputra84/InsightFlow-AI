"""
Document Ingestion & Management API Routes.
Provides endpoints for uploading, listing, and deleting RAG business documents.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_api_key
from app.schemas.rag import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
)
from app.services.rag import RagService

logger = logging.getLogger("insightflow.api.documents")

router = APIRouter(prefix="/api/documents", tags=["Documents"], dependencies=[Depends(verify_api_key)])



@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document file to ingest (.pdf, .txt, .csv)"),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest a business document (PDF, TXT, CSV).
    Extracts text, splits into chunks, computes dense embeddings, and stores in the vector index.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    try:
        content_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream.",
        )

    try:
        result = RagService.ingest_document(
            db=db,
            file_bytes=content_bytes,
            filename=file.filename,
            content_type=file.content_type or "",
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Unexpected error ingesting document '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while indexing document. Please verify the file and try again.",
        )


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """
    List all uploaded business documents and their indexing status.
    """
    try:
        docs = RagService.list_documents(db)
        return DocumentListResponse(documents=docs, total_count=len(docs))
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve indexed documents list.",
        )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document and cascade-delete all its indexed vector chunks.
    """
    try:
        filename = RagService.delete_document(db, document_id)
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )
        return DocumentDeleteResponse(
            document_id=document_id,
            filename=filename,
            deleted=True,
            message=f"Document '{filename}' and all associated vector chunks were successfully deleted.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document '{document_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
