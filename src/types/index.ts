export type DateRange = "7d" | "30d" | "90d" | "1y" | "custom";

export interface KpiMetric {
  id: string;
  label: string;
  value: string | number;
  changePercent: number;
  trend: "up" | "down" | "neutral";
  periodLabel: string;
  iconName: string;
  aiInsight?: string;
  sparklineData?: number[];
  dataProvenance?: string;
}

export interface RevenueDataPoint {
  date: string;
  revenue: number;
  target: number;
  orders: number;
  dataProvenance?: string;
}

export interface CategorySales {
  category: string;
  revenue: number;
  percentage: number;
  growth: number;
  color?: string;
  dataProvenance?: string;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  agent: "Analyst" | "Root Cause" | "Forecaster" | "Reporter" | "System" | string;
  title: string;
  description: string;
  type: "insight" | "alert" | "report" | "action";
  severity?: "normal" | "warning" | "success" | "critical";
  dataProvenance?: string;
}

export interface ReportItem {
  id: string;
  title: string;
  category: "Executive" | "Financial" | "Operational" | "Diagnostic" | "Forecast" | string;
  generatedAt: string;
  agent: string;
  status: "ready" | "processing" | "failed";
  summary: string;
  keyMetrics: { label: string; value: string }[];
  fileSize?: string;
  dataProvenance?: string;
  content?: string;
}

export interface AiChatMessage {
  id: string;
  sender: "user" | "assistant";
  timestamp: string;
  content: string;
  findings?: string[];
  metrics?: { label: string; value: string; change?: string }[];
  chartData?: {
    type: "bar" | "line" | "area";
    title: string;
    xAxisKey: string;
    data: Record<string, string | number>[];
    series: { key: string; name: string; color: string }[];
  };
  tableData?: {
    columns: string[];
    rows: (string | number)[][];
  };
  suggestedFollowUps?: string[];
  citations?: CitationItem[];
  dataSource?: {
    database: string;
    tables: string[];
    groundedMetricsCount: number;
    modelUsed: string;
    latencyMs: number;
  };
}

export interface UploadedDataPreview {
  fileName: string;
  fileSize: number;
  rowCount: number;
  columnCount: number;
  columns: { name: string; type: "string" | "number" | "date" | "boolean" }[];
  sampleRows: Record<string, any>[];
  validationIssues?: { row?: number; column?: string; message: string; type: "warning" | "error" }[];
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  description: string;
  capabilities: string[];
  status: "idle" | "running" | "completed" | "error" | "offline";
  lastRun?: string;
  currentTask?: string;
  progressPercent?: number;
  metricsProcessed?: number;
  color: string;
}

export interface AgentExecutionLog {
  id: string;
  timestamp: string;
  agentId: string;
  agentName: string;
  level: "info" | "success" | "warn" | "error";
  message: string;
}

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  company: string;
  department: string;
  avatarUrl?: string;
}

export interface SystemPreferences {
  theme: "dark" | "light" | "system";
  currency: "USD" | "EUR" | "GBP" | "CAD";
  aiModel: string;
  autoRunAgents: boolean;
  emailDigest: boolean;
  slackWebhookUrl?: string;
  backendApiUrl: string;
}

export interface BackendStatus {
  connected: boolean;
  latencyMs?: number;
  version?: string;
  checkedAt: string;
  error?: string;
}

export interface CitationItem {
  documentId: string;
  documentName: string;
  pageNumber?: number | null;
  chunkIndex: number;
  snippet: string;
  relevanceScore: number;
}

export interface DocumentItem {
  id: string;
  filename: string;
  contentType: string;
  fileSize: number;
  chunkCount: number;
  status: "pending" | "processing" | "indexed" | "error";
  createdAt: string;
  errorMessage?: string | null;
}

export interface DocumentUploadResponse {
  documentId: string;
  filename: string;
  contentType: string;
  fileSize: number;
  chunkCount: number;
  status: string;
  message: string;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  totalCount: number;
  indexedCount: number;
}

