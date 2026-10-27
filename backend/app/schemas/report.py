from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ReportKeyMetric(BaseModel):
    label: str
    value: str

    model_config = ConfigDict(populate_by_name=True)


class ReportItemResponse(BaseModel):
    id: str
    title: str
    category: str
    generatedAt: str = Field(..., alias="generatedAt", validation_alias="generated_at")
    agent: str
    status: str
    summary: str
    keyMetrics: List[ReportKeyMetric] = Field(default_factory=list, alias="keyMetrics", validation_alias="key_metrics")
    fileSize: Optional[str] = Field("1.2 MB", alias="fileSize", validation_alias="file_size")
    dataProvenance: str = Field("verified_mysql", alias="dataProvenance", validation_alias="data_provenance")
    content: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ReportGenerateRequest(BaseModel):
    category: Optional[str] = "Executive"
    range: Optional[str] = "30d"
    custom_title: Optional[str] = None
