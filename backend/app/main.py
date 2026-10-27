import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.session import engine, Base, SessionLocal, check_db_connection
from app.models import seed_initial_data
from app.api.routes import (
    health_router,
    dashboard_router,
    agents_router,
    analytics_router,
    documents_router,
    rag_router,
    forecast_router,
    reports_router,
    datasets_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("insightflow.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    Verifies database tables and seeds initial data if database is reachable.
    """
    logger.info("Initializing InsightFlow AI Backend...")
    if settings.ENVIRONMENT.strip().lower() == "production" and not settings.API_AUTH_KEY.strip():
        logger.critical("FATAL CONFIGURATION: Cannot start in production without API_AUTH_KEY set!")
        raise RuntimeError("CRITICAL: API_AUTH_KEY must be configured when ENVIRONMENT=production.")

    is_healthy, latency, status_msg = check_db_connection()
    if is_healthy:
        logger.info(f"MySQL Database is connected ({latency}ms). Ensuring tables exist...")
        try:
            Base.metadata.create_all(bind=engine)
            from app.db.migrate_provenance import run_migration
            run_migration()
            with SessionLocal() as session:
                seed_initial_data(session)
            logger.info("Database tables and baseline seeds verified successfully.")
        except Exception as e:
            logger.error(f"Error during database startup migration/seed: {e}")
    else:
        logger.warning(
            f"MySQL Database is currently unreachable ({status_msg}). "
            "Backend starting in standby mode."
        )

    yield

    logger.info("Shutting down InsightFlow AI Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Business Intelligence Agent Platform API",
    lifespan=lifespan,
)

from app.core.middleware import SecurityAndRateLimitMiddleware

# Strict CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
# Security headers, payload size limit, and rate limiting
app.add_middleware(SecurityAndRateLimitMiddleware)


# Global Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check backend logs."},
    )


# Register API Routers
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(agents_router)
app.include_router(analytics_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(forecast_router)
app.include_router(reports_router)
app.include_router(datasets_router)



@app.get("/", tags=["Root"])
def root_info():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "documentation": "/docs",
    }
