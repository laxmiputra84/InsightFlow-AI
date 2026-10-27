from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ColumnSchema(BaseModel):
    name: str
    dataType: str = Field(..., alias="dataType", validation_alias="dataType")
    detectedRole: str = Field(..., alias="detectedRole", validation_alias="detectedRole")
    missingCount: int = Field(0, alias="missingCount", validation_alias="missingCount")
    missingPercent: float = Field(0.0, alias="missingPercent", validation_alias="missingPercent")
    uniqueCount: int = Field(0, alias="uniqueCount", validation_alias="uniqueCount")
    sampleValues: List[Any] = Field(default_factory=list, alias="sampleValues", validation_alias="sampleValues")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DetectedMappings(BaseModel):
    dateColumn: Optional[str] = Field(None, alias="dateColumn", validation_alias="date_column")
    amountColumn: Optional[str] = Field(None, alias="amountColumn", validation_alias="amount_column")
    quantityColumn: Optional[str] = Field(None, alias="quantityColumn", validation_alias="quantity_column")
    categoryColumn: Optional[str] = Field(None, alias="categoryColumn", validation_alias="category_column")
    countryColumn: Optional[str] = Field(None, alias="countryColumn", validation_alias="country_column")
    customerColumn: Optional[str] = Field(None, alias="customerColumn", validation_alias="customer_column")
    isOnlineRetail: bool = Field(False, alias="isOnlineRetail", validation_alias="is_online_retail")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DataQualityIssue(BaseModel):
    type: str  # info, warning, error
    field: Optional[str] = None
    message: str
    affectedRows: Optional[int] = Field(None, alias="affectedRows")

    model_config = ConfigDict(populate_by_name=True)


