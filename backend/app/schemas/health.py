from typing import Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    database: str = "connected"
    database_latency_ms: Optional[float] = None
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)
