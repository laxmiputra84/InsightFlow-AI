from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class ColumnProfile(BaseModel):
    name: str
    dataType: str = Field(..., alias="dataType")
    semanticRole: str = Field(..., alias="semanticRole")
    missingCount: int = Field(0, alias="missingCount")
    missingPercent: float = Field(0.0, alias="missingPercent")
    uniqueCount: int = Field(0, alias="uniqueCount")
    sampleValues: List[Any] = Field(default_factory=list, alias="sampleValues")

    model_config = ConfigDict(populate_by_name=True)


class DatasetProfileResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    rowCount: int = Field(..., alias="rowCount")
    columnCount: int = Field(..., alias="columnCount")
    fileType: str = Field(..., alias="fileType")
    fileSizeBytes: int = Field(..., alias="fileSizeBytes")
    detectedDomain: Literal["sales", "finance", "customer", "inventory", "general"] = Field(..., alias="detectedDomain")
    domainConfidence: float = Field(..., alias="domainConfidence")
    columnProfiles: List[ColumnProfile] = Field(default_factory=list, alias="columnProfiles")
    domainMappings: Dict[str, Optional[str]] = Field(default_factory=dict, alias="domainMappings")
    businessSummary: str = Field(..., alias="businessSummary")
    createdAt: str = Field(..., alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class CleaningOperation(BaseModel):
    ruleId: str = Field(..., alias="ruleId")
    ruleName: str = Field(..., alias="ruleName")
    description: str
    affectedRows: int = Field(..., alias="affectedRows")
    targetColumns: List[str] = Field(default_factory=list, alias="targetColumns")
    priority: Literal["high", "medium", "low"] = "medium"
    enabled: bool = True

    model_config = ConfigDict(populate_by_name=True)


class DataQualityAnalysisResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    qualityScore: float = Field(..., alias="qualityScore")
    totalRows: int = Field(..., alias="totalRows")
    totalColumns: int = Field(..., alias="totalColumns")
    totalCells: int = Field(..., alias="totalCells")
    missingCells: int = Field(0, alias="missingCells")
    missingCellRate: float = Field(0.0, alias="missingCellRate")
    duplicateRows: int = Field(0, alias="duplicateRows")
    duplicateRate: float = Field(0.0, alias="duplicateRate")
    invalidDateCount: int = Field(0, alias="invalidDateCount")
    invalidDatesByCol: Dict[str, int] = Field(default_factory=dict, alias="invalidDatesByCol")
    inconsistentCategoryCount: int = Field(0, alias="inconsistentCategoryCount")
    inconsistentCategories: List[Dict[str, Any]] = Field(default_factory=list, alias="inconsistentCategories")
    suspiciousNumericCount: int = Field(0, alias="suspiciousNumericCount")
    suspiciousNumericIssues: List[Dict[str, Any]] = Field(default_factory=list, alias="suspiciousNumericIssues")
    suggestedOperations: List[CleaningOperation] = Field(default_factory=list, alias="suggestedOperations")
    cleanlinessStatus: Literal["healthy", "moderate_issues", "poor_quality"] = Field(..., alias="cleanlinessStatus")
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class MetricItem(BaseModel):
    id: str
    label: str
    value: str
    rawValue: Optional[float] = Field(None, alias="rawValue")
    unit: Optional[str] = None
    trend: Optional[str] = None  # "up", "down", "neutral"
    changePercent: Optional[float] = Field(None, alias="changePercent")
    periodLabel: Optional[str] = Field(None, alias="periodLabel")
    aiInsight: Optional[str] = Field(None, alias="aiInsight")
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class MissingColumnRequirement(BaseModel):
    metricName: str = Field(..., alias="metricName")
    missingColumns: List[str] = Field(default_factory=list, alias="missingColumns")
    explanation: str

    model_config = ConfigDict(populate_by_name=True)


class BusinessMetricsResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    domain: Literal["sales", "finance", "customer", "inventory", "general"]
    computedMetrics: List[MetricItem] = Field(default_factory=list, alias="computedMetrics")
    missingRequirements: List[MissingColumnRequirement] = Field(default_factory=list, alias="missingRequirements")
    domainDetails: Dict[str, Any] = Field(default_factory=dict, alias="domainDetails")
    temporalTrends: List[Dict[str, Any]] = Field(default_factory=list, alias="temporalTrends")
    topCategories: List[Dict[str, Any]] = Field(default_factory=list, alias="topCategories")
    topRegions: List[Dict[str, Any]] = Field(default_factory=list, alias="topRegions")
    findings: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class AnomalyItem(BaseModel):
    anomalyId: str = Field(..., alias="anomalyId")
    severity: Literal["critical", "warning", "info"]
    anomalyType: Literal["spike", "drop", "outlier", "suspicious_record"] = Field(..., alias="anomalyType")
    columnName: Optional[str] = Field(None, alias="columnName")
    title: str
    description: str
    statisticalMethod: str = Field(..., alias="statisticalMethod")
    isConfirmedBusinessProblem: bool = Field(..., alias="isConfirmedBusinessProblem")
    businessInterpretation: str = Field(..., alias="businessInterpretation")
    affectedRecordsCount: int = Field(..., alias="affectedRecordsCount")
    evidence: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class AnomalyReportResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    totalAnomalies: int = Field(..., alias="totalAnomalies")
    criticalCount: int = Field(0, alias="criticalCount")
    warningCount: int = Field(0, alias="warningCount")
    infoCount: int = Field(0, alias="infoCount")
    anomalies: List[AnomalyItem] = Field(default_factory=list)
    summary: str
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class BusinessAnalysisWorkflowResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    status: str
    executionTimeMs: int = Field(..., alias="executionTimeMs")
    domain: Literal["sales", "finance", "customer", "inventory", "general"]
    profile: DatasetProfileResponse
    quality: DataQualityAnalysisResponse
    businessAnalysis: BusinessMetricsResponse = Field(..., alias="businessAnalysis")
    anomalies: AnomalyReportResponse
    executiveSummary: str = Field(..., alias="executiveSummary")
    recommendations: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class AnalysisStatusResponse(BaseModel):
    datasetId: str = Field(..., alias="datasetId")
    datasetName: str = Field(..., alias="datasetName")
    status: str
    domain: Optional[str] = None
    hasResults: bool = Field(..., alias="hasResults")
    qualityScore: Optional[float] = Field(None, alias="qualityScore")
    lastAnalyzedAt: Optional[str] = Field(None, alias="lastAnalyzedAt")

    model_config = ConfigDict(populate_by_name=True)