export interface DocumentDeleteResponse {
  documentId: string;
  deleted: boolean;
  message: string;
}

export interface RagAskResponse {
  id: string;
  query: string;
  answer: string;
  citations: CitationItem[];
  grounded: boolean;
  model: string;
  latencyMs: number;
  kpiContextIncluded?: boolean;
}

export interface RagHealthResponse {
  status: string;
  vectorStore: string;
  embeddingEngine: string;
  totalDocuments: number;
  indexedDocuments: number;
  totalChunks: number;
  supportedFormats: string[];
}

// ============================================================================
// Milestone 8: Predictive Analytics and Sales Forecasting Types
// ============================================================================

export interface ForecastAvailabilityResponse {
  hasSufficientData: boolean;
  message: string;
  totalObservations: number;
  minDate?: string | null;
  maxDate?: string | null;
  supportedMetrics: string[];
  requiredObservations: number;
  dataProvenance?: string;
  provenanceLabel?: string;
}

export interface HistoricalPoint {
  date: string;
  value: number;
  isActual: boolean;
  dataProvenance?: string;
}

export interface ForecastPoint {
  date: string;
  forecast: number;
  lowerBound: number;
  upperBound: number;
}

export interface ModelEvaluationMetric {
  modelName: string;
  mae: number;
  rmse: number;
  mape: number;
  selected: boolean;
}

export interface ForecastGenerateRequest {
  metricName: "revenue" | "orders" | string;
  horizonDays: number;
  testSize?: number;
  confidenceLevel?: number;
}

export interface ForecastGenerateResponse {
  runId: string;
  metricName: string;
  horizonDays: number;
  selectedModel: string;
  outOfSampleMetrics: {
    mae: number;
    rmse: number;
    mape: number;
  };
  candidateEvaluations: ModelEvaluationMetric[];
  trendDirection: "up" | "down" | "flat";
  projectedGrowthRate: number;
  historicalPoints: HistoricalPoint[];
  forecastPoints: ForecastPoint[];
  recommendations: string[];
  createdAt: string;
  dataProvenance?: string;
  provenanceLabel?: string;
}

export interface ForecastHistoryItem {
  id: string;
  metricName: string;
  horizonDays: number;
  modelName: string;
  mae: number;
  rmse: number;
  mape: number;
  trendDirection: "up" | "down" | "flat";
  growthRate: number;
  createdAt: string;
  dataProvenance?: string;
}

export interface ForecastHistoryResponse {
  runs: ForecastHistoryItem[];
  totalCount: number;
}

export interface ForecastEvaluateResponse {
  runId: string;
  metricName: string;
  evaluatedPointsCount: number;
  actualVsPredicted: {
    date: string;
    actual: number;
    predicted: number;
    error: number;
    lowerBound?: number;
    upperBound?: number;
  }[];
  realizedMae: number;
  realizedRmse: number;
  realizedMape: number;
  accuracyStatus: string;
}

// ============================================================================
// Real Dataset Types & Mappings
// ============================================================================

export interface ColumnSchema {
  name: string;
  dataType: string;
  detectedRole: string;
  missingCount: number;
  missingPercent: number;
  uniqueCount: number;
  sampleValues: (string | number | boolean | null)[];
}

export interface DetectedMappings {
  dateColumn?: string | null;
  amountColumn?: string | null;
  quantityColumn?: string | null;
  categoryColumn?: string | null;
  countryColumn?: string | null;
  customerColumn?: string | null;
  isOnlineRetail: boolean;
}

export interface DataQualityIssue {
  type: "info" | "warning" | "error" | string;
  field?: string | null;
  message: string;
  affectedRows?: number | null;
}

export interface DataQualityReport {
  qualityScore: number;
  totalRows: number;
  totalColumns: number;
  missingValuesTotal: number;
  duplicateRowsCount: number;
  invalidRowsCount: number;
  anomalyCount: number;
  issues: DataQualityIssue[];
}

