import logging
from sqlalchemy import text
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def run_migration():
    """Adds data_provenance column to daily_metrics if not already present."""
    with engine.connect() as conn:
        try:
            # Check if column already exists
            res = conn.execute(text("SHOW COLUMNS FROM daily_metrics LIKE 'data_provenance'"))
            if res.fetchone():
                logger.info("Column 'data_provenance' already exists on 'daily_metrics'.")
                return

            logger.info("Adding column 'data_provenance' to 'daily_metrics'...")
            conn.execute(
                text("ALTER TABLE daily_metrics ADD COLUMN data_provenance VARCHAR(32) NOT NULL DEFAULT 'synthetic_seed'")
            )
            conn.commit()
            logger.info("Successfully added 'data_provenance' column.")
        except Exception as e:
            logger.error(f"Migration error: {e}")

if __name__ == "__main__":
    run_migration()
