"use client";

import React, { useState, useEffect } from "react";
import {
  FileSpreadsheet,
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  Bot,
  Sparkles,
  CheckCircle,
  FileText,
  Clock,
  ArrowDownToLine,
  Share2,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { InsightFlowApi } from "@/services/api";
import { ReportItem } from "@/types";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReports() {
      const res = await InsightFlowApi.getReports();
      if (res.data) {
        setReports(res.data);
      }
    }
    loadReports();
  }, []);

  const categories = ["All", "Executive", "Diagnostic", "Forecast", "Operational"];

  const filteredReports = reports.filter((rep) => {
    const matchesSearch =
      rep.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rep.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "All" || rep.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handlePreview = (report: ReportItem) => {
    setSelectedReport(report);
    setPreviewModalOpen(true);
  };

  const handleDownload = (report: ReportItem, format: "md" | "csv" = "md") => {
    const downloadUrl = InsightFlowApi.getReportDownloadUrl(report.id, format);
    window.open(downloadUrl, "_blank");
  };

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    setGenerateError(null);
    try {
      const cat = selectedCategory === "All" ? "Executive" : selectedCategory;
      const res = await InsightFlowApi.generateReport({
        category: cat,
        range: "30d",
        custom_title: `Executive ${cat} Intelligence Synthesis (${new Date().toLocaleDateString("en-US", { month: "short", year: "numeric" })})`,
      });
      if (res.data) {
        setReports((prev) => [res.data!, ...prev]);
        setSelectedReport(res.data);
        setPreviewModalOpen(true);
      } else {
        setGenerateError(res.error || "Failed to synthesize report.");
      }
    } catch (err: any) {
      setGenerateError(err?.message || "Report generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-indigo-400" />
              Generated Intelligence Reports
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Access executive syntheses, root cause deep-dives, and forecasting briefs compiled by the Report Agent
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="gap-2"
            >
              <Sparkles className={`h-4 w-4 ${isGenerating ? "animate-spin" : "text-indigo-300"}`} />
              <span>{isGenerating ? "Synthesizing Report..." : "Generate Report"}</span>
            </Button>
            <Badge variant="purple" size="md">
              {reports.length} Reports in MySQL
            </Badge>
          </div>
        </div>

        {generateError && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-300">
            {generateError}
          </div>
        )}

        {/* Filter and Search Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search reports by title, keyword, or metric..."
              className="w-full rounded-xl border border-slate-800 bg-slate-900/90 py-2.5 pl-10 pr-4 text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
            />
          </div>

          {/* Category Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-xl px-3 py-2 text-xs font-medium transition-all ${
                  selectedCategory === cat
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "border border-slate-800 bg-slate-900/80 text-slate-400 hover:text-white"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Reports Listing Grid */}
        {filteredReports.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredReports.map((report) => (
              <div
                key={report.id}
                className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg backdrop-blur-md flex flex-col justify-between hover:border-slate-700/80 transition-all duration-200"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-md">
                      {report.category}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {report.fileSize || "1.2 MB"}
                    </span>
                  </div>

                  <h3
                    onClick={() => handlePreview(report)}
                    className="mt-2.5 text-sm font-bold text-white hover:text-indigo-300 transition-colors cursor-pointer"
                  >
                    {report.title}
                  </h3>

                  <p className="mt-1.5 text-xs text-slate-300 leading-relaxed line-clamp-3">
                    {report.summary}
                  </p>

                  {/* Key Metrics row */}
                  <div className="mt-3.5 grid grid-cols-3 gap-2 py-2.5 px-3 rounded-xl border border-slate-800/80 bg-slate-950/60">
                    {report.keyMetrics.map((m, idx) => (
                      <div key={idx}>
                        <span className="text-[10px] text-slate-400 block truncate">{m.label}</span>
                        <span className="text-xs font-bold text-white font-mono mt-0.5 block">
                          {m.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer with action buttons */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5 text-[11px]">
                    <Clock className="h-3.5 w-3.5 text-slate-500" />
                    {report.generatedAt}
                  </span>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handlePreview(report)}
                      className="text-xs gap-1.5"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      Preview
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(report, "md")}
                      className="text-xs gap-1.5"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Export Markdown
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={FileSpreadsheet}
            title="No reports match your search criteria"
            description="Try modifying your keyword filter or select 'All' categories."
            action={
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedCategory("All");
                }}
              >
                Clear Search & Filters
              </Button>
            }
          />
        )}

        {/* Report Preview Modal */}
        {selectedReport && (
          <Modal
            isOpen={previewModalOpen}
            onClose={() => setPreviewModalOpen(false)}
            title={selectedReport.title}
            description={`Category: ${selectedReport.category} • Synthesized by ${selectedReport.agent} on ${selectedReport.generatedAt}`}
            maxWidth="2xl"
          >
            <div className="space-y-4">
              <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5 mb-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  Executive Synthesis
                </span>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {selectedReport.summary}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Key Diagnostic Metrics
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  {selectedReport.keyMetrics.map((km, i) => (
                    <div key={i} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                      <span className="text-[11px] text-slate-400 block">{km.label}</span>
                      <span className="text-base font-bold text-white font-mono mt-0.5 block">
                        {km.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-xs text-slate-300 space-y-2">
                <h5 className="font-semibold text-white">Agent Attribution & Confidence</h5>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  This report was compiled through multi-model attribution combining automated variance analysis and Bayesian forecasting models. Confidence interval calibrated at 95%.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDownload(selectedReport, "csv")}
                  className="gap-1.5 text-xs"
                >
                  <ArrowDownToLine className="h-3.5 w-3.5" />
                  Download CSV
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleDownload(selectedReport, "md")}
                  className="gap-1.5 text-xs"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download Markdown Report
                </Button>
              </div>
            </div>
          </Modal>
        )}
      </div>
    </AppShell>
  );
}
