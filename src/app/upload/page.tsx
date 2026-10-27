"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  X,
  ArrowRight,
  Database,
  FileCheck,
  RefreshCw,
  Sparkles,
  Layers,
  Table as TableIcon,
  Trash2,
  Search,
  BookOpen,
  Send,
  HelpCircle,
  FileCode,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { InsightFlowApi } from "@/services/api";
import {
  DatasetItem,
  DatasetDetail,
  DatasetPreviewData,
  DocumentItem,
  CitationItem,
  RagAskResponse,
  RagHealthResponse,
} from "@/types";

export default function UploadPage() {
  // Navigation tabs: "datasets" (primary) or "rag" (unstructured documents)
  const [activeTab, setActiveTab] = useState<"datasets" | "rag">("datasets");

  // =========================================================================
  // Tab 1: Real Datasets State
  // =========================================================================
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [datasetDetail, setDatasetDetail] = useState<DatasetDetail | null>(null);
  const [previewData, setPreviewData] = useState<DatasetPreviewData | null>(null);
  const [previewPage, setPreviewPage] = useState(1);
  const [previewSearch, setPreviewSearch] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [datasetListLoading, setDatasetListLoading] = useState(false);

  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const datasetFileInputRef = useRef<HTMLInputElement>(null);

  // Global messages
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // =========================================================================
  // Tab 2: RAG Documents State
  // =========================================================================
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [ragHealth, setRagHealth] = useState<RagHealthResponse | null>(null);
  const [ragQuery, setRagQuery] = useState("");
  const [isAskingRag, setIsAskingRag] = useState(false);
  const [ragResult, setRagResult] = useState<RagAskResponse | null>(null);
  const [ragError, setRagError] = useState<string | null>(null);
  const [expandedSnippets, setExpandedSnippets] = useState<Record<number, boolean>>({});
  const docFileInputRef = useRef<HTMLInputElement>(null);

  // Load datasets and active dataset on mount
  useEffect(() => {
    loadDatasets();
    fetchDocumentsAndHealth();
  }, []);

  // When selectedDatasetId changes, load details and preview
  useEffect(() => {
    if (selectedDatasetId) {
      loadDatasetDetails(selectedDatasetId);
      loadDatasetPreview(selectedDatasetId, 1, previewSearch);
    } else {
      setDatasetDetail(null);
      setPreviewData(null);
    }
  }, [selectedDatasetId]);

  const loadDatasets = async () => {
    setDatasetListLoading(true);
    try {
      const res = await InsightFlowApi.getDatasets();
      if (res.data) {
        setDatasets(res.data);
        // Find active dataset or pick first
        const active = res.data.find((d) => d.isActive);
        if (active) {
          setSelectedDatasetId(active.id);
        } else if (res.data.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(res.data[0].id);
        }
      }
    } catch (err: any) {
      console.error("Failed to load datasets:", err);
    } finally {
      setDatasetListLoading(false);
    }
  };

  const loadDatasetDetails = async (id: string) => {
    try {
      const res = await InsightFlowApi.getDatasetDetail(id);
      if (res.data) {
        setDatasetDetail(res.data);
      }
    } catch (err: any) {
      console.error("Failed to fetch dataset details:", err);
    }
  };

  const loadDatasetPreview = async (id: string, page: number, search: string) => {
    setPreviewLoading(true);
    try {
      const res = await InsightFlowApi.getDatasetPreview(id, page, 15, search);
      if (res.data) {
        setPreviewData(res.data);
        setPreviewPage(page);
      }
    } catch (err: any) {
      console.error("Failed to fetch dataset preview:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Deletion modal state
  const [datasetPendingDelete, setDatasetPendingDelete] = useState<DatasetItem | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const handleActivateDataset = async (id: string) => {
    try {
      const res = await InsightFlowApi.activateDataset(id);
      if (res.data) {
        setSuccessMessage("Dataset activated! Dashboard is now powered by this dataset.");
        await loadDatasets();
      } else {
        setErrorMessage(res.error || "Failed to activate dataset.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to activate dataset.");
    }
  };

  const handleExecuteDelete = async (ds: DatasetItem) => {
    setIsDeleting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await InsightFlowApi.deleteDataset(ds.id);
      if (res.data) {
        // 4. Remove dataset from Available Datasets list immediately
        const remaining = datasets.filter((d) => d.id !== ds.id);
        setDatasets(remaining);

        // 5. If deleted dataset was active or selected, auto-select remaining or empty state
        const wasActive = ds.isActive || selectedDatasetId === ds.id;
        const nextId = res.data.nextActiveDatasetId;

        if (nextId && remaining.some((d) => d.id === nextId)) {
          setSelectedDatasetId(nextId);
          setDatasets((prev) =>
            prev.map((d) =>
              d.id === nextId ? { ...d, isActive: true } : { ...d, isActive: false }
            )
          );
        } else if (remaining.length > 0) {
          const fallbackNext = remaining[0];
          setSelectedDatasetId(fallbackNext.id);
          await InsightFlowApi.activateDataset(fallbackNext.id);
          setDatasets((prev) =>
            prev.map((d) =>
              d.id === fallbackNext.id ? { ...d, isActive: true } : { ...d, isActive: false }
            )
          );
        } else {
          // No datasets remain: reset state to empty
          setSelectedDatasetId(null);
          setDatasetDetail(null);
          setPreviewData(null);
        }

        setSuccessMessage(
          `Dataset '${ds.name}' and all associated records were permanently deleted.`
        );
        setDatasetPendingDelete(null);
      } else {
        // 10. Deletion failed: retain the dataset card and display a meaningful error
        setErrorMessage(
          res.error || `Failed to delete dataset '${ds.name}'. The dataset was retained.`
        );
        setDatasetPendingDelete(null);
      }
    } catch (err: any) {
      setErrorMessage(
        err?.message || `An error occurred while deleting dataset '${ds.name}'. The dataset was retained.`
      );
      setDatasetPendingDelete(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // Upload handler for CSV/Excel
  const handleDatasetFileSelected = async (file: File) => {
    const validExtensions = [".csv", ".xlsx", ".xls"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setErrorMessage(`Unsupported dataset format '${ext}'. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage("File exceeds 50MB maximum dataset limit.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      setUploadProgress(50);
      const res = await InsightFlowApi.uploadDataset(file);
      setUploadProgress(100);

      if (res.data) {
        setSuccessMessage(`Dataset '${res.data.name}' successfully parsed with ${res.data.rowCount.toLocaleString()} rows and ${res.data.columnCount} columns!`);
        await loadDatasets();
        setSelectedDatasetId(res.data.id);
      } else {
        setErrorMessage(res.error || "Dataset processing failed.");
      }
    } catch (err: any) {
      setErrorMessage(err?.message || "Dataset upload failed.");
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (datasetFileInputRef.current) datasetFileInputRef.current.value = "";
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleDatasetFileSelected(e.dataTransfer.files[0]);
    }
  };

  // RAG Document Fetcher
  const fetchDocumentsAndHealth = async () => {
    setLoadingDocs(true);
    try {
      const [docsResp, healthResp] = await Promise.all([
        InsightFlowApi.listDocuments(),
        InsightFlowApi.getRagHealth(),
      ]);
      setDocuments(docsResp.data?.documents || []);
      setRagHealth(healthResp.data || null);
    } catch (err: any) {
      console.warn("RAG fetch error:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleAskRag = async (e?: React.FormEvent, customQuestion?: string) => {
    if (e) e.preventDefault();
    const queryToAsk = (customQuestion || ragQuery).trim();
    if (!queryToAsk || isAskingRag) return;

    setIsAskingRag(true);
    setRagError(null);
    setRagResult(null);

    try {
      const result = await InsightFlowApi.askRag(queryToAsk, { topK: 4 });
      if (result.data) {
        setRagResult(result.data);
      } else {
        setRagError(result.error || "Failed to retrieve evidence and generate answer.");
      }
    } catch (err: any) {
      setRagError(err.message || "Failed to retrieve evidence and generate answer.");
    } finally {
      setIsAskingRag(false);
    }
  };

  const toggleSnippet = (index: number) => {
    setExpandedSnippets((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-indigo-400" />
                Real Dataset Upload & Processing
              </h1>
              <Badge variant="purple" size="sm">
                Multi-Format
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Upload real CSV or Excel datasets to drive dynamic dashboard KPIs, automated quality audits, and multi-agent reasoning.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/">
              <Button size="sm" variant="outline" className="gap-2">
                <ArrowRight className="h-3.5 w-3.5" />
                Go to Dashboard
              </Button>
            </Link>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                loadDatasets();
                fetchDocumentsAndHealth();
              }}
              disabled={datasetListLoading || loadingDocs}
              title="Refresh"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${datasetListLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* Global Notifications */}
        {errorMessage && (
          <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
            <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400" />
            <span className="flex-1 font-medium">{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
            <span className="flex-1 font-medium">{successMessage}</span>
            <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800">
          <button
            onClick={() => setActiveTab("datasets")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "datasets"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileSpreadsheet className="h-4 w-4" />
            Tabular Datasets (CSV & Excel)
            {datasets.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300 font-mono">
                {datasets.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("rag")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "rag"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <BookOpen className="h-4 w-4" />
            Document Ingestion & RAG Assistant
            {documents.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                {documents.length}
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: Real Datasets Engine */}
        {activeTab === "datasets" && (
          <div className="space-y-6">
            {/* Upload Drop Zone */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
                dragActive
                  ? "border-indigo-500 bg-indigo-500/10"
                  : "border-slate-800 bg-slate-900/60 hover:border-slate-700"
              }`}
            >
              <input
                ref={datasetFileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleDatasetFileSelected(e.target.files[0]);
                  }
                }}
                className="hidden"
                id="dataset-upload-input"
              />

              <div className="max-w-md mx-auto space-y-3">
                <div className="h-12 w-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400">
                  {isUploading ? (
                    <RefreshCw className="h-6 w-6 animate-spin" />
                  ) : (
                    <UploadCloud className="h-6 w-6" />
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-white">
                    {isUploading ? "Uploading & Analyzing Dataset..." : "Upload Business Dataset"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Drag and drop your <strong>.csv</strong>, <strong>.xlsx</strong>, or <strong>.xls</strong> dataset here, or browse from your computer (up to 50MB).
                  </p>
                </div>

                <div className="flex items-center justify-center gap-3 pt-2">
                  <Button
                    size="sm"
                    variant="primary"
                    disabled={isUploading}
                    onClick={() => datasetFileInputRef.current?.click()}
                    className="gap-2"
                  >
                    <FileSpreadsheet className="h-3.5 w-3.5" />
                    Browse Files
                  </Button>
                </div>

                <div className="pt-2 flex items-center justify-center gap-4 text-[11px] text-slate-500 font-mono">
                  <span>✓ UCI Online Retail Supported</span>
                  <span>•</span>
                  <span>✓ Auto-Schema Detection</span>
                  <span>•</span>
                  <span>✓ Quality Audit</span>
                </div>
              </div>
            </div>

            {/* Datasets List Grid */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Database className="h-4 w-4 text-indigo-400" />
                  Available Datasets ({datasets.length})
                </h3>
                <span className="text-[11px] text-slate-400">
                  Active dataset powers all dashboard metrics & agents
                </span>
              </div>

              {datasets.length === 0 ? (
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs text-slate-400">
                  No datasets uploaded yet. Upload a CSV or Excel file above to begin.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {datasets.map((ds) => {
                    const isSelected = selectedDatasetId === ds.id;
                    const isActive = ds.isActive;

                    return (
                      <div
                        key={ds.id}
                        onClick={() => setSelectedDatasetId(ds.id)}
                        className={`rounded-2xl border p-4 cursor-pointer transition-all relative ${
                          isSelected
                            ? "border-indigo-500 bg-indigo-500/10 shadow-lg"
                            : "border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-white truncate max-w-[170px]" title={ds.name}>
                                {ds.name}
                              </span>
                              {isActive && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                  ACTIVE
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 truncate max-w-[200px]" title={ds.filename}>
                              {ds.filename} ({formatFileSize(ds.fileSize)})
                            </p>
                          </div>

                          <Badge variant={ds.qualityScore >= 90 ? "success" : ds.qualityScore >= 75 ? "warning" : "default"} size="sm">
                            {ds.qualityScore.toFixed(1)}% Quality
                          </Badge>
                        </div>

                        {/* Specs */}
                        <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800/80 text-xs">
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase">Rows</span>
                            <p className="font-mono font-semibold text-slate-200">{ds.rowCount.toLocaleString()}</p>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase">Columns</span>
                            <p className="font-mono font-semibold text-slate-200">{ds.columnCount}</p>
                          </div>
                        </div>

                        {/* Role Tags */}
                        <div className="flex flex-wrap gap-1 mt-2.5">
                          {ds.detectedMappings.isOnlineRetail && (
                            <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[9px]">
                              Online Retail
                            </span>
                          )}
                          {ds.detectedMappings.dateColumn && (
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[9px]">
                              Date: {ds.detectedMappings.dateColumn}
                            </span>
                          )}
                          {ds.detectedMappings.amountColumn && (
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[9px]">
                              Rev: {ds.detectedMappings.amountColumn}
                            </span>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center justify-between gap-2 mt-4 pt-3 border-t border-slate-800/80">
                          {!isActive ? (
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleActivateDataset(ds.id);
                              }}
                              className="text-[11px] py-1 h-7"
                            >
                              Set as Active
                            </Button>
                          ) : (
                            <Link href="/" onClick={(e) => e.stopPropagation()}>
                              <Button size="sm" variant="outline" className="text-[11px] py-1 h-7 text-emerald-300 border-emerald-500/30">
                                View Dashboard →
                              </Button>
                            </Link>
                          )}

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setDatasetPendingDelete(ds);
                            }}
                            disabled={isDeleting && datasetPendingDelete?.id === ds.id}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            title="Delete dataset"
                          >
                            {isDeleting && datasetPendingDelete?.id === ds.id ? (
                              <RefreshCw className="h-3.5 w-3.5 animate-spin text-rose-400" />
                            ) : (
                              <Trash2 className="h-3.5 w-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Selected Dataset Inspection & Quality Audit */}
            {datasetDetail && (
              <div className="space-y-6 pt-4 border-t border-slate-800">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-base font-semibold text-white flex items-center gap-2">
                      <ShieldCheck className="h-5 w-5 text-indigo-400" />
                      Dataset Schema & Quality Audit: {datasetDetail.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Uploaded {datasetDetail.createdAt} • Detected schema mappings and Tukey IQR data quality report
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {!datasetDetail.isActive && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleActivateDataset(datasetDetail.id)}
                        className="gap-1.5"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Activate on Dashboard
                      </Button>
                    )}
                  </div>
                </div>

                {/* Quality Metrics Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Quality Score</span>
                    <p className="text-2xl font-bold text-emerald-400 font-mono mt-1">
                      {datasetDetail.qualityReport.qualityScore.toFixed(1)}%
                    </p>
                    <span className="text-[10px] text-slate-500">Based on missing, duplicates & anomalies</span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Total Rows</span>
                    <p className="text-2xl font-bold text-white font-mono mt-1">
                      {datasetDetail.rowCount.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-slate-500">{datasetDetail.columnCount} columns detected</span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Missing Cells</span>
                    <p className="text-2xl font-bold text-amber-400 font-mono mt-1">
                      {datasetDetail.qualityReport.missingValuesTotal.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-slate-500">Across all records and fields</span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Duplicate Rows</span>
                    <p className="text-2xl font-bold text-slate-300 font-mono mt-1">
                      {datasetDetail.qualityReport.duplicateRowsCount.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-slate-500">Exact duplicate observations</span>
                  </div>
                </div>

                {/* Detected Issues Callout */}
                {datasetDetail.qualityReport.issues.length > 0 && (
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5 space-y-3">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <FileCheck className="h-4 w-4 text-indigo-400" />
                      Automated Quality & Integrity Findings:
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {datasetDetail.qualityReport.issues.map((issue, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2.5 p-3 rounded-xl border border-slate-800/80 bg-slate-900/50 text-xs"
                        >
                          <span
                            className={`h-2 w-2 rounded-full mt-1 shrink-0 ${
                              issue.type === "error"
                                ? "bg-rose-400"
                                : issue.type === "warning"
                                ? "bg-amber-400"
                                : "bg-cyan-400"
                            }`}
                          />
                          <div className="space-y-0.5">
                            <span className="font-semibold text-slate-200">
                              {issue.field ? `Field [${issue.field}]: ` : ""}
                              {issue.message}
                            </span>
                            {issue.affectedRows && (
                              <p className="text-[10px] text-slate-400 font-mono">
                                Affected records: {issue.affectedRows.toLocaleString()}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Schema Structure Table */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-lg overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <Layers className="h-4 w-4 text-indigo-400" />
                      <h4 className="text-sm font-semibold text-white">Detected Column Schema</h4>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      {datasetDetail.columnsSchema.length} Columns Analyzed
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[11px]">
                        <tr>
                          <th className="p-3 font-semibold">Column Name</th>
                          <th className="p-3 font-semibold">Data Type</th>
                          <th className="p-3 font-semibold">Detected Role</th>
                          <th className="p-3 font-semibold">Missing Count (%)</th>
                          <th className="p-3 font-semibold">Unique Values</th>
                          <th className="p-3 font-semibold">Sample Values</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                        {datasetDetail.columnsSchema.map((col, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/30">
                            <td className="p-3 font-semibold text-white">{col.name}</td>
                            <td className="p-3">
                              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
                                {col.dataType}
                              </span>
                            </td>
                            <td className="p-3">
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider ${
                                  col.detectedRole === "date"
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : col.detectedRole === "amount"
                                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                    : col.detectedRole === "quantity"
                                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                    : col.detectedRole === "category"
                                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                    : "bg-slate-800 text-slate-400"
                                }`}
                              >
                                {col.detectedRole}
                              </span>
                            </td>
                            <td className="p-3 text-slate-300">
                              {col.missingCount.toLocaleString()} ({col.missingPercent}%)
                            </td>
                            <td className="p-3 text-slate-300">{col.uniqueCount.toLocaleString()}</td>
                            <td className="p-3 text-slate-400 truncate max-w-xs font-sans">
                              {col.sampleValues.slice(0, 3).map((v) => String(v)).join(", ")}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Paginated Real Records Preview */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-lg overflow-hidden space-y-4 p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <TableIcon className="h-4 w-4 text-indigo-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Real Dataset Records (Page {previewPage} of {previewData?.totalPages || 1})
                      </h4>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                        <input
                          type="text"
                          value={previewSearch}
                          onChange={(e) => setPreviewSearch(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && selectedDatasetId) {
                              loadDatasetPreview(selectedDatasetId, 1, previewSearch);
                            }
                          }}
                          placeholder="Search records..."
                          className="rounded-lg border border-slate-800 bg-slate-950/80 pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                        />
                      </div>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          if (selectedDatasetId) {
                            loadDatasetPreview(selectedDatasetId, 1, previewSearch);
                          }
                        }}
                        className="text-xs h-8 px-2.5"
                      >
                        Search
                      </Button>
                    </div>
                  </div>

                  {previewLoading ? (
                    <div className="p-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin text-indigo-400" />
                      Loading records...
                    </div>
                  ) : !previewData || previewData.rows.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-400">
                      No records found matching query.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[11px]">
                          <tr>
                            {previewData.columns.map((col, idx) => (
                              <th key={idx} className="p-3 font-semibold whitespace-nowrap">
                                {col.name}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                          {previewData.rows.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-slate-800/30">
                              {previewData.columns.map((col, cIdx) => (
                                <td key={cIdx} className="p-3 whitespace-nowrap">
                                  {typeof row[col.name] === "number"
                                    ? row[col.name].toLocaleString()
                                    : String(row[col.name] ?? "")}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Pagination Controls */}
                  {previewData && previewData.totalPages > 1 && (
                    <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
                      <span className="text-slate-400">
                        Showing {(previewPage - 1) * previewData.pageSize + 1} -{" "}
                        {Math.min(previewPage * previewData.pageSize, previewData.totalRows)} of{" "}
                        {previewData.totalRows.toLocaleString()} rows
                      </span>

                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={previewPage <= 1 || previewLoading}
                          onClick={() => {
                            if (selectedDatasetId) {
                              loadDatasetPreview(selectedDatasetId, previewPage - 1, previewSearch);
                            }
                          }}
                          className="h-8 px-2"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <span className="font-mono text-slate-300">
                          {previewPage} / {previewData.totalPages}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={previewPage >= previewData.totalPages || previewLoading}
                          onClick={() => {
                            if (selectedDatasetId) {
                              loadDatasetPreview(selectedDatasetId, previewPage + 1, previewSearch);
                            }
                          }}
                          className="h-8 px-2"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Unstructured Documents & RAG Pipeline */}
        {activeTab === "rag" && (
          <div className="space-y-6">
            {/* RAG Status Bar */}
            {ragHealth && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3 flex flex-wrap items-center justify-between text-xs text-slate-300 gap-2">
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  Vector Store: <strong>{ragHealth.vectorStore}</strong>
                </span>
                <span className="text-slate-400">
                  Total Indexed Chunks: <strong>{ragHealth.totalChunks}</strong>
                </span>
                <span className="text-slate-400">
                  Embedding Engine: <strong>{ragHealth.embeddingEngine}</strong>
                </span>
              </div>
            )}

            {/* Document Ingestion Upload */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <UploadCloud className="h-4 w-4 text-indigo-400" />
                Ingest PDF & Text Documents into Vector Store
              </h3>

              <div className="flex items-center gap-3">
                <input
                  ref={docFileInputRef}
                  type="file"
                  accept=".pdf,.txt"
                  onChange={async (e) => {
                    if (e.target.files && e.target.files[0]) {
                      const file = e.target.files[0];
                      try {
                        const res = await InsightFlowApi.uploadDocument(file);
                        if (res.data) {
                          setSuccessMessage(`Document '${file.name}' indexed successfully into ${res.data.chunkCount} vector chunks!`);
                          await fetchDocumentsAndHealth();
                        } else {
                          setErrorMessage(res.error || "Document indexing failed.");
                        }
                      } catch (err: any) {
                        setErrorMessage(err.message || "Failed to upload document.");
                      }
                    }
                  }}
                  className="hidden"
                  id="doc-upload-input"
                />
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => docFileInputRef.current?.click()}
                  className="gap-2"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Upload PDF / TXT Document
                </Button>
              </div>

              {/* Document List */}
              <div className="space-y-2 pt-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Indexed Knowledge Documents ({documents.length})
                </h4>

                {documents.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No business documents uploaded yet.</p>
                ) : (
                  <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/60">
                    {documents.map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between p-3 text-xs">
                        <div className="flex items-center gap-2.5">
                          <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
                          <div>
                            <span className="font-semibold text-white">{doc.filename}</span>
                            <span className="text-slate-500 ml-2">({formatFileSize(doc.fileSize)})</span>
                            <p className="text-[10px] text-slate-400">{doc.chunkCount} vector chunks • Uploaded {doc.createdAt}</p>
                          </div>
                        </div>
                        <button
                          onClick={async () => {
                            if (confirm(`Delete document '${doc.filename}'?`)) {
                              await InsightFlowApi.deleteDocument(doc.id);
                              await fetchDocumentsAndHealth();
                            }
                          }}
                          className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* RAG Search & Citations */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-lg p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Ask Documents (RAG Search)
              </h3>

              <form onSubmit={handleAskRag} className="flex gap-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  placeholder="Ask any question about your indexed policies, SLAs, or data..."
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/70 pl-4 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isAskingRag || !ragQuery.trim()}
                  className="gap-2 px-4 text-xs"
                >
                  {isAskingRag ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  Ask
                </Button>
              </form>

              {ragError && (
                <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
                  {ragError}
                </div>
              )}

              {ragResult && (
                <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3">
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
                    <Badge variant={ragResult.grounded ? "success" : "default"} size="sm">
                      {ragResult.grounded ? "Grounded in Document Evidence" : "General Knowledge"}
                    </Badge>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Latency: {ragResult.latencyMs}ms
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-line">
                    {ragResult.answer}
                  </p>

                  {ragResult.citations.length > 0 && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Verified Citations:</span>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {ragResult.citations.map((cite, idx) => (
                          <div key={idx} className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5 text-[11px] space-y-1">
                            <div className="flex items-center justify-between font-semibold text-white">
                              <span>{cite.documentName}</span>
                              <Badge variant="purple" size="sm">{Math.round(cite.relevanceScore * 100)}% Match</Badge>
                            </div>
                            <p className="text-slate-300 font-sans line-clamp-2">&ldquo;{cite.snippet}&rdquo;</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Permanent Deletion Confirmation Modal */}
        {datasetPendingDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md rounded-2xl border border-rose-500/30 bg-[#0d1322] p-6 shadow-2xl space-y-4">
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 shrink-0">
                  <AlertTriangle className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-white">Permanently Delete Dataset</h3>
                  <p className="text-xs font-semibold text-rose-200 leading-snug">
                    Are you sure you want to permanently delete this dataset and all its associated data?
                  </p>
                </div>
              </div>

              <div className="rounded-xl border border-white/[0.08] bg-slate-950/70 p-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400">Target Dataset:</span>
                  <span className="font-semibold text-white truncate max-w-[220px]" title={datasetPendingDelete.name}>
                    {datasetPendingDelete.name}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400">Stored Filename:</span>
                  <span className="font-mono text-slate-300 truncate max-w-[220px]" title={datasetPendingDelete.filename}>
                    {datasetPendingDelete.filename}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400">Records & Columns:</span>
                  <span className="font-mono text-slate-200">
                    {datasetPendingDelete.rowCount.toLocaleString()} rows • {datasetPendingDelete.columnCount} columns
                  </span>
                </div>
                {datasetPendingDelete.isActive && (
                  <div className="pt-2 border-t border-slate-800 text-[11px] text-amber-300 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                    <span>This is currently the active dataset. Another dataset will be promoted automatically.</span>
                  </div>
                )}
              </div>

              <div className="text-[11px] text-slate-400 leading-relaxed">
                <strong>Warning:</strong> This permanently deletes the dataset file from disk, removes detected schema definitions, purges data quality audits, and resets associated agent execution state.
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isDeleting}
                  onClick={() => setDatasetPendingDelete(null)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  disabled={isDeleting}
                  onClick={() => handleExecuteDelete(datasetPendingDelete)}
                  className="bg-rose-600 hover:bg-rose-500 text-white border-rose-500/50 gap-2 text-xs"
                >
                  {isDeleting ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-3.5 w-3.5" />
                      Permanently Delete
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
