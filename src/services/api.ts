/**
 * InsightFlow AI - Centralized Typed API Client
 * Connects frontend directly to FastAPI backend and MySQL database.
 * STRICT RULE: No fabricated data or hardcoded mock fallbacks.
 * Unreachable endpoints return transparent error and unavailable states.
 */

import {
  KpiMetric,
  RevenueDataPoint,
  CategorySales,
  ActivityEvent,
  ReportItem,
  AiChatMessage,
  AgentInfo,
  BackendStatus,
  DateRange,
  DocumentItem,
  DocumentUploadResponse,
  DocumentListResponse,
  DocumentDeleteResponse,
  RagAskResponse,
  RagHealthResponse,
  ForecastAvailabilityResponse,
  ForecastGenerateRequest,
  ForecastGenerateResponse,
  ForecastHistoryResponse,
  ForecastEvaluateResponse,
  DatasetItem,
  DatasetDetail,
  DatasetPreviewData,
  DatasetDashboardData,
  DatasetAgentTaskResponse,
  DatasetSwarmResponse,
  CleaningPreviewResponse,
  CleaningApplyResponse,
  DatasetSixAgentWorkflowResponse,
  DatasetProfileResponse,
  DataQualityAnalysisResponse,
  BusinessMetricsResponse,
  AnomalyReportResponse,
  BusinessAnalysisWorkflowResponse,
  AnalysisStatusResponse,
} from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export function getAuthHeaders(includeContentType = true): Record<string, string> {
  const headers: Record<string, string> = {};
  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }
  // Retrieve from ephemeral tab session storage (never leaked in bundles)
  const apiKey =
    typeof window !== "undefined"
      ? sessionStorage.getItem("insightflow_session_key") ||
        localStorage.getItem("insightflow_api_key")
      : null;
  if (apiKey && apiKey.trim()) {
    headers["X-API-Key"] = apiKey.trim();
  }
  return headers;
}

export interface ApiResponse<T> {
  data: T | null;
  status: "success" | "error";
  error?: string;
  source: "verified_backend" | "unavailable";
  dataProvenance?: string;
}

