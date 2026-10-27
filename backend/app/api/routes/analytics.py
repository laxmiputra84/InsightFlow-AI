import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.analytics import AskAnalyticsRequest, AnalyticsAskResponse
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"], dependencies=[Depends(verify_api_key)])


@router.post("/ask", response_model=AnalyticsAskResponse, response_model_by_alias=True)
def ask_business_question(
    request: AskAnalyticsRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts a natural language business question, retrieves verified read-only metrics
    from MySQL, and returns a grounded explanation synthesized via Gemini.
    Zero arbitrary SQL execution allowed.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business question query string cannot be empty.",
        )

    try:
        response = AnalyticsService.generate_analytics_response(
            db=db,
            query=query,
            range_type=request.range or "30d",
        )
        return response
    except Exception as e:
        logger.error(f"Error processing AI analytics query '{query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process business inquiry due to an internal error. Please try again.",
        )