export interface DatasetItem {
  id: string;
  name: string;
  filename: string;
  fileType: string;
  fileSize: number;
  rowCount: number;
  columnCount: number;
  qualityScore: number;
  isActive: boolean;
  detectedMappings: DetectedMappings;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetDetail extends DatasetItem {
  columnsSchema: ColumnSchema[];
  qualityReport: DataQualityReport;
}

export interface DatasetPreviewData {
  datasetId: string;
  columns: ColumnSchema[];
  rows: Record<string, any>[];
  totalRows: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DatasetKpiItem {
  id: string;
  label: string;
  value: string;
  rawValue?: number | null;
  changePercent?: number | null;
  trend?: "up" | "down" | "neutral" | null;
  periodLabel?: string | null;
  iconName?: string | null;
  aiInsight?: string | null;
  description?: string | null;
}

export interface DatasetTimeSeriesPoint {
  date: string;
  value: number;
  volume: number;
  cancellations?: number;
}

export interface DatasetDistributionItem {
  name: string;
  value: number;
  count: number;
  percentage: number;
}

export interface DatasetFilterOptions {
  availableRanges: string[];
  categories: string[];
  countries: string[];
  minDate?: string | null;
  maxDate?: string | null;
}

export interface DatasetDashboardData {
  datasetId: string;
  datasetName: string;
  rowCount: number;
  columnCount: number;
  qualityScore: number;
  kpis: DatasetKpiItem[];
  timeSeries: DatasetTimeSeriesPoint[];
  categoryBreakdown: DatasetDistributionItem[];
  countryBreakdown: DatasetDistributionItem[];
  filterOptions: DatasetFilterOptions;
  dataProvenance: string;
  lastRefreshed: string;
}

export interface DatasetAgentTaskResponse {
  agentId: string;
  agentName: string;
  status: "idle" | "running" | "completed" | "failed" | string;
  executionTimeMs: number;
  inputSummary?: string | null;
  findings: string[];
  metrics: Record<string, any>;
  recommendations?: string[] | null;
  citations: string[];
  errors?: string[];
  timestamp: string;
}

export interface DatasetSwarmResponse {
  datasetId: string;
  datasetName: string;
  status: string;
  executionTimeMs: number;
  query?: string | null;
  businessAnalyst: DatasetAgentTaskResponse;
  qualityAnalyst: DatasetAgentTaskResponse;
  forecastAnalyst: DatasetAgentTaskResponse;
  combinedExecutiveSummary: string;
  timestamp: string;
}

export interface CleaningRuleModel {
  ruleId: string;
  ruleName: string;
  description: string;
  affectedRows: number;
  targetColumns: string[];
  enabled: boolean;
}

export interface CleaningPreviewResponse {
  datasetId: string;
  datasetName: string;
  totalOriginalRows: number;
  totalCleanedRows: number;
  duplicatesRemoved: number;
  missingCellsImputed: number;
  whitespaceTrimmedCells: number;
  anomalousRowsAdjusted: number;
  proposedRules: CleaningRuleModel[];
  beforeSample: Record<string, any>[];
  afterSample: Record<string, any>[];
  approvalRequired: boolean;
}

export interface CleaningApplyResponse {
  status: string;
  message: string;
  originalDatasetId: string;
  cleanedDatasetId: string;
  cleanedDatasetName: string;
  rowsRetained: number;
  rowsRemoved: number;
}

export interface DatasetSixAgentWorkflowResponse {
  datasetId: string;
  datasetName: string;
  status: string;
  executionTimeMs: number;
  query?: string | null;
  understandingAgent: DatasetAgentTaskResponse;
  cleaningAgent: DatasetAgentTaskResponse;
  businessAgent: DatasetAgentTaskResponse;
  anomalyAgent: DatasetAgentTaskResponse;
  forecastingAgent: DatasetAgentTaskResponse;
  dashboardAgent: DatasetAgentTaskResponse;
  dashboardLayout: Record<string, any>;
  recommendations: string[];
  cleaningPreview?: CleaningPreviewResponse | null;
  executiveSummary: string;
  timestamp: string;
}

export interface ColumnProfile {
  name: string;
  dataType: string;
  semanticRole: string;
  missingCount: number;
  missingPercent: number;
  uniqueCount: number;
  sampleValues: any[];
}

export interface DatasetProfileResponse {
  datasetId: string;
  datasetName: string;
  rowCount: number;
  columnCount: number;
  fileType: string;
  fileSizeBytes: number;
  detectedDomain: "sales" | "finance" | "customer" | "inventory" | "general";
  domainConfidence: number;
  columnProfiles: ColumnProfile[];
  domainMappings: Record<string, string | null>;
  businessSummary: string;
  createdAt: string;
}

export interface CleaningOperation {
  ruleId: string;
  ruleName: string;
  description: string;
  affectedRows: number;
  targetColumns: string[];
  priority: "high" | "medium" | "low";
  enabled: boolean;
}

export interface DataQualityAnalysisResponse {
  datasetId: string;
  qualityScore: number;
  totalRows: number;
  totalColumns: number;
  totalCells: number;
  missingCells: number;
  missingCellRate: number;
  duplicateRows: number;
  duplicateRate: number;
  invalidDateCount: number;
  invalidDatesByCol: Record<string, number>;
  inconsistentCategoryCount: number;
  inconsistentCategories: Array<{
    column: string;
    rawUniqueCount: number;
    normalizedUniqueCount: number;
    casingDiscrepancies: number;
    sampleValues: string[];
  }>;
  suspiciousNumericCount: number;
  suspiciousNumericIssues: Array<{
    column: string;
    issueType: string;
    affectedCount: number;
    description: string;
  }>;
  suggestedOperations: CleaningOperation[];
  cleanlinessStatus: "healthy" | "moderate_issues" | "poor_quality";
  timestamp: string;
}

export interface MetricItem {
  id: string;
  label: string;
  value: string;
  rawValue?: number | null;
  unit?: string | null;
  trend?: "up" | "down" | "neutral" | null;
  changePercent?: number | null;
  periodLabel?: string | null;
  aiInsight?: string | null;
  description?: string | null;
}

export interface MissingColumnRequirement {
  metricName: string;
  missingColumns: string[];
  explanation: string;
}

export interface BusinessMetricsResponse {
  datasetId: string;
  domain: "sales" | "finance" | "customer" | "inventory" | "general";
  computedMetrics: MetricItem[];
  missingRequirements: MissingColumnRequirement[];
  domainDetails: Record<string, any>;
  temporalTrends: Array<{ date: string; value: number; volume?: number; profit?: number }>;
  topCategories: Array<{ name: string; value: number; count: number; percentage: number }>;
  topRegions: Array<{ name: string; value: number; count: number; percentage: number }>;
  findings: string[];
  citations: string[];
  timestamp: string;
}

export interface AnomalyItem {
  anomalyId: string;
  severity: "critical" | "warning" | "info";
  anomalyType: "spike" | "drop" | "outlier" | "suspicious_record";
  columnName?: string | null;
  title: string;
  description: string;
  statisticalMethod: string;
  isConfirmedBusinessProblem: boolean;
  businessInterpretation: string;
  affectedRecordsCount: number;
  evidence: Record<string, any>;
}

export interface AnomalyReportResponse {
  datasetId: string;
  totalAnomalies: number;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  anomalies: AnomalyItem[];
  summary: string;
  timestamp: string;
}

export interface BusinessAnalysisWorkflowResponse {
  datasetId: string;
  datasetName: string;
  status: string;
  executionTimeMs: number;
  domain: "sales" | "finance" | "customer" | "inventory" | "general";
  profile: DatasetProfileResponse;
  quality: DataQualityAnalysisResponse;
  businessAnalysis: BusinessMetricsResponse;
  anomalies: AnomalyReportResponse;
  executiveSummary: string;
  recommendations: string[];
  citations: string[];
  timestamp: string;
}

export interface AnalysisStatusResponse {
  datasetId: string;
  datasetName: string;
  status: string;
  domain?: string | null;
  hasResults: boolean;
  qualityScore?: number | null;
  lastAnalyzedAt?: string | null;
}