export const InsightFlowApi = {
  // ==========================================================================
  // Health & System Connectivity
  // ==========================================================================
  async checkHealth(): Promise<BackendStatus> {
    const checkedAt = new Date().toLocaleTimeString();
    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        const json = await res.json();
        return {
          connected: json.status === "ok",
          latencyMs: json.database_latency_ms,
          version: json.version,
          checkedAt,
        };
      }
      return {
        connected: false,
        checkedAt,
        error: `HTTP ${res.status}: ${res.statusText}`,
      };
    } catch (err: any) {
      return {
        connected: false,
        checkedAt,
        error: err?.message || "FastAPI connection refused",
      };
    }
  },

  // ==========================================================================
  // Dashboard & Metrics (MySQL Ground Truth)
  // ==========================================================================
  async getDashboardKpis(
    range: DateRange = "30d"
  ): Promise<ApiResponse<KpiMetric[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/kpis?range=${range}`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      const errText = await res.text().catch(() => "");
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${errText || res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to communicate with KPI service",
        source: "unavailable",
      };
    }
  },

  async getRevenueTrend(
    range: DateRange = "30d"
  ): Promise<ApiResponse<RevenueDataPoint[]>> {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/dashboard/revenue-trend?range=${range}`,
        {
          headers: getAuthHeaders(false),
          cache: "no-store",
          signal: AbortSignal.timeout(8000),
        }
      );
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: data[0]?.dataProvenance || "synthetic_seed",
        };
      }
      const errText = await res.text().catch(() => "");
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${errText || res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to fetch revenue time-series",
        source: "unavailable",
      };
    }
  },

  async getCategorySales(): Promise<ApiResponse<CategorySales[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/categories`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: data[0]?.dataProvenance || "synthetic_seed",
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to fetch category sales",
        source: "unavailable",
      };
    }
  },

  async getGeographicPerformance(): Promise<ApiResponse<any[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/geographic`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "synthetic_seed",
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to fetch geographic performance",
        source: "unavailable",
      };
    }
  },

  async getRecentAlerts(): Promise<ApiResponse<any[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/alerts`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_system",
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to fetch alerts",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Autonomous Agents & LangGraph Swarm
  // ==========================================================================
  async getAgents(): Promise<ApiResponse<AgentInfo[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/agents`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to retrieve agents from MySQL",
        source: "unavailable",
      };
    }
  },

  async runAgent(agentId: string): Promise<ApiResponse<AgentInfo>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/agents/${agentId}/run`, {
        method: "POST",
        headers: getAuthHeaders(true),
        signal: AbortSignal.timeout(25000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      const errText = await res.text().catch(() => "");
      return {
        data: null,
        status: "error",
        error: `Agent run failed (${res.status}): ${errText || res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Agent execution request timed out",
        source: "unavailable",
      };
    }
  },

  async runAllAgents(): Promise<ApiResponse<AgentInfo[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/agents/run-all`, {
        method: "POST",
        headers: getAuthHeaders(true),
        signal: AbortSignal.timeout(30000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      const errText = await res.text().catch(() => "");
      return {
        data: null,
        status: "error",
        error: `Swarm run failed: ${errText || res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Swarm execution request timed out",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Natural Language AI Analytics Assistant (LangGraph & LangChain)
  // ==========================================================================
  async askAi(
    query: string,
    range: DateRange = "30d"
  ): Promise<ApiResponse<AiChatMessage>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/analytics/ask`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({ query: query.trim(), range }),
        signal: AbortSignal.timeout(25000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      const errJson = await res.json().catch(() => null);
      const detail = errJson?.detail || `HTTP ${res.status}: ${res.statusText}`;
      return {
        data: null,
        status: "error",
        error: typeof detail === "string" ? detail : JSON.stringify(detail),
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to communicate with AI analytics service",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Executive Reports (MySQL Persisted)
  // ==========================================================================
  async getReports(): Promise<ApiResponse<ReportItem[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/reports`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load reports from MySQL",
        source: "unavailable",
      };
    }
  },

  async generateReport(payload: {
    category?: string;
    range?: string;
    custom_title?: string;
  }): Promise<ApiResponse<ReportItem>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/reports/generate`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(20000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: "verified_mysql",
        };
      }
      const errText = await res.text().catch(() => "");
      return {
        data: null,
        status: "error",
        error: `Failed to synthesize report: ${errText || res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Report generation timed out",
        source: "unavailable",
      };
    }
  },

  getReportDownloadUrl(reportId: string, format: "md" | "csv" = "md"): string {
    return `${API_BASE_URL}/api/reports/${reportId}/download?format=${format}`;
  },

  // ==========================================================================
  // Documents & RAG Pipeline
  // ==========================================================================
  async uploadDocument(file: File): Promise<ApiResponse<DocumentUploadResponse>> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const headers = getAuthHeaders(false);
      // Remove Content-Type so browser sets multipart boundary automatically
      delete headers["Content-Type"];

      const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: "POST",
        headers,
        body: formData,
        signal: AbortSignal.timeout(45000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Upload failed (HTTP ${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Network error while uploading document",
        source: "unavailable",
      };
    }
  },

  async getDocuments(): Promise<ApiResponse<DocumentListResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to list documents",
        source: "unavailable",
      };
    }
  },

  async listDocuments(): Promise<ApiResponse<DocumentListResponse>> {
    return this.getDocuments();
  },

  async deleteDocument(documentId: string): Promise<ApiResponse<DocumentDeleteResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
        method: "DELETE",
        headers: getAuthHeaders(false),
        signal: AbortSignal.timeout(10000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Deletion failed (HTTP ${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to delete document",
        source: "unavailable",
      };
    }
  },

  async askRag(
    queryOrPayload:
      | string
      | {
          query: string;
          topK?: number;
          documentIds?: string[];
          includeKpiContext?: boolean;
        },
    options?: {
      topK?: number;
      documentIds?: string[];
      includeKpiContext?: boolean;
    }
  ): Promise<ApiResponse<RagAskResponse>> {
    try {
      const query =
        typeof queryOrPayload === "string"
          ? queryOrPayload
          : queryOrPayload.query;
      const topK =
        typeof queryOrPayload === "string"
          ? options?.topK || 4
          : queryOrPayload.topK || 4;
      const documentIds =
        typeof queryOrPayload === "string"
          ? options?.documentIds
          : queryOrPayload.documentIds;
      const includeKpiContext =
        typeof queryOrPayload === "string"
          ? options?.includeKpiContext ?? true
          : queryOrPayload.includeKpiContext ?? true;

      const res = await fetch(`${API_BASE_URL}/api/rag/ask`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          query: query.trim(),
          top_k: topK,
          document_ids: documentIds,
          include_kpi_context: includeKpiContext,
        }),
        signal: AbortSignal.timeout(30000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `RAG Query failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "RAG QA service unreachable",
        source: "unavailable",
      };
    }
  },

  async getRagHealth(): Promise<ApiResponse<RagHealthResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/rag/health`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to check RAG health",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Predictive Analytics & Sales Forecasting
  // ==========================================================================
  async getForecastAvailability(
    metric: string = "revenue"
  ): Promise<ApiResponse<ForecastAvailabilityResponse>> {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/forecast/availability?metric=${metric}`,
        {
          headers: getAuthHeaders(false),
          cache: "no-store",
          signal: AbortSignal.timeout(6000),
        }
      );
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: data.dataProvenance,
        };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to inspect forecast availability",
        source: "unavailable",
      };
    }
  },

  async generateForecast(
    req: ForecastGenerateRequest
  ): Promise<ApiResponse<ForecastGenerateResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/forecast/generate`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          metric_name: req.metricName,
          horizon_days: req.horizonDays,
          test_size: req.testSize,
          confidence_level: req.confidenceLevel,
        }),
        signal: AbortSignal.timeout(30000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          data,
          status: "success",
          source: "verified_backend",
          dataProvenance: data.dataProvenance,
        };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Forecast generation failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Forecast generation service timed out",
        source: "unavailable",
      };
    }
  },

  async getForecastHistory(limit: number = 20): Promise<ApiResponse<ForecastHistoryResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/forecast/history?limit=${limit}`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to retrieve forecast runs",
        source: "unavailable",
      };
    }
  },

  async evaluateForecast(runId: string): Promise<ApiResponse<ForecastEvaluateResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/forecast/evaluate?run_id=${runId}`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Evaluation failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Forecast evaluation failed",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Real Dataset & Agentic Analytics Engine
  // ==========================================================================

  async uploadDataset(file: File): Promise<ApiResponse<DatasetDetail>> {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const headers = getAuthHeaders(false); // multipart/form-data sets its own boundary

      const res = await fetch(`${API_BASE_URL}/api/datasets/upload`, {
        method: "POST",
        headers,
        body: formData,
        signal: AbortSignal.timeout(60000), // 60s for large CSV/XLSX
      });

      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Upload failed with HTTP ${res.status}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Dataset upload timed out or failed",
        source: "unavailable",
      };
    }
  },

  async getDatasets(): Promise<ApiResponse<DatasetItem[]>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to list datasets",
        source: "unavailable",
      };
    }
  },

  async getActiveDataset(): Promise<ApiResponse<DatasetItem | null>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/active`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      if (res.status === 404) {
        return { data: null, status: "success", source: "verified_backend" };
      }
      return {
        data: null,
        status: "error",
        error: `HTTP ${res.status}: ${res.statusText}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to check active dataset",
        source: "unavailable",
      };
    }
  },

  async getDatasetDetail(datasetId: string): Promise<ApiResponse<DatasetDetail>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `HTTP ${res.status}`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to inspect dataset details",
        source: "unavailable",
      };
    }
  },

  async activateDataset(datasetId: string): Promise<ApiResponse<{ status: string; datasetId: string; message: string }>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/activate`, {
        method: "POST",
        headers: getAuthHeaders(true),
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Failed to activate dataset (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Activation request failed",
        source: "unavailable",
      };
    }
  },

  async getDatasetPreview(
    datasetId: string,
    page: number = 1,
    pageSize: number = 20,
    search: string = ""
  ): Promise<ApiResponse<DatasetPreviewData>> {
    try {
      const searchParam = search ? `&search=${encodeURIComponent(search)}` : "";
      const res = await fetch(
        `${API_BASE_URL}/api/datasets/${datasetId}/preview?page=${page}&page_size=${pageSize}${searchParam}`,
        {
          headers: getAuthHeaders(false),
          cache: "no-store",
          signal: AbortSignal.timeout(10000),
        }
      );
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Preview failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load dataset preview",
        source: "unavailable",
      };
    }
  },

  async getDatasetDashboard(
    datasetId: string,
    params?: { range?: string; category?: string; country?: string; search?: string }
  ): Promise<ApiResponse<DatasetDashboardData>> {
    try {
      const q = new URLSearchParams();
      if (params?.range) q.set("range", params.range);
      if (params?.category) q.set("category", params.category);
      if (params?.country) q.set("country", params.country);
      if (params?.search) q.set("search", params.search);

      const qs = q.toString() ? `?${q.toString()}` : "";
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/dashboard${qs}`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(12000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Dashboard aggregation failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load dataset dashboard",
        source: "unavailable",
      };
    }
  },

  async runDatasetAgent(
    datasetId: string,
    agentId: string,
    query?: string
  ): Promise<ApiResponse<DatasetAgentTaskResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/agents/${agentId}/run`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({ query: query || null }),
        signal: AbortSignal.timeout(45000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Agent execution failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Agent execution timed out or failed",
        source: "unavailable",
      };
    }
  },

  async runDatasetSwarm(
    datasetId: string,
    query?: string
  ): Promise<ApiResponse<DatasetSwarmResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/agents/run-all`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({ query: query || null }),
        signal: AbortSignal.timeout(60000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Swarm workflow failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Multi-agent swarm execution timed out",
        source: "unavailable",
      };
    }
  },

  async runDatasetWorkflow(
    datasetId: string,
    query?: string
  ): Promise<ApiResponse<DatasetSixAgentWorkflowResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/workflow/run${query ? `?query=${encodeURIComponent(query)}` : ""}`, {
        method: "POST",
        headers: getAuthHeaders(true),
        signal: AbortSignal.timeout(90000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `6-Agent workflow execution failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Workflow execution timed out or failed",
        source: "unavailable",
      };
    }
  },

  async getDatasetCleaningPreview(
    datasetId: string
  ): Promise<ApiResponse<CleaningPreviewResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/clean/preview`, {
        method: "GET",
        headers: getAuthHeaders(false),
        signal: AbortSignal.timeout(30000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Failed to fetch cleaning preview (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to fetch cleaning preview",
        source: "unavailable",
      };
    }
  },

  async applyDatasetCleaningPlan(
    datasetId: string,
    approvedRuleIds?: string[],
    newDatasetName?: string,
    setAsActive = true
  ): Promise<ApiResponse<CleaningApplyResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/clean/apply`, {
        method: "POST",
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          approvedRuleIds: approvedRuleIds || null,
          newDatasetName: newDatasetName || null,
          setAsActive,
        }),
        signal: AbortSignal.timeout(60000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Failed to apply cleaning plan (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to apply cleaning plan",
        source: "unavailable",
      };
    }
  },

  async deleteDataset(
    datasetId: string
  ): Promise<
    ApiResponse<{
      status: string;
      message: string;
      datasetId?: string;
      nextActiveDatasetId?: string | null;
      wasActive?: boolean;
    }>
  > {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}`, {
        method: "DELETE",
        headers: getAuthHeaders(false),
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Delete failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Dataset deletion failed",
        source: "unavailable",
      };
    }
  },

  // ==========================================================================
  // Business Analysis Engine Endpoints
  // ==========================================================================

  async runBusinessAnalysis(
    datasetId: string
  ): Promise<ApiResponse<BusinessAnalysisWorkflowResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/analysis`, {
        method: "POST",
        headers: getAuthHeaders(true),
        signal: AbortSignal.timeout(90000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Business analysis failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Business analysis timed out or failed",
        source: "unavailable",
      };
    }
  },

  async getDatasetProfile(
    datasetId: string
  ): Promise<ApiResponse<DatasetProfileResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/profile`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Profile fetch failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load dataset profile",
        source: "unavailable",
      };
    }
  },

  async getDatasetQuality(
    datasetId: string
  ): Promise<ApiResponse<DataQualityAnalysisResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/quality`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Quality audit failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load data quality report",
        source: "unavailable",
      };
    }
  },

  async getDatasetBusinessAnalysis(
    datasetId: string
  ): Promise<ApiResponse<BusinessMetricsResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/business-analysis`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(20000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Business metrics failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load business metrics",
        source: "unavailable",
      };
    }
  },

  async getDatasetAnomalies(
    datasetId: string
  ): Promise<ApiResponse<AnomalyReportResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/anomalies`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(20000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Anomaly audit failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to load anomaly report",
        source: "unavailable",
      };
    }
  },

  async getAnalysisStatus(
    datasetId: string
  ): Promise<ApiResponse<AnalysisStatusResponse>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/analysis/status`, {
        headers: getAuthHeaders(false),
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      });
      if (res.ok) {
        const data = await res.json();
        return { data, status: "success", source: "verified_backend" };
      }
      const errJson = await res.json().catch(() => null);
      return {
        data: null,
        status: "error",
        error: errJson?.detail || `Status check failed (${res.status})`,
        source: "unavailable",
      };
    } catch (err: any) {
      return {
        data: null,
        status: "error",
        error: err?.message || "Failed to check analysis status",
        source: "unavailable",
      };
    }
  },
};

