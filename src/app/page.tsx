"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  LineChart,
  Bot,
  AlertTriangle,
  FileSpreadsheet,
  UploadCloud,
  CheckCircle,
  Clock,
  ChevronDown,
  ArrowUp,
  ArrowDown,
  Send,
  Loader2,
  Globe,
  DollarSign,
  ShoppingCart,
  Users,
  BarChart3,
  ShieldAlert,
  RefreshCw,
  Database,
  Info,
  Play,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Layers,
  Lightbulb,
  Zap,
  AlertOctagon,
  Activity,
  CheckSquare,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { AppShell } from "@/components/layout/AppShell";
import { InsightFlowApi } from "@/services/api";
import {
  DatasetItem,
  DatasetDashboardData,
  DatasetPreviewData,
  DatasetKpiItem,
  DateRange,
  AiChatMessage,
  BusinessAnalysisWorkflowResponse,
  AnomalyItem,
  MetricItem,
  MissingColumnRequirement,
} from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const PIE_COLORS = [
  "#38bdf8",
  "#818cf8",
  "#c084fc",
  "#34d399",
  "#fbbf24",
  "#f87171",
  "#a78bfa",
  "#2dd4bf",
];

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [dashboardData, setDashboardData] = useState<DatasetDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Business Analysis Engine State
  const [businessAnalysis, setBusinessAnalysis] = useState<BusinessAnalysisWorkflowResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [anomalySeverityFilter, setAnomalySeverityFilter] = useState<"all" | "critical" | "warning" | "info">("all");

  // Filters
  const [range, setRange] = useState<string>("all");
  const [category, setCategory] = useState<string>("all");
  const [country, setCountry] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  // Paginated Preview
  const [previewData, setPreviewData] = useState<DatasetPreviewData | null>(null);
  const [previewPage, setPreviewPage] = useState<number>(1);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  // AI Assistant Chat State
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    { sender: "user" | "assistant"; text: string; findings?: string[]; latency?: number; error?: boolean }[]
  >([]);
  const [isAsking, setIsAsking] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Load initial dataset list
  useEffect(() => {
    loadInitialDatasets();
  }, []);

  // When selected dataset or filters change, reload dashboard
  useEffect(() => {
    if (selectedDatasetId) {
      loadDashboard(selectedDatasetId);
      loadPreview(selectedDatasetId, 1, search);
      loadBusinessAnalysis(selectedDatasetId);
    } else {
      setDashboardData(null);
      setPreviewData(null);
      setBusinessAnalysis(null);
      setLoading(false);
    }
  }, [selectedDatasetId, range, category, country]);

  const loadBusinessAnalysis = async (datasetId: string) => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await InsightFlowApi.runBusinessAnalysis(datasetId);
      if (res.data) {
        setBusinessAnalysis(res.data);
      } else {
        setAnalysisError(res.error || "Business analysis engine unavailable");
      }
    } catch (err: any) {
      setAnalysisError(err?.message || "Communication failure with business analysis engine");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadInitialDatasets = async () => {
    setLoading(true);
    try {
      const res = await InsightFlowApi.getDatasets();
      if (res.data && res.data.length > 0) {
        setDatasets(res.data);
        const active = res.data.find((d) => d.isActive) || res.data[0];
        setSelectedDatasetId(active.id);
      } else {
        setDatasets([]);
        setSelectedDatasetId("");
        setDashboardData(null);
        setPreviewData(null);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load datasets");
      setDatasets([]);
      setSelectedDatasetId("");
      setDashboardData(null);
      setPreviewData(null);
      setLoading(false);
    }
  };

  const loadDashboard = async (datasetId: string) => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (range !== "all") params.range = range;
      if (category !== "all") params.category = category;
      if (country !== "all") params.country = country;
      if (search.trim()) params.search = search.trim();

      const res = await InsightFlowApi.getDatasetDashboard(datasetId, params);
      if (res.data) {
        setDashboardData(res.data);
      } else {
        setError(res.error || "Dashboard data unavailable from backend");
      }
    } catch (err: any) {
      setError(err?.message || "Communication failure with dashboard service");
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async (datasetId: string, page: number, query: string) => {
    setPreviewLoading(true);
    try {
      const res = await InsightFlowApi.getDatasetPreview(datasetId, page, 10, query);
      if (res.data) {
        setPreviewData(res.data);
        setPreviewPage(page);
      }
    } catch (err) {
      console.warn("Preview load error:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleApplySearch = () => {
    if (selectedDatasetId) {
      loadDashboard(selectedDatasetId);
      loadPreview(selectedDatasetId, 1, search);
    }
  };

  const handleResetFilters = () => {
    setRange("all");
    setCategory("all");
    setCountry("all");
    setSearch("");
  };

  const handleAskQuestion = async (queryText?: string) => {
    const q = (queryText || chatInput).trim();
    if (!q || isAsking) return;

    setChatInput("");
    setChatMessages((prev) => [...prev, { sender: "user", text: q }]);
    setIsAsking(true);

    try {
      // Query dataset agent with question
      const res = await InsightFlowApi.runDatasetAgent(selectedDatasetId, "business_analyst", q);
      if (res.data) {
        setChatMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: res.data?.findings.join("\n\n") || "Analysis complete.",
            findings: res.data?.findings,
            latency: res.data?.executionTimeMs,
          },
        ]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: res.error || "Unable to answer question with current dataset context.",
            error: true,
          },
        ]);
      }
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: `Inquiry failed: ${err?.message || "Backend error"}.`,
          error: true,
        },
      ]);
    } finally {
      setIsAsking(false);
      setTimeout(() => {
        chatScrollRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  };

  const activeDatasetObj = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Top Provenance & Dataset Switcher Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-[#0b1120] border border-white/[0.08] rounded-2xl shadow-xl">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-cyan-400" />
              <span className="text-xs text-slate-400 font-medium">Active Dataset:</span>
            </div>

            {datasets.length === 0 ? (
              <span className="text-xs text-amber-400">No datasets found</span>
            ) : (
              <select
                value={selectedDatasetId}
                onChange={(e) => {
                  setSelectedDatasetId(e.target.value);
                  handleResetFilters();
                }}
                className="rounded-xl border border-white/10 bg-slate-900 px-3 py-1.5 text-xs text-white font-semibold focus:border-cyan-500 focus:outline-none"
              >
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name} ({ds.rowCount.toLocaleString()} rows) {ds.isActive ? "★ Active" : ""}
                  </option>
                ))}
              </select>
            )}

            {activeDatasetObj && (
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <span className="hidden sm:inline">•</span>
                <span className="text-slate-300">{activeDatasetObj.columnCount} columns</span>
                <span>•</span>
                <span className="text-emerald-400 font-semibold">{activeDatasetObj.qualityScore.toFixed(1)}% Clean</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {dashboardData?.lastRefreshed && (
              <span className="text-[11px] text-slate-400 font-mono">
                Synced: <strong className="text-slate-200">{dashboardData.lastRefreshed}</strong>
              </span>
            )}
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                if (selectedDatasetId) {
                  loadBusinessAnalysis(selectedDatasetId);
                  loadDashboard(selectedDatasetId);
                }
              }}
              disabled={isAnalyzing || !selectedDatasetId}
              className="text-xs h-8 gap-1.5 bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white shadow-md shadow-indigo-500/20"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5 text-cyan-200" />
                  <span>Run 8-Stage Analysis</span>
                </>
              )}
            </Button>

            <button
              onClick={() => {
                if (selectedDatasetId) {
                  loadDashboard(selectedDatasetId);
                  loadBusinessAnalysis(selectedDatasetId);
                }
              }}
              disabled={loading || isAnalyzing || !selectedDatasetId}
              className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading || isAnalyzing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>

            <Link href="/upload">
              <Button size="sm" variant="outline" className="text-xs h-8 gap-1.5">
                <UploadCloud className="h-3.5 w-3.5 text-indigo-400" />
                Upload Dataset
              </Button>
            </Link>
          </div>
        </div>

        {/* Empty State when no dataset exists */}
        {datasets.length === 0 && !loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center space-y-4">
            <FileSpreadsheet className="h-10 w-10 text-slate-500 mx-auto" />
            <h3 className="text-base font-semibold text-white">No Dataset Loaded</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              InsightFlow AI generates interactive dashboards strictly from uploaded real datasets. Upload a CSV or Excel file to get started.
            </p>
            <Link href="/upload">
              <Button variant="primary" size="sm" className="gap-2">
                <UploadCloud className="h-4 w-4" />
                Upload CSV or Excel Dataset
              </Button>
            </Link>
          </div>
        )}

        {/* Error Callout */}
        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Dashboard Content */}
        {dashboardData && (
          <div className="space-y-6">
            {/* Analysis Progress Banner */}
            {isAnalyzing && (
              <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-indigo-200 animate-pulse">
                <div className="flex items-center gap-2.5">
                  <Loader2 className="h-4 w-4 text-cyan-400 animate-spin shrink-0" />
                  <span>
                    <strong>LangGraph 8-Stage Analysis Executing:</strong> [1. Validation] → [2. Profiling] → [3. Quality] → [4. Analysis] → [5. Anomalies] → [6. Insights] → [7. Validation] → [8. Complete]
                  </span>
                </div>
                <Badge variant="purple" size="sm">
                  Autonomous Pipeline Active
                </Badge>
              </div>
            )}

            {/* Analysis Error Alert with Retry */}
            {analysisError && (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 flex items-center justify-between text-xs text-rose-300">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="h-4 w-4 text-rose-400 shrink-0" />
                  <span>{analysisError}</span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => selectedDatasetId && loadBusinessAnalysis(selectedDatasetId)}
                  className="h-7 text-xs border-rose-500/40 text-rose-200"
                >
                  Retry Analysis
                </Button>
              </div>
            )}

            {/* Executive Overview Hero Card */}
            {businessAnalysis && (
              <div className="rounded-2xl border border-white/[0.08] bg-gradient-to-br from-[#0c1322] via-[#0d1629] to-[#0a101f] p-5 shadow-2xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-cyan-400" />
                      <h2 className="text-sm font-bold text-white tracking-wide uppercase">Executive Overview</h2>
                    </div>
                    <Badge
                      variant={
                        businessAnalysis.domain === "sales"
                          ? "success"
                          : businessAnalysis.domain === "finance"
                          ? "info"
                          : businessAnalysis.domain === "customer"
                          ? "purple"
                          : businessAnalysis.domain === "inventory"
                          ? "warning"
                          : "default"
                      }
                      size="sm"
                    >
                      {businessAnalysis.domain.toUpperCase()} DOMAIN ({Math.round(businessAnalysis.profile.domainConfidence * 100)}% Confidence)
                    </Badge>
                    <Badge
                      variant={businessAnalysis.quality.cleanlinessStatus === "healthy" ? "success" : "warning"}
                      size="sm"
                    >
                      {businessAnalysis.quality.qualityScore.toFixed(1)}% Data Hygiene
                    </Badge>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Audited {businessAnalysis.profile.rowCount.toLocaleString()} records • {businessAnalysis.executionTimeMs}ms
                  </span>
                </div>

                <div className="space-y-3">
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {businessAnalysis.executiveSummary}
                  </p>

                  {/* Grounded Key Findings */}
                  {businessAnalysis.businessAnalysis.findings.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {businessAnalysis.businessAnalysis.findings.slice(0, 4).map((f, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-1.5 text-[11px] text-cyan-200/90 bg-cyan-950/40 border border-cyan-800/40 rounded-lg px-2.5 py-1"
                        >
                          <CheckCircle2 className="h-3 w-3 text-cyan-400 shrink-0" />
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Missing Column Requirements Explanation */}
                  {businessAnalysis.businessAnalysis.missingRequirements.length > 0 && (
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 space-y-1.5 text-xs text-amber-200">
                      <div className="flex items-center gap-1.5 font-semibold text-amber-300">
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                        <span>Data Requirement Notice (Zero Hallucinated Numbers):</span>
                      </div>
                      <div className="space-y-1 pl-5">
                        {businessAnalysis.businessAnalysis.missingRequirements.map((mr, idx) => (
                          <div key={idx} className="text-[11px] text-amber-200/90">
                            <strong>{mr.metricName}:</strong> {mr.explanation}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Online Retail Domain Rules Indicator */}
            {activeDatasetObj?.detectedMappings.isOnlineRetail && (
              <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3.5 flex items-center justify-between text-xs text-cyan-200">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>
                    <strong>UCI Online Retail Rules Active:</strong> InvoiceNo cancellations (prefix &apos;C&apos;) and negative return quantities are cleanly segmented from gross transaction volume.
                  </span>
                </div>
                <Badge variant="purple" size="sm">
                  Deterministic Business Logic
                </Badge>
              </div>
            )}

            {/* Interactive Filters Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-900/80 text-xs">
              <div className="flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-1.5 text-slate-400 font-semibold mr-1">
                  <Filter className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Filters:</span>
                </div>

                {/* Range Filter */}
                {dashboardData.filterOptions.availableRanges.length > 0 && (
                  <select
                    value={range}
                    onChange={(e) => setRange(e.target.value)}
                    className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="all">Time Range: All Observations</option>
                    {dashboardData.filterOptions.availableRanges.map((r) => (
                      <option key={r} value={r}>
                        Time Range: {r.toUpperCase()}
                      </option>
                    ))}
                  </select>
                )}

                {/* Category Filter */}
                {dashboardData.filterOptions.categories.length > 0 && (
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-white focus:border-indigo-500 focus:outline-none max-w-[180px] truncate"
                  >
                    <option value="all">Category: All Categories</option>
                    {dashboardData.filterOptions.categories.map((c) => (
                      <option key={c} value={c}>
                        Category: {c}
                      </option>
                    ))}
                  </select>
                )}

                {/* Country Filter */}
                {dashboardData.filterOptions.countries.length > 0 && (
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="all">Country: All Regions</option>
                    {dashboardData.filterOptions.countries.map((ct) => (
                      <option key={ct} value={ct}>
                        Country: {ct}
                      </option>
                    ))}
                  </select>
                )}

                {/* Reset */}
                {(range !== "all" || category !== "all" || country !== "all" || search) && (
                  <button
                    onClick={handleResetFilters}
                    className="text-xs text-rose-400 hover:underline px-2"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {/* Keyword Search */}
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleApplySearch()}
                  placeholder="Filter records..."
                  className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
                <Button size="sm" variant="outline" onClick={handleApplySearch} className="h-7 text-xs px-2.5">
                  Apply
                </Button>
              </div>
            </div>

            {/* Dynamic KPIs Grid: Domain-Specific Metrics or Baseline */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {businessAnalysis?.businessAnalysis?.computedMetrics && businessAnalysis.businessAnalysis.computedMetrics.length > 0 ? (
                businessAnalysis.businessAnalysis.computedMetrics.map((kpi) => (
                  <div
                    key={kpi.id}
                    className="rounded-2xl border border-white/[0.08] bg-slate-900/80 p-4 shadow-lg flex flex-col justify-between space-y-2 hover:border-cyan-500/30 transition-colors"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-medium truncate">{kpi.label}</span>
                      {kpi.trend && (
                        <span
                          className={`flex items-center gap-0.5 text-[11px] font-semibold ${
                            kpi.trend === "up"
                              ? "text-emerald-400"
                              : kpi.trend === "down"
                              ? "text-rose-400"
                              : "text-slate-400"
                          }`}
                        >
                          {kpi.trend === "up" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {kpi.changePercent ? `${kpi.changePercent}%` : ""}
                        </span>
                      )}
                    </div>

                    <div>
                      <p className="text-2xl font-bold text-white font-mono">{kpi.value}</p>
                      {kpi.periodLabel && (
                        <span className="text-[10px] text-slate-500">{kpi.periodLabel}</span>
                      )}
                    </div>

                    {kpi.aiInsight ? (
                      <div className="text-[11px] text-cyan-300/90 bg-cyan-950/40 border border-cyan-800/40 rounded-lg p-2 font-sans">
                        {kpi.aiInsight}
                      </div>
                    ) : kpi.description ? (
                      <span className="text-[10px] text-slate-500 italic">{kpi.description}</span>
                    ) : null}
                  </div>
                ))
              ) : (
                dashboardData.kpis.map((kpi) => (
                  <div
                    key={kpi.id}
                    className="rounded-2xl border border-white/[0.08] bg-slate-900/80 p-4 shadow-lg flex flex-col justify-between space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-medium truncate">{kpi.label}</span>
                      {kpi.trend && (
                        <span
                          className={`flex items-center gap-0.5 text-[11px] font-semibold ${
                            kpi.trend === "up"
                              ? "text-emerald-400"
                              : kpi.trend === "down"
                              ? "text-rose-400"
                              : "text-slate-400"
                          }`}
                        >
                          {kpi.trend === "up" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {kpi.changePercent ? `${kpi.changePercent}%` : ""}
                        </span>
                      )}
                    </div>

                    <div>
                      <p className="text-2xl font-bold text-white font-mono">{kpi.value}</p>
                      {kpi.periodLabel && (
                        <span className="text-[10px] text-slate-500">{kpi.periodLabel}</span>
                      )}
                    </div>

                    {kpi.aiInsight ? (
                      <div className="text-[11px] text-cyan-300/90 bg-cyan-950/40 border border-cyan-800/40 rounded-lg p-2 font-sans">
                        {kpi.aiInsight}
                      </div>
                    ) : kpi.description ? (
                      <span className="text-[10px] text-slate-500 italic">{kpi.description}</span>
                    ) : null}
                  </div>
                ))
              )}
            </div>

            {/* Charts Row: Time Series & Category Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Time-Series Trend */}
              <div className="lg:col-span-2 rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <LineChart className="h-4 w-4 text-cyan-400" />
                      Temporal Revenue & Volume Trajectory
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Grounded daily aggregation across validated records
                    </p>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {dashboardData.timeSeries.length} Days Observed
                  </span>
                </div>

                {dashboardData.timeSeries.length === 0 ? (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-500">
                    No time-series date column detected in this dataset.
                  </div>
                ) : (
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={dashboardData.timeSeries}>
                        <defs>
                          <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis
                          dataKey="date"
                          stroke="#64748b"
                          tick={{ fill: "#94a3b8", fontSize: 10 }}
                          tickLine={false}
                        />
                        <YAxis
                          stroke="#64748b"
                          tick={{ fill: "#94a3b8", fontSize: 10 }}
                          tickLine={false}
                          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const rev = payload.find((p) => p.dataKey === "value")?.value;
                              const vol = payload.find((p) => p.dataKey === "volume")?.value;
                              const canc = payload.find((p) => p.dataKey === "cancellations")?.value;
                              return (
                                <div className="rounded-xl border border-slate-800 bg-slate-950/95 p-3 text-xs shadow-xl space-y-1">
                                  <p className="font-bold text-white border-b border-slate-800 pb-1">{label}</p>
                                  <p className="text-cyan-400 font-mono">
                                    Revenue: ${Number(rev).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                  </p>
                                  <p className="text-slate-300 font-mono">Volume: {vol} items</p>
                                  {canc !== undefined && Number(canc) > 0 && (
                                    <p className="text-rose-400 font-mono">Cancelled: {Number(canc)} orders</p>
                                  )}
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="value"
                          stroke="#38bdf8"
                          strokeWidth={2}
                          fillOpacity={1}
                          fill="url(#revenueGrad)"
                          name="Revenue"
                        />
                        <Line
                          type="monotone"
                          dataKey="volume"
                          stroke="#818cf8"
                          strokeWidth={1.5}
                          dot={false}
                          name="Items"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Category / Product Breakdown Pie Chart */}
              <div className="rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <PieChart className="h-4 w-4 text-purple-400" />
                      Category Distribution
                    </h3>
                    <p className="text-[11px] text-slate-400">Top revenue contributors</p>
                  </div>
                </div>

                {dashboardData.categoryBreakdown.length === 0 ? (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-500">
                    No categorical dimension detected.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={dashboardData.categoryBreakdown}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            innerRadius={45}
                            outerRadius={68}
                            paddingAngle={3}
                          >
                            {dashboardData.categoryBreakdown.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={PIE_COLORS[index % PIE_COLORS.length]}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const item = payload[0].payload;
                                return (
                                  <div className="rounded-xl border border-slate-800 bg-slate-950/95 p-2.5 text-xs shadow-xl">
                                    <p className="font-semibold text-white">{item.name}</p>
                                    <p className="text-cyan-400 font-mono">
                                      ${Number(item.value).toLocaleString()} ({item.percentage}%)
                                    </p>
                                    <p className="text-slate-400 text-[10px]">{item.count} items</p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="max-h-28 overflow-y-auto space-y-1 pr-1">
                      {dashboardData.categoryBreakdown.slice(0, 5).map((cat, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[11px]">
                          <span className="flex items-center gap-1.5 text-slate-300 truncate max-w-[130px]">
                            <span
                              className="h-2 w-2 rounded-full shrink-0"
                              style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                            />
                            {cat.name}
                          </span>
                          <span className="font-mono text-slate-400 font-medium">{cat.percentage}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Country Distribution & Records Preview */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Geographic Ranking */}
              <div className="rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Globe className="h-4 w-4 text-emerald-400" />
                    Geographic Distribution
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {dashboardData.countryBreakdown.length} Countries
                  </span>
                </div>

                {dashboardData.countryBreakdown.length === 0 ? (
                  <div className="h-48 flex items-center justify-center text-xs text-slate-500">
                    No country column detected.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {dashboardData.countryBreakdown.slice(0, 6).map((ct, idx) => (
                      <div key={idx} className="space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-200">{ct.name}</span>
                          <span className="font-mono text-cyan-400">
                            ${ct.value.toLocaleString()} ({ct.percentage}%)
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-400 rounded-full"
                            style={{ width: `${Math.min(100, ct.percentage * 1.5)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Real Record Inspection Drawer / Mini-Table */}
              <div className="lg:col-span-2 rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <BarChart3 className="h-4 w-4 text-indigo-400" />
                      Live Verified Records Sample
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Grounded records from backend MySQL dataset storage
                    </p>
                  </div>
                  <Link href="/upload">
                    <Button size="sm" variant="outline" className="text-xs h-7">
                      View Full Preview →
                    </Button>
                  </Link>
                </div>

                {previewLoading ? (
                  <div className="h-48 flex items-center justify-center text-xs text-slate-400 gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-indigo-400" />
                    Loading records...
                  </div>
                ) : !previewData || previewData.rows.length === 0 ? (
                  <div className="h-48 flex items-center justify-center text-xs text-slate-500">
                    No records available.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px]">
                        <tr>
                          {previewData.columns.slice(0, 6).map((c, idx) => (
                            <th key={idx} className="p-2 font-semibold whitespace-nowrap">
                              {c.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {previewData.rows.slice(0, 5).map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-800/40">
                            {previewData.columns.slice(0, 6).map((c, cIdx) => (
                              <td key={cIdx} className="p-2 whitespace-nowrap">
                                {typeof row[c.name] === "number"
                                  ? row[c.name].toLocaleString()
                                  : String(row[c.name] ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Anomaly Alert Center & Data Quality Summary */}
            {businessAnalysis && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left: Anomaly Alert Center */}
                <div className="rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div>
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-rose-400" />
                        Statistical Anomaly & Event Detection Center
                      </h3>
                      <p className="text-[11px] text-slate-400">
                        Evaluates Tukey IQR fences, Gaussian Z-scores, and temporal volume shifts
                      </p>
                    </div>
                    <Badge variant={businessAnalysis.anomalies.criticalCount > 0 ? "danger" : "success"} size="sm">
                      {businessAnalysis.anomalies.totalAnomalies} Patterns Audited
                    </Badge>
                  </div>

                  {/* Anomaly Filter Tabs */}
                  <div className="flex items-center gap-2 text-xs">
                    {(["all", "critical", "warning", "info"] as const).map((sev) => {
                      const count =
                        sev === "all"
                          ? businessAnalysis.anomalies.totalAnomalies
                          : sev === "critical"
                          ? businessAnalysis.anomalies.criticalCount
                          : sev === "warning"
                          ? businessAnalysis.anomalies.warningCount
                          : businessAnalysis.anomalies.infoCount;
                      return (
                        <button
                          key={sev}
                          onClick={() => setAnomalySeverityFilter(sev)}
                          className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                            anomalySeverityFilter === sev
                              ? "bg-slate-800 text-white border border-slate-700"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          {sev.toUpperCase()} ({count})
                        </button>
                      );
                    })}
                  </div>

                  {/* Anomaly Items List */}
                  {businessAnalysis.anomalies.anomalies.length === 0 ? (
                    <div className="h-32 flex items-center justify-center text-xs text-slate-500">
                      Zero statistical anomalies detected across all records.
                    </div>
                  ) : (
                    <div className="max-h-80 overflow-y-auto space-y-2.5 pr-1">
                      {businessAnalysis.anomalies.anomalies
                        .filter(
                          (a) => anomalySeverityFilter === "all" || a.severity === anomalySeverityFilter
                        )
                        .map((anom) => (
                          <div
                            key={anom.anomalyId}
                            className={`rounded-xl border p-3 text-xs space-y-1.5 ${
                              anom.severity === "critical"
                                ? "border-rose-500/30 bg-rose-500/5 text-rose-200"
                                : anom.severity === "warning"
                                ? "border-amber-500/30 bg-amber-500/5 text-amber-200"
                                : "border-cyan-500/30 bg-cyan-500/5 text-cyan-200"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-white">{anom.title}</span>
                              <div className="flex items-center gap-1.5">
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                    anom.severity === "critical"
                                      ? "bg-rose-500/20 text-rose-400"
                                      : anom.severity === "warning"
                                      ? "bg-amber-500/20 text-amber-400"
                                      : "bg-cyan-500/20 text-cyan-400"
                                  }`}
                                >
                                  {anom.severity}
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">
                                  {anom.affectedRecordsCount} rows
                                </span>
                              </div>
                            </div>
                            <p className="text-[11px] text-slate-300 leading-normal">{anom.description}</p>
                            <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1 border-t border-white/[0.04]">
                              <span>Method: {anom.statisticalMethod}</span>
                              <span className={anom.isConfirmedBusinessProblem ? "text-rose-400 font-semibold" : "text-slate-400"}>
                                {anom.isConfirmedBusinessProblem ? "Confirmed Business Event" : "Statistical Outlier"}
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>

                {/* Right: Data Quality & Hygiene Center */}
                <div className="rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div>
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        Data Quality & Hygiene Audit
                      </h3>
                      <p className="text-[11px] text-slate-400">
                        Completeness, uniqueness, and non-destructive transformation preview
                      </p>
                    </div>
                    <Badge variant={businessAnalysis.quality.cleanlinessStatus === "healthy" ? "success" : "warning"} size="sm">
                      {businessAnalysis.quality.qualityScore.toFixed(1)}/100 Quality
                    </Badge>
                  </div>

                  {/* 4 Metric Tiles */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-1">
                      <span className="text-slate-400 text-[11px]">Missing Cells</span>
                      <p className="text-lg font-bold font-mono text-white">
                        {businessAnalysis.quality.missingCells.toLocaleString()} ({businessAnalysis.quality.missingCellRate}%)
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-1">
                      <span className="text-slate-400 text-[11px]">Duplicate Rows</span>
                      <p className="text-lg font-bold font-mono text-white">
                        {businessAnalysis.quality.duplicateRows.toLocaleString()} ({businessAnalysis.quality.duplicateRate}%)
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-1">
                      <span className="text-slate-400 text-[11px]">Invalid Dates</span>
                      <p className="text-lg font-bold font-mono text-white">
                        {businessAnalysis.quality.invalidDateCount.toLocaleString()}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-1">
                      <span className="text-slate-400 text-[11px]">Inconsistent Text Casing</span>
                      <p className="text-lg font-bold font-mono text-white">
                        {businessAnalysis.quality.inconsistentCategoryCount.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Suggested Cleaning Operations */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-300">
                      Suggested Non-Destructive Cleaning Operations ({businessAnalysis.quality.suggestedOperations.length})
                    </span>
                    {businessAnalysis.quality.suggestedOperations.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No automated cleaning transformations required. Data is clean.</p>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {businessAnalysis.quality.suggestedOperations.map((op) => (
                          <div
                            key={op.ruleId}
                            className="rounded-lg border border-slate-800 bg-slate-950/70 p-2.5 text-xs flex items-center justify-between"
                          >
                            <div className="space-y-0.5">
                              <span className="font-semibold text-slate-200">{op.ruleName}</span>
                              <p className="text-[11px] text-slate-400">{op.description}</p>
                            </div>
                            <span className="text-[10px] font-mono text-indigo-400 shrink-0 ml-2">
                              {op.affectedRows.toLocaleString()} rows
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Strategic Action Recommendations */}
                  {businessAnalysis.recommendations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800 space-y-1.5">
                      <span className="text-xs font-semibold text-cyan-300 flex items-center gap-1.5">
                        <Lightbulb className="h-3.5 w-3.5 text-cyan-400" />
                        Strategic Next Actions Formulated By Agent:
                      </span>
                      <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-1 pl-1">
                        {businessAnalysis.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Grounded Natural Language Analytics Q&A Box */}
            <div className="rounded-2xl border border-white/[0.08] bg-slate-900/90 p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Ask AI Business Analyst Grounded In Current Dataset
                  </h3>
                </div>
                <Link href="/agents">
                  <span className="text-xs text-indigo-400 hover:underline">
                    Open Full Multi-Agent Swarm →
                  </span>
                </Link>
              </div>

              {/* Chat Transcript */}
              {chatMessages.length > 0 && (
                <div className="max-h-60 overflow-y-auto space-y-3 pr-2">
                  {chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`rounded-xl p-3 text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-slate-800/70 text-white ml-8"
                          : "bg-slate-950/80 border border-slate-800 text-slate-200 mr-8"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                        <span className="font-semibold">{msg.sender === "user" ? "You" : "Business Analyst Agent"}</span>
                        {msg.latency && <span className="font-mono">{msg.latency}ms</span>}
                      </div>
                      <p className="whitespace-pre-line">{msg.text}</p>
                    </div>
                  ))}
                  <div ref={chatScrollRef} />
                </div>
              )}

              {/* Chat Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAskQuestion();
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={`Ask a question about ${activeDatasetObj?.name || "this dataset"} (e.g. 'What is the UK revenue and top product?')...`}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isAsking || !chatInput.trim()}
                  className="text-xs px-4"
                >
                  {isAsking ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  <span className="ml-1 hidden sm:inline">Ask</span>
                </Button>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
