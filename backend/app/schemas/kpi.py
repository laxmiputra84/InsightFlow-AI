from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict


class KpiMetricResponse(BaseModel):
    id: str
    label: str
    value: Union[str, float, int]
    changePercent: float = Field(..., alias="changePercent", validation_alias="change_percent")
    trend: str  # "up" | "down" | "neutral"
    periodLabel: str = Field(..., alias="periodLabel", validation_alias="period_label")
    iconName: str = Field(..., alias="iconName", validation_alias="icon_name")
    aiInsight: Optional[str] = Field(None, alias="aiInsight", validation_alias="ai_insight")
    sparklineData: Optional[List[float]] = Field(None, alias="sparklineData", validation_alias="sparkline_data")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
