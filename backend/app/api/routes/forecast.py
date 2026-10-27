import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.forecast import (
    ForecastAvailabilityResponse,
    ForecastGenerateRequest,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastEvaluateResponse,
)
from app.services.forecast import ForecastingService

logger = logging.getLogger("insightflow.forecast.routes")

router = APIRouter(prefix="/api/forecast", tags=["Predictive Forecasting"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/availability",
    response_model=ForecastAvailabilityResponse,
    summary="Check data sufficiency for forecasting",
    description="Inspects historical observations and verifies if minimum 14 daily data points exist.",
)
def check_forecast_availability(
    metric: str = Query("revenue", description="Metric to inspect ('revenue' or 'orders')"),
    db: Session = Depends(get_db),
):
    try:
        return ForecastingService.check_availability(db, metric_name=metric)
    except Exception as e:
        logger.error(f"Error checking forecast availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check data availability due to an internal error.",
        )


@router.post(
    "/generate",
    response_model=ForecastGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate time-series forecast with model evaluation",
    description=(
        "Fits baseline and statistical candidate models on chronological train split, "
        "selects model with lowest out-of-sample RMSE, and produces projected values "
        "with prediction intervals and grounded business recommendations."
    ),
)
def generate_forecast(
    request: ForecastGenerateRequest,
    db: Session = Depends(get_db),
):
    try:
        return ForecastingService.generate_forecast(db, request)
    except ValueError as ve:
        logger.warning(f"Forecasting validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Error generating forecast: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Forecasting failed due to an internal calculation or database error.",
        )


@router.get(
    "/history",
    response_model=ForecastHistoryResponse,
    summary="List historical forecast runs",
    description="Retrieves log of previously generated forecasts and their out-of-sample accuracy metrics.",
)
def get_forecast_history(
    limit: int = Query(20, ge=1, le=100, description="Max runs to return"),
    db: Session = Depends(get_db),
):
    try:
        return ForecastingService.get_history(db, limit=limit)
    except Exception as e:
        logger.error(f"Error retrieving forecast history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve forecast history due to an internal error.",
        )


@router.get(
    "/evaluate",
    response_model=ForecastEvaluateResponse,
    summary="Evaluate forecast run against realized actuals",
    description="Compares past forecast projections with subsequent actuals recorded in the database.",
)
def evaluate_forecast(
    run_id: str = Query(..., description="ID of the forecast run to evaluate"),
    db: Session = Depends(get_db),
):
    try:
        return ForecastingService.evaluate_past_run(db, run_id=run_id)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Error evaluating forecast run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed due to an internal error.",
        )
