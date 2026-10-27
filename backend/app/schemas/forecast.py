from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ForecastAvailabilityResponse(CamelModel):
    has_sufficient_data: bool = Field(..., description="Whether minimum historical observations threshold is met")
    message: str = Field(..., description="Explanation of data sufficiency or requirement")
    total_observations: int = Field(..., description="Number of historical daily observations available")
    min_date: Optional[str] = Field(None, description="Earliest date in historical series (YYYY-MM-DD)")
    max_date: Optional[str] = Field(None, description="Latest date in historical series (YYYY-MM-DD)")
    supported_metrics: List[str] = Field(default_factory=lambda: ["revenue", "orders"])
    required_observations: int = Field(14, description="Minimum daily observations required to run models")
    data_provenance: str = Field(default="synthetic_seed", description="Origin of training observations ('synthetic_seed' or 'empirical_recorded')")
    provenance_label: str = Field(default="Synthetic Baseline (Demo Seed)", description="Human-readable provenance tag")


class HistoricalPoint(CamelModel):
    date: str
    value: float
    is_actual: bool = True
    data_provenance: str = "synthetic_seed"


class ForecastPoint(CamelModel):
    date: str
    forecast: float
    lower_bound: float
    upper_bound: float


class ModelEvaluationMetric(CamelModel):
    model_name: str
    mae: float
    rmse: float
    mape: float
    selected: bool


class ForecastGenerateRequest(CamelModel):
    metric_name: str = Field(default="revenue", description="'revenue' or 'orders'")
    horizon_days: int = Field(default=14, ge=1, le=90, description="Forecast horizon in days (1 to 90)")
    test_size: Optional[int] = Field(default=7, ge=3, le=30, description="Chronological holdout test set size in days")
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99, description="Confidence level for prediction bands")


class ForecastGenerateResponse(CamelModel):
    run_id: str
    metric_name: str
    horizon_days: int
    selected_model: str
    out_of_sample_metrics: Dict[str, float]
    candidate_evaluations: List[ModelEvaluationMetric]
    trend_direction: str  # "up" | "down" | "flat"
    projected_growth_rate: float
    historical_points: List[HistoricalPoint]
    forecast_points: List[ForecastPoint]
    recommendations: List[str]
    created_at: str
    data_provenance: str = Field(default="synthetic_seed", description="Origin of historical training data")
    provenance_label: str = Field(default="Synthetic Baseline (Demo Seed)", description="Human-readable provenance tag")


class ForecastHistoryItem(CamelModel):
    id: str
    metric_name: str
    horizon_days: int
    model_name: str
    mae: float
    rmse: float
    mape: float
    trend_direction: str
    growth_rate: float
    created_at: str
    data_provenance: str = "synthetic_seed"


class ForecastHistoryResponse(CamelModel):
    runs: List[ForecastHistoryItem]
    total_count: int


class ForecastEvaluateResponse(CamelModel):
    run_id: str
    metric_name: str
    evaluated_points_count: int
    actual_vs_predicted: List[Dict[str, Any]]
    realized_mae: float
    realized_rmse: float
    realized_mape: float
    accuracy_status: str
