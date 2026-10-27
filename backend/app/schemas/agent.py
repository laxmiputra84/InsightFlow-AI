from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AgentInfoResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    capabilities: List[str]
    status: str  # "idle" | "running" | "completed" | "error" | "offline"
    lastRun: Optional[str] = Field(None, alias="lastRun", validation_alias="last_run")
    currentTask: Optional[str] = Field(None, alias="currentTask", validation_alias="current_task")
    progressPercent: Optional[float] = Field(None, alias="progressPercent", validation_alias="progress_percent")
    metricsProcessed: Optional[int] = Field(None, alias="metricsProcessed", validation_alias="metrics_processed")
    color: str

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