class DataQualityReport(BaseModel):
    qualityScore: float = Field(..., alias="qualityScore", validation_alias="qualityScore")
    totalRows: int = Field(..., alias="totalRows", validation_alias="totalRows")
    totalColumns: int = Field(..., alias="totalColumns", validation_alias="totalColumns")
    missingValuesTotal: int = Field(0, alias="missingValuesTotal", validation_alias="missingValuesTotal")
    duplicateRowsCount: int = Field(0, alias="duplicateRowsCount", validation_alias="duplicateRowsCount")
    invalidRowsCount: int = Field(0, alias="invalidRowsCount", validation_alias="invalidRowsCount")
    anomalyCount: int = Field(0, alias="anomalyCount", validation_alias="anomalyCount")
    issues: List[DataQualityIssue] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DatasetItemResponse(BaseModel):
    id: str
    name: str
    filename: str
    fileType: str = Field(..., alias="fileType", validation_alias="file_type")
    fileSize: int = Field(..., alias="fileSize", validation_alias="file_size")
    rowCount: int = Field(..., alias="rowCount", validation_alias="row_count")
    columnCount: int = Field(..., alias="columnCount", validation_alias="column_count")
    qualityScore: float = Field(100.0, alias="qualityScore")
    isActive: bool = Field(False, alias="isActive", validation_alias="is_active")
    detectedMappings: DetectedMappings = Field(..., alias="detectedMappings", validation_alias="detected_mappings")
    createdAt: Union[str, datetime] = Field(..., alias="createdAt", validation_alias="created_at")
    updatedAt: Union[str, datetime] = Field(..., alias="updatedAt", validation_alias="updated_at")

    @field_validator("createdAt", "updatedAt", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S UTC")
        return str(v)

    @field_validator("qualityScore", mode="before")
    @classmethod
    def extract_quality_score(cls, v, info):
        if isinstance(v, (int, float)):
            return float(v)
        # If passed from model or dict
        return 100.0

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DatasetDetailResponse(DatasetItemResponse):
    columnsSchema: List[ColumnSchema] = Field(default_factory=list, alias="columnsSchema", validation_alias="columns_schema")
    qualityReport: DataQualityReport = Field(..., alias="qualityReport", validation_alias="quality_report")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DatasetPreviewResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    columns: List[ColumnSchema]
    rows: List[Dict[str, Any]]
    totalRows: int = Field(..., alias="totalRows")
    page: int
    pageSize: int = Field(..., alias="pageSize")
    totalPages: int = Field(..., alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


class DatasetKpiItem(BaseModel):
    id: str
    label: str
    value: str
    rawValue: Optional[float] = Field(None, alias="rawValue")
    changePercent: Optional[float] = Field(None, alias="changePercent")
    trend: Optional[str] = None
    periodLabel: Optional[str] = Field(None, alias="periodLabel")
    iconName: Optional[str] = Field(None, alias="iconName")
    aiInsight: Optional[str] = Field(None, alias="aiInsight")
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DatasetTimeSeriesPoint(BaseModel):
    date: str
    value: float
    volume: int
    cancellations: Optional[int] = 0

    model_config = ConfigDict(populate_by_name=True)


class DatasetDistributionItem(BaseModel):
    name: str
    value: float
    count: int
    percentage: float

    model_config = ConfigDict(populate_by_name=True)


class DatasetFilterOptions(BaseModel):
    availableRanges: List[str] = Field(default_factory=list, alias="availableRanges")
    categories: List[str] = Field(default_factory=list)
    countries: List[str] = Field(default_factory=list)
    minDate: Optional[str] = Field(None, alias="minDate")
    maxDate: Optional[str] = Field(None, alias="maxDate")

    model_config = ConfigDict(populate_by_name=True)


class DatasetDashboardResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    rowCount: int = Field(..., alias="rowCount")
    columnCount: int = Field(..., alias="columnCount")
    qualityScore: float = Field(100.0, alias="qualityScore")
    kpis: List[DatasetKpiItem]
    timeSeries: List[DatasetTimeSeriesPoint] = Field(default_factory=list, alias="timeSeries")
    categoryBreakdown: List[DatasetDistributionItem] = Field(default_factory=list, alias="categoryBreakdown")
    countryBreakdown: List[DatasetDistributionItem] = Field(default_factory=list, alias="countryBreakdown")
    filterOptions: DatasetFilterOptions = Field(..., alias="filterOptions")
    dataProvenance: str = Field("real_dataset", alias="dataProvenance")
    lastRefreshed: str = Field(..., alias="lastRefreshed")

    model_config = ConfigDict(populate_by_name=True)


class DatasetAgentTaskResponse(BaseModel):
    agentId: str = Field(..., alias="agentId")
    agentName: str = Field(..., alias="agentName")
    status: str
    executionTimeMs: int = Field(..., alias="executionTimeMs")
    inputSummary: Optional[str] = Field(None, alias="inputSummary")
    findings: List[str]
    metrics: Dict[str, Any]
    recommendations: Optional[List[str]] = None
    citations: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class DatasetSwarmResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    status: str
    executionTimeMs: int = Field(..., alias="executionTimeMs")
    query: Optional[str] = None
    businessAnalyst: DatasetAgentTaskResponse = Field(..., alias="businessAnalyst")
    qualityAnalyst: DatasetAgentTaskResponse = Field(..., alias="qualityAnalyst")
    forecastAnalyst: DatasetAgentTaskResponse = Field(..., alias="forecastAnalyst")
    combinedExecutiveSummary: str = Field(..., alias="combinedExecutiveSummary")
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class CleaningRuleModel(BaseModel):
    ruleId: str = Field(..., alias="ruleId")
    ruleName: str = Field(..., alias="ruleName")
    description: str
    affectedRows: int = Field(..., alias="affectedRows")
    targetColumns: List[str] = Field(default_factory=list, alias="targetColumns")
    enabled: bool = True

    model_config = ConfigDict(populate_by_name=True)


class CleaningPreviewResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    totalOriginalRows: int = Field(..., alias="totalOriginalRows")
    totalCleanedRows: int = Field(..., alias="totalCleanedRows")
    duplicatesRemoved: int = Field(0, alias="duplicatesRemoved")
    missingCellsImputed: int = Field(0, alias="missingCellsImputed")
    whitespaceTrimmedCells: int = Field(0, alias="whitespaceTrimmedCells")
    anomalousRowsAdjusted: int = Field(0, alias="anomalousRowsAdjusted")
    proposedRules: List[CleaningRuleModel] = Field(default_factory=list, alias="proposedRules")
    beforeSample: List[Dict[str, Any]] = Field(default_factory=list, alias="beforeSample")
    afterSample: List[Dict[str, Any]] = Field(default_factory=list, alias="afterSample")
    approvalRequired: bool = Field(True, alias="approvalRequired")

    model_config = ConfigDict(populate_by_name=True)


class CleaningApplyRequest(BaseModel):
    approvedRuleIds: Optional[List[str]] = Field(default=None, alias="approvedRuleIds")
    newDatasetName: Optional[str] = Field(default=None, alias="newDatasetName")
    setAsActive: bool = Field(default=True, alias="setAsActive")

    model_config = ConfigDict(populate_by_name=True)


class CleaningApplyResponse(BaseModel):
    status: str
    message: str
    originalDatasetId: str = Field(..., alias="originalDatasetId")
    cleanedDatasetId: str = Field(..., alias="cleanedDatasetId")
    cleanedDatasetName: str = Field(..., alias="cleanedDatasetName")
    rowsRetained: int = Field(..., alias="rowsRetained")
    rowsRemoved: int = Field(..., alias="rowsRemoved")

    model_config = ConfigDict(populate_by_name=True)


class DatasetSixAgentWorkflowResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    status: str
    executionTimeMs: int = Field(..., alias="executionTimeMs")
    query: Optional[str] = None
    understandingAgent: DatasetAgentTaskResponse = Field(..., alias="understandingAgent")
    cleaningAgent: DatasetAgentTaskResponse = Field(..., alias="cleaningAgent")
    businessAgent: DatasetAgentTaskResponse = Field(..., alias="businessAgent")
    anomalyAgent: DatasetAgentTaskResponse = Field(..., alias="anomalyAgent")
    forecastingAgent: DatasetAgentTaskResponse = Field(..., alias="forecastingAgent")
    dashboardAgent: DatasetAgentTaskResponse = Field(..., alias="dashboardAgent")
    dashboardLayout: Dict[str, Any] = Field(default_factory=dict, alias="dashboardLayout")
    recommendations: List[str] = Field(default_factory=list)
    cleaningPreview: Optional[CleaningPreviewResponse] = Field(None, alias="cleaningPreview")
    executiveSummary: str = Field(..., alias="executiveSummary")
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)

