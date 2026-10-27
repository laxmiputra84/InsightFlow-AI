from datetime import datetime
from fastapi import APIRouter, Response, status
from app.schemas.health import HealthResponse
from app.db.session import check_db_connection
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(response: Response):
    """
    Verifies API liveness and active MySQL database connectivity.
    Returns HTTP 200 when database is healthy, or HTTP 503 when database is unreachable.
    """
    is_healthy, latency_ms, db_status = check_db_connection()

    current_time = datetime.utcnow().isoformat() + "Z"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded",
            version=settings.VERSION,
            database=db_status,
            database_latency_ms=latency_ms,
            timestamp=current_time,
        )

    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        database="connected",
        database_latency_ms=latency_ms,
        timestamp=current_time,
    )
