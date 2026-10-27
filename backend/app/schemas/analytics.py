from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class AskAnalyticsRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Natural language business question (e.g., 'Why did sales decrease last month?')",
    )
    range: Optional[Literal["7d", "30d", "90d", "1y"]] = Field(
        "30d",
        description="Date range window for analytics context",
    )

    model_config = ConfigDict(extra="ignore")


class MetricHighlight(BaseModel):
    label: str
    value: str
    change: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ChartSeries(BaseModel):
    key: str
    name: str
    color: str

    model_config = ConfigDict(populate_by_name=True)


class ChartData(BaseModel):
    type: Literal["bar", "line", "area"]
    title: str
    xAxisKey: str = Field("segment", alias="xAxisKey", validation_alias="x_axis_key")
    data: List[Dict[str, Any]]
    series: List[ChartSeries]

    model_config = ConfigDict(populate_by_name=True)


class TableData(BaseModel):
    columns: List[str]
    rows: List[List[Optional[Union[str, int, float]]]]

    model_config = ConfigDict(populate_by_name=True)


class DataSourceInfo(BaseModel):
    database: str
    tables: List[str]
    groundedMetricsCount: int = Field(..., alias="groundedMetricsCount", validation_alias="grounded_metrics_count")
    modelUsed: str = Field(..., alias="modelUsed", validation_alias="model_used")
    latencyMs: float = Field(..., alias="latencyMs", validation_alias="latency_ms")

    model_config = ConfigDict(populate_by_name=True)


class AnalyticsAskResponse(BaseModel):
    id: str
    sender: Literal["assistant"] = "assistant"
    timestamp: str
    content: str
    findings: Optional[List[str]] = None
    metrics: Optional[List[MetricHighlight]] = None
    chartData: Optional[ChartData] = Field(None, alias="chartData", validation_alias="chart_data")
    tableData: Optional[TableData] = Field(None, alias="tableData", validation_alias="table_data")
    suggestedFollowUps: Optional[List[str]] = Field(None, alias="suggestedFollowUps", validation_alias="suggested_follow_ups")
    dataSource: Optional[DataSourceInfo] = Field(None, alias="dataSource", validation_alias="data_source")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
