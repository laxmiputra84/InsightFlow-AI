import time
import logging
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Configure engine with connection pooling and health pre-ping
connect_args = {}
if "sqlite" in settings.sqlalchemy_database_url:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a managed database session.
    Automatically closes session after request handling and rolls back on unhandled error.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, float, str]:
    """
    Executes a lightweight query (SELECT 1) to verify database liveness.
    Returns: (is_healthy, latency_ms, status_message)
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return True, latency_ms, "connected"
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Database health check failed: {e}")
        return False, latency_ms, f"disconnected: {str(e)}"
