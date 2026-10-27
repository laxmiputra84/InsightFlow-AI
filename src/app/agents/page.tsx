"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bot,
  Play,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  Activity,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  Server,
  RefreshCw,
  Database,
  FileSpreadsheet,
  Check,
  ChevronRight,
  HelpCircle,
  Sparkle,
  FileSearch,
  Sparkles as CleaningIcon,
  LayoutDashboard,
  Calendar,
  X,
  Sliders,
  AlertTriangle,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { InsightFlowApi } from "@/services/api";
import {
  DatasetItem,
  DatasetAgentTaskResponse,
  DatasetSixAgentWorkflowResponse,
  CleaningPreviewResponse,
  BackendStatus,
} from "@/types";

interface AgentDisplayCard {
  id: string;
  name: string;
  role: string;
  description: string;
  iconName: string;
  status: "idle" | "running" | "completed" | "error";
  lastRun?: DatasetAgentTaskResponse;
}

export default function AgentsPage() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [isLoadingDatasets, setIsLoadingDatasets] = useState<boolean>(true);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    connected: false,
    checkedAt: "Checking...",
  });

  const [pipelineState, setPipelineState] = useState<"idle" | "running" | "completed">("idle");
  const [runningAgentId, setRunningAgentId] = useState<string | null>(null);
  const [workflowResult, setWorkflowResult] = useState<DatasetSixAgentWorkflowResponse | null>(null);
  const [swarmQuery, setSwarmQuery] = useState("");

  // Cleaning Preview Modal State
  const [isCleaningModalOpen, setIsCleaningModalOpen] = useState(false);
  const [cleaningPreview, setCleaningPreview] = useState<CleaningPreviewResponse | null>(null);
  const [isCleaningLoading, setIsCleaningLoading] = useState(false);
  const [isApplyingCleaning, setIsApplyingCleaning] = useState(false);
  const [cleaningSuccessMsg, setCleaningSuccessMsg] = useState<string | null>(null);

  const [agentCards, setAgentCards] = useState<AgentDisplayCard[]>([
    {
      id: "agent-understanding",
      name: "Data Understanding Agent",
      role: "Schema & Semantic Role Discovery",
      description:
        "Inspects structural properties, verifies data types, evaluates missingness ratios, cardinality, and infers business column roles.",
      iconName: "FileSearch",
      status: "idle",
    },
    {
      id: "agent-cleaning",
      name: "Data Cleaning Agent",
      role: "Hygiene Auditing & Safe Staging",
      description:
        "Identifies whitespace pollution, duplicate rows, missing entries, and generates a non-destructive transformation preview requiring explicit user approval.",
      iconName: "CleaningIcon",
      status: "idle",
    },
    {
      id: "agent-analyst",
      name: "Business Analyst Agent",
      role: "Core Performance & EDA Analytics",
      description:
        "Computes verified KPIs (Revenue, AOV, Orders), category leaders, and segment distributions with grounded numeric citations.",
      iconName: "TrendingUp",
      status: "idle",
    },
    {
      id: "agent-quality",
      name: "Anomaly & Data Quality Agent",
      role: "Statistical Outliers & Event Segregation",
      description:
        "Computes Data Hygiene score, evaluates Tukey IQR fences, and segregates return/cancellation transactions from data entry corruption.",
      iconName: "ShieldAlert",
      status: "idle",
    },
    {
      id: "agent-forecaster",
      name: "Forecasting Agent",
      role: "Holdout ML Models & Horizon Projection",
      description:
        "Validates chronological eligibility (≥14 days), evaluates Exponential Smoothing and Linear Trend against a Naive Baseline, reporting RMSE and MAPE.",
      iconName: "Bot",
      status: "idle",
    },
    {
      id: "agent-dashboard",
      name: "Dashboard & Recommendations Agent",
      role: "Layout Synthesis & Strategic Guidance",
      description:
        "Synthesizes multi-agent findings, recommends optimal dashboard widgets based on schema dimensions, and formulates evidence-grounded directives.",
      iconName: "LayoutDashboard",
      status: "idle",
    },
  ]);

  const [logs, setLogs] = useState<
    { id: string; timestamp: string; agentName: string; level: "info" | "success" | "warn" | "error"; message: string }[]
  >([
    {
      id: "init",
      timestamp: new Date().toLocaleTimeString(),
      agentName: "Orchestrator",
      level: "info",
      message: "LangGraph 6-Agent Dataset-Driven BI System ready. Select an active dataset to execute workflows.",
    },
  ]);

  useEffect(() => {
    initPage();
  }, []);

  const initPage = async () => {
    setIsLoadingDatasets(true);
    const health = await InsightFlowApi.checkHealth();
    setBackendStatus(health);

    try {
      const res = await InsightFlowApi.getDatasets();
      if (res.data && res.data.length > 0) {
        setDatasets(res.data);
        const active = res.data.find((d) => d.isActive) || res.data[0];
        setSelectedDatasetId(active.id);
        addLog("Orchestrator", "info", `Loaded active dataset '${active.name}' (${active.rowCount.toLocaleString()} records).`);
      } else {
        setDatasets([]);
        setSelectedDatasetId("");
        addLog("Orchestrator", "warn", "No dataset found. Upload a business dataset to run multi-agent workflows.");
      }
    } catch (err: any) {
      addLog("Orchestrator", "error", `Failed to load datasets: ${err?.message}`);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const addLog = (agentName: string, level: "info" | "success" | "warn" | "error", message: string) => {
    setLogs((prev) => [
      {
        id: `log-${Date.now()}-${Math.random()}`,
        timestamp: new Date().toLocaleTimeString(),
        agentName,
        level,
        message,
      },
      ...prev.slice(0, 50),
    ]);
  };

  // Run single agent
  const handleRunSingleAgent = async (agentId: string) => {
    if (!selectedDatasetId) {
      addLog("Orchestrator", "warn", "Please select a dataset first.");
      return;
    }

    setRunningAgentId(agentId);
    setAgentCards((prev) =>
      prev.map((c) => (c.id === agentId ? { ...c, status: "running" } : c))
    );

    const targetAgent = agentCards.find((c) => c.id === agentId);
    addLog(targetAgent?.name || agentId, "info", `Dispatching single-agent execution on dataset '${selectedDatasetId}'...`);

    try {
      const res = await InsightFlowApi.runDatasetAgent(selectedDatasetId, agentId, swarmQuery || undefined);
      if (res.data) {
        const taskRes = res.data;
        setAgentCards((prev) =>
          prev.map((c) =>
            c.id === agentId ? { ...c, status: "completed", lastRun: taskRes } : c
          )
        );
        addLog(
          taskRes.agentName,
          "success",
          `Execution completed in ${taskRes.executionTimeMs}ms with ${taskRes.findings.length} verifiable findings.`
        );
      } else {
        setAgentCards((prev) =>
          prev.map((c) => (c.id === agentId ? { ...c, status: "error" } : c))
        );
        addLog(targetAgent?.name || agentId, "error", res.error || "Agent execution failed.");
      }
    } catch (err: any) {
      setAgentCards((prev) =>
        prev.map((c) => (c.id === agentId ? { ...c, status: "error" } : c))
      );
      addLog(targetAgent?.name || agentId, "error", err?.message || "Execution exception.");
    } finally {
      setRunningAgentId(null);
    }
  };

  // Run full 6-agent LangGraph workflow
  const handleRunFullWorkflow = async () => {
    if (!selectedDatasetId) {
      addLog("Orchestrator", "warn", "No dataset selected for 6-agent LangGraph workflow.");
      return;
    }

    setPipelineState("running");
    setWorkflowResult(null);
    setAgentCards((prev) => prev.map((c) => ({ ...c, status: "running" })));
    addLog("Orchestrator", "info", `Dispatching LangGraph 6-Agent BI Pipeline on dataset '${selectedDatasetId}'...`);

    try {
      const res = await InsightFlowApi.runDatasetWorkflow(selectedDatasetId, swarmQuery || undefined);
      if (res.data) {
        const data = res.data;
        setWorkflowResult(data);
        setPipelineState("completed");

        setAgentCards((prev) =>
          prev.map((c) => {
            if (c.id === "agent-understanding") return { ...c, status: "completed", lastRun: data.understandingAgent };
            if (c.id === "agent-cleaning") return { ...c, status: "completed", lastRun: data.cleaningAgent };
            if (c.id === "agent-analyst") return { ...c, status: "completed", lastRun: data.businessAgent };
            if (c.id === "agent-quality") return { ...c, status: "completed", lastRun: data.anomalyAgent };
            if (c.id === "agent-forecaster") return { ...c, status: "completed", lastRun: data.forecastingAgent };
            if (c.id === "agent-dashboard") return { ...c, status: "completed", lastRun: data.dashboardAgent };
            return c;
          })
        );

        addLog("Orchestrator", "success", `LangGraph 6-Agent workflow completed successfully in ${data.executionTimeMs}ms.`);
        addLog("Data Understanding", "info", `Understood schema & column roles.`);
        addLog("Data Cleaning", "info", `Evaluated hygiene; safe preview prepared.`);
        addLog("Business Analyst", "info", `Computed verified revenue & AOV.`);
        addLog("Quality Analyst", "info", `Audited Tukey IQR outlier fences.`);
        addLog("Forecasting Agent", "info", `Calibrated out-of-sample models.`);
        addLog("Dashboard Agent", "info", `Synthesized UI widget layouts & recommendations.`);
      } else {
        setPipelineState("idle");
        setAgentCards((prev) => prev.map((c) => ({ ...c, status: "error" })));
        addLog("Orchestrator", "error", res.error || "6-Agent workflow execution failed.");
      }
    } catch (err: any) {
      setPipelineState("idle");
      setAgentCards((prev) => prev.map((c) => ({ ...c, status: "error" })));
      addLog("Orchestrator", "error", err?.message || "Workflow execution exception.");
    }
  };

  // Open Data Cleaning Modal and fetch preview
  const handleOpenCleaningModal = async () => {
    if (!selectedDatasetId) return;
    setIsCleaningModalOpen(true);
    setIsCleaningLoading(true);
    setCleaningSuccessMsg(null);

    try {
      const res = await InsightFlowApi.getDatasetCleaningPreview(selectedDatasetId);
      if (res.data) {
        setCleaningPreview(res.data);
      } else {
        addLog("Data Cleaning Agent", "error", res.error || "Failed to load cleaning preview.");
      }
    } catch (err: any) {
      addLog("Data Cleaning Agent", "error", err?.message || "Error loading cleaning preview.");
    } finally {
      setIsCleaningLoading(false);
    }
  };

  // Approve and Apply Cleaning Transformations
  const handleApproveCleaning = async () => {
    if (!selectedDatasetId || !cleaningPreview) return;
    setIsApplyingCleaning(true);
    setCleaningSuccessMsg(null);

    try {
      const approvedIds = cleaningPreview.proposedRules.map((r) => r.ruleId);
      const res = await InsightFlowApi.applyDatasetCleaningPlan(
        selectedDatasetId,
        approvedIds,
        `${cleaningPreview.datasetName} (Cleaned)`,
        true
      );

      if (res.data) {
        setCleaningSuccessMsg(
          `Success: Created and activated promoted cleaned dataset '${res.data.cleanedDatasetName}' (${res.data.rowsRetained.toLocaleString()} rows retained, ${res.data.rowsRemoved.toLocaleString()} removed).`
        );
        addLog(
          "Data Cleaning Agent",
          "success",
          `Promoted cleaned dataset '${res.data.cleanedDatasetName}'. Original raw dataset preserved unchanged.`
        );
        // Refresh dataset list
        await initPage();
      } else {
        addLog("Data Cleaning Agent", "error", res.error || "Failed to apply cleaning transformations.");
      }
    } catch (err: any) {
      addLog("Data Cleaning Agent", "error", err?.message || "Cleaning approval failed.");
    } finally {
      setIsApplyingCleaning(false);
    }
  };

  const activeDatasetObj = datasets.find((d) => d.id === selectedDatasetId);

  const getAgentIcon = (iconName: string) => {
    switch (iconName) {
      case "FileSearch":
        return <FileSearch className="h-5 w-5 text-blue-400" />;
      case "CleaningIcon":
        return <CleaningIcon className="h-5 w-5 text-emerald-400" />;
      case "TrendingUp":
        return <TrendingUp className="h-5 w-5 text-indigo-400" />;
      case "ShieldAlert":
        return <ShieldAlert className="h-5 w-5 text-pink-400" />;
      case "Bot":
        return <Bot className="h-5 w-5 text-cyan-400" />;
      case "LayoutDashboard":
        return <LayoutDashboard className="h-5 w-5 text-purple-400" />;
      default:
        return <Bot className="h-5 w-5 text-indigo-400" />;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <Bot className="h-5 w-5 text-indigo-400" />
                Six-Agent Dataset-Driven BI Workflow
              </h1>
              <Badge variant="purple" size="sm">
                LangGraph Orchestrated
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Autonomous empirical intelligence engine executing data understanding, safe cleaning preview, business KPIs, quality audits, holdout forecasting, and dashboard layout synthesis.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {activeDatasetObj && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleOpenCleaningModal}
                className="gap-2 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10"
              >
                <CleaningIcon className="h-3.5 w-3.5 text-emerald-400" />
                Preview & Apply Data Cleaning
              </Button>
            )}

            {pipelineState === "running" ? (
              <Button size="sm" variant="secondary" disabled className="gap-2">
                <RefreshCw className="h-4 w-4 animate-spin text-indigo-400" />
                Workflow Executing...
              </Button>
            ) : (
              <Button
                size="sm"
                variant="primary"
                onClick={handleRunFullWorkflow}
                disabled={!selectedDatasetId || runningAgentId !== null}
                className="gap-2"
              >
                <Play className="h-3.5 w-3.5" />
                Run 6-Agent LangGraph Workflow
              </Button>
            )}

            {pipelineState === "completed" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setPipelineState("idle");
                  setWorkflowResult(null);
                  setAgentCards((prev) => prev.map((c) => ({ ...c, status: "idle", lastRun: undefined })));
                }}
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Dataset Selection Bar or Truthful Empty State */}
        {datasets.length === 0 && !isLoadingDatasets ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Database className="h-7 w-7" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">No Dataset Available</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                The 6-agent Agentic BI workflow operates directly on verified business data. Upload a CSV or Excel dataset to activate the pipeline.
              </p>
            </div>
            <Link href="/upload">
              <Button variant="primary" size="sm" className="gap-2 mt-2">
                <FileSpreadsheet className="h-4 w-4" />
                Upload New Dataset
              </Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-slate-800 bg-slate-900/70 text-xs">
            <div className="flex items-center gap-2.5">
              <Database className="h-4 w-4 text-indigo-400" />
              <span className="font-semibold text-white">Active Dataset:</span>
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
              >
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name} ({ds.rowCount.toLocaleString()} rows) {ds.isActive ? "★ Active" : ""}
                  </option>
                ))}
              </select>
            </div>

            {activeDatasetObj && (
              <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                <span>Rows: <strong className="text-white">{activeDatasetObj.rowCount.toLocaleString()}</strong></span>
                <span>•</span>
                <span>Cols: <strong className="text-white">{activeDatasetObj.columnCount}</strong></span>
                <span>•</span>
                <span>Quality: <strong className="text-emerald-400">{activeDatasetObj.qualityScore.toFixed(1)}%</strong></span>
                <Link href="/upload" className="text-indigo-400 hover:underline font-sans ml-2">
                  Manage Datasets →
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Optional Query Input */}
        {datasets.length > 0 && (
          <div className="flex gap-2">
            <input
              type="text"
              value={swarmQuery}
              onChange={(e) => setSwarmQuery(e.target.value)}
              placeholder="Analytical query (e.g. 'Investigate customer retention and category sales' or leave blank for full automated audit)"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>
        )}

        {/* Combined Executive Brief (When 6-Agent Workflow Completes) */}
        {workflowResult && (
          <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">
                  LangGraph 6-Agent Synthesis Brief: {workflowResult.datasetName}
                </h3>
              </div>
              <Badge variant="purple" size="sm">
                Executed in {workflowResult.executionTimeMs}ms
              </Badge>
            </div>

            <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line font-sans">
              {workflowResult.executiveSummary}
            </div>

            {/* Strategic Recommendations Banner */}
            {workflowResult.recommendations && workflowResult.recommendations.length > 0 && (
              <div className="pt-3 border-t border-indigo-500/20 space-y-2">
                <span className="text-[11px] uppercase font-bold text-emerald-400 tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" />
                  Evidence-Grounded Strategic Recommendations:
                </span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {workflowResult.recommendations.map((rec, rIdx) => (
                    <div key={rIdx} className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-slate-300 flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">#{rIdx + 1}</span>
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* The 6 Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {agentCards.map((agent) => {
            const isRunning = runningAgentId === agent.id || pipelineState === "running";
            const lastRun = agent.lastRun;

            return (
              <div
                key={agent.id}
                className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all"
              >
                <div className="space-y-3">
                  {/* Top Bar */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-2.5">
                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 shrink-0 mt-0.5">
                        {getAgentIcon(agent.iconName)}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">{agent.name}</h3>
                        <p className="text-[11px] text-indigo-400 font-medium mt-0.5">{agent.role}</p>
                      </div>
                    </div>

                    <Badge
                      variant={
                        agent.status === "completed"
                          ? "success"
                          : agent.status === "running"
                          ? "purple"
                          : agent.status === "error"
                          ? "default"
                          : "default"
                      }
                      size="sm"
                    >
                      {agent.status.toUpperCase()}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed">{agent.description}</p>

                  {/* Findings / Output Panel if completed */}
                  {lastRun && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 space-y-2.5 text-xs">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono pb-1 border-b border-slate-800">
                        <span>Duration: {lastRun.executionTimeMs}ms</span>
                        <span>{lastRun.timestamp}</span>
                      </div>

                      {/* Input Summary */}
                      {lastRun.inputSummary && (
                        <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80 font-mono">
                          <span className="text-slate-500">Input:</span> {lastRun.inputSummary}
                        </div>
                      )}

                      {/* Verifiable Findings */}
                      <div className="space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                          Verifiable Findings:
                        </span>
                        {lastRun.findings.map((f, fIdx) => (
                          <div key={fIdx} className="flex items-start gap-2 text-slate-300 text-[11px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                            <span>{f}</span>
                          </div>
                        ))}
                      </div>

                      {/* Recommendations if present */}
                      {lastRun.recommendations && lastRun.recommendations.length > 0 && (
                        <div className="space-y-1 pt-1.5 border-t border-slate-800">
                          <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                            Recommendations:
                          </span>
                          {lastRun.recommendations.map((r, rIdx) => (
                            <div key={rIdx} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                              <span className="text-emerald-400">✓</span>
                              <span>{r}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Evidence Citations */}
                      {lastRun.citations && lastRun.citations.length > 0 && (
                        <div className="pt-1.5 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
                          <span>Evidence: {lastRun.citations.join(" | ")}</span>
                        </div>
                      )}

                      {/* Errors if any */}
                      {lastRun.errors && lastRun.errors.length > 0 && (
                        <div className="pt-1.5 border-t border-rose-500/20 text-[11px] text-rose-400">
                          Errors: {lastRun.errors.join("; ")}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Bottom Action */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isRunning || !selectedDatasetId}
                    onClick={() => handleRunSingleAgent(agent.id)}
                    className="w-full gap-2 text-xs"
                  >
                    {isRunning ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5" />
                        Execute Agent
                      </>
                    )}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live Execution Terminal Log */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-xl space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2 text-slate-300">
              <Terminal className="h-4 w-4 text-indigo-400" />
              <span className="font-semibold text-white">Agent Execution Stream & Telemetry</span>
            </div>
            <span className="text-[10px] text-slate-500">Live Agent Pipeline Audit Trail</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1.5 pr-2">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-2 text-[11px]">
                <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                <span
                  className={`font-semibold shrink-0 ${
                    log.level === "success"
                      ? "text-emerald-400"
                      : log.level === "error"
                      ? "text-rose-400"
                      : log.level === "warn"
                      ? "text-amber-400"
                      : "text-indigo-400"
                  }`}
                >
                  [{log.agentName}]:
                </span>
                <span className="text-slate-300">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Safe Data Cleaning Preview & Approval Modal */}
      {isCleaningModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <CleaningIcon className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">Safe Data Cleaning Preview & Approval</h2>
                  <p className="text-xs text-slate-400">
                    Non-destructive staging: Original raw data is permanently preserved. Transformations require explicit approval.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsCleaningModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            {isCleaningLoading ? (
              <div className="py-12 text-center space-y-3">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-emerald-400" />
                <p className="text-xs text-slate-400">Evaluating dataset hygiene and preparing transformation preview...</p>
              </div>
            ) : cleaningPreview ? (
              <div className="space-y-4">
                {/* Notice Alert */}
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-200 flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
                  <div>
                    <strong>Data Preservation Guarantee:</strong> Original uploaded dataset{" "}
                    <span className="font-mono text-white">'{cleaningPreview.datasetName}'</span> will remain 100% untouched. Promoting cleaned data creates an isolated version.
                  </div>
                </div>

                {/* Impact Metrics Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Original Rows</span>
                    <p className="text-base font-bold text-white mt-0.5">{cleaningPreview.totalOriginalRows.toLocaleString()}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Cleaned Rows</span>
                    <p className="text-base font-bold text-emerald-400 mt-0.5">{cleaningPreview.totalCleanedRows.toLocaleString()}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Duplicates Dropped</span>
                    <p className="text-base font-bold text-amber-400 mt-0.5">{cleaningPreview.duplicatesRemoved.toLocaleString()}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Imputed / Trimmed</span>
                    <p className="text-base font-bold text-indigo-400 mt-0.5">
                      {(cleaningPreview.missingCellsImputed + cleaningPreview.whitespaceTrimmedCells).toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Proposed Rules */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-white">Formulated Cleaning Rules</span>
                  <div className="space-y-1.5">
                    {cleaningPreview.proposedRules.map((r) => (
                      <div key={r.ruleId} className="flex items-center justify-between p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 text-xs">
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-emerald-400" />
                          <div>
                            <span className="font-semibold text-white">{r.ruleName}</span>
                            <p className="text-[11px] text-slate-400">{r.description}</p>
                          </div>
                        </div>
                        <Badge variant="info" size="sm">
                          {r.affectedRows.toLocaleString()} rows affected
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Before vs After Preview Sample */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-white">Sample Before vs After Comparison (First 2 Rows)</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] font-mono">
                    <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/80 space-y-1">
                      <span className="text-amber-400 font-bold font-sans">Raw Before:</span>
                      <pre className="text-slate-300 overflow-x-auto text-[10px]">
                        {JSON.stringify(cleaningPreview.beforeSample.slice(0, 2), null, 2)}
                      </pre>
                    </div>
                    <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/80 space-y-1">
                      <span className="text-emerald-400 font-bold font-sans">Cleaned After:</span>
                      <pre className="text-slate-300 overflow-x-auto text-[10px]">
                        {JSON.stringify(cleaningPreview.afterSample.slice(0, 2), null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>

                {cleaningSuccessMsg && (
                  <div className="p-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-xs text-emerald-300">
                    {cleaningSuccessMsg}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No cleaning preview available.</p>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCleaningModalOpen(false)}
              >
                Close
              </Button>
              {cleaningPreview && !cleaningSuccessMsg && (
                <Button
                  variant="primary"
                  size="sm"
                  disabled={isApplyingCleaning}
                  onClick={handleApproveCleaning}
                  className="gap-2 bg-emerald-600 hover:bg-emerald-500"
                >
                  {isApplyingCleaning ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Promoting Dataset...
                    </>
                  ) : (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      Approve & Promote Cleaned Dataset
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
