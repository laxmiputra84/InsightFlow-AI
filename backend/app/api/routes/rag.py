"""
RAG Question Answering & Health API Routes.
Provides evidence-grounded document QA with citations and RAG readiness health check.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.rag import RagAskRequest, RagAskResponse, RagHealthResponse
from app.services.rag import RagService

logger = logging.getLogger("insightflow.api.rag")

router = APIRouter(prefix="/api/rag", tags=["RAG"], dependencies=[Depends(verify_api_key)])


@router.post("/ask", response_model=RagAskResponse, response_model_by_alias=True)
def ask_document_question(
    request: RagAskRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts a natural language business question and returns an evidence-grounded
    answer synthesized from retrieved document chunks with source citations.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    try:
        response = RagService.ask(
            db=db,
            query=query,
            top_k=request.top_k,
            document_ids=request.document_ids,
            include_kpi_context=request.include_kpi_context,
        )
        return response
    except Exception as e:
        logger.error(f"Error processing RAG query '{query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the document question. Please try again.",
        )


@router.get("/health", response_model=RagHealthResponse)
def get_rag_health(db: Session = Depends(get_db)):
    """
    Reports readiness and indexed statistics of the RAG pipeline components.
    """
    try:
        return RagService.get_health(db)
    except Exception as e:
        logger.error(f"Error checking RAG health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check RAG component health.",
        )
