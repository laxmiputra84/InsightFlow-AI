from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RevenueDataPointResponse(BaseModel):
    date: str
    revenue: float
    target: float
    orders: float
    dataProvenance: str = Field("synthetic_seed", alias="dataProvenance", validation_alias="data_provenance")

    model_config = ConfigDict(populate_by_name=True)


class CategorySalesResponse(BaseModel):
    category: str
    revenue: float
    percentage: float
    growth: float
    color: str
    dataProvenance: str = Field("synthetic_seed", alias="dataProvenance", validation_alias="data_provenance")

    model_config = ConfigDict(populate_by_name=True)


class GeographicRegionResponse(BaseModel):
    id: str
    name: str
    revenue: float
    revenueFormatted: str = Field(..., alias="revenueFormatted", validation_alias="revenue_formatted")
    growth: float
    growthFormatted: str = Field(..., alias="growthFormatted", validation_alias="growth_formatted")
    dataProvenance: str = Field("synthetic_seed", alias="dataProvenance", validation_alias="data_provenance")

    model_config = ConfigDict(populate_by_name=True)


class RecentAlertResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: str
    severity: str = "info"
    dataProvenance: str = Field("verified_system", alias="dataProvenance", validation_alias="data_provenance")

    model_config = ConfigDict(populate_by_name=True)
