"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  Calendar,
  Layers,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  ArrowRight,
  Sliders,
  CheckCircle2,
  HelpCircle,
  BarChart3,
  ChevronRight,
  Database,
  History,
  Info,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { InsightFlowApi } from "@/services/api";
import {
  ForecastAvailabilityResponse,
  ForecastGenerateResponse,
  ForecastHistoryResponse,
  ForecastEvaluateResponse,
} from "@/types";

export default function ForecastPage() {
  const [metricName, setMetricName] = useState<"revenue" | "orders">("revenue");
  const [horizonDays, setHorizonDays] = useState<number>(14);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);

  const [availability, setAvailability] = useState<ForecastAvailabilityResponse | null>(null);
  const [loadingAvailability, setLoadingAvailability] = useState<boolean>(true);

  const [forecast, setForecast] = useState<ForecastGenerateResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [history, setHistory] = useState<ForecastHistoryResponse | null>(null);
  const [evaluation, setEvaluation] = useState<ForecastEvaluateResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // Check data availability and load history on mount
  useEffect(() => {
    checkDataAvailability(metricName);
    loadHistory();
  }, [metricName]);

  const checkDataAvailability = async (metric: string) => {
    setLoadingAvailability(true);
    try {
      const availResp = await InsightFlowApi.getForecastAvailability(metric);
      if (availResp.data) {
        setAvailability(availResp.data);
        if (availResp.data.hasSufficientData && !forecast) {
          // Auto-generate initial 14d forecast
          handleGenerate(metric, horizonDays);
        }
      } else if (availResp.error) {
        setErrorMsg(availResp.error);
      }
    } catch (err: any) {
      console.warn("Availability check error:", err);
      setErrorMsg(err?.message || "Failed to inspect forecast availability.");
    } finally {
      setLoadingAvailability(false);
    }
  };

  const loadHistory = async () => {
    try {
      const histResp = await InsightFlowApi.getForecastHistory(10);
      if (histResp.data) {
        setHistory(histResp.data);
      }
    } catch (err: any) {
      console.warn("History fetch error:", err);
    }
  };

  const handleGenerate = async (metric?: string, horizon?: number) => {
    const selectedMetric = metric || metricName;
    const selectedHorizon = horizon || horizonDays;

    setIsGenerating(true);
    setErrorMsg(null);
    setEvaluation(null);

    try {
      const resp = await InsightFlowApi.generateForecast({
        metricName: selectedMetric,
        horizonDays: selectedHorizon,
        confidenceLevel,
      });
      if (resp.data) {
        setForecast(resp.data);
        await loadHistory();
      } else if (resp.error) {
        setErrorMsg(resp.error);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate empirical forecast.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEvaluate = async (runId: string) => {
    setIsEvaluating(true);
    try {
      const evalResp = await InsightFlowApi.evaluateForecast(runId);
      if (evalResp.data) {
        setEvaluation(evalResp.data);
      } else if (evalResp.error) {
        setErrorMsg(evalResp.error);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to evaluate forecast run.");
    } finally {
      setIsEvaluating(false);
    }
  };

  // Combine historical points and forecast points into continuous chart series
  const prepareChartData = () => {
    if (!forecast) return [];

    const chartData: any[] = [];

    // Add recent historical observations
    const recentHist = forecast.historicalPoints.slice(-30);
    recentHist.forEach((pt) => {
      chartData.push({
        date: pt.date.slice(5), // MM-DD
        fullDate: pt.date,
        actual: pt.value,
        forecast: null,
        lower: null,
        upper: null,
        isActual: pt.isActual,
      });
    });

    // Bridge historical last point to forecast start so lines connect
    if (recentHist.length > 0) {
      const lastHist = recentHist[recentHist.length - 1];
      const bridgeIndex = chartData.length - 1;
      chartData[bridgeIndex].forecast = lastHist.value;
      chartData[bridgeIndex].lower = lastHist.value;
      chartData[bridgeIndex].upper = lastHist.value;
    }

    // Add projected future points
    forecast.forecastPoints.forEach((pt) => {
      chartData.push({
        date: pt.date.slice(5),
        fullDate: pt.date,
        actual: null,
        forecast: pt.forecast,
        lower: pt.lowerBound,
        upper: pt.upperBound,
        isActual: false,
      });
    });

    return chartData;
  };

  const chartData = prepareChartData();

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-indigo-400" />
                Predictive Analytics & Sales Forecasting
              </h1>
              <Badge variant="purple" size="sm">
                Milestone 8
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Empirical time-series forecasting with chronological out-of-sample model selection and prediction bands
            </p>
          </div>

          {/* Data Availability Indicator Pill */}
          <div className="flex items-center gap-2">
            {availability && (
              <div className="flex flex-wrap items-center gap-2 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/80 text-[11px] text-slate-300">
                <span
                  className={`h-2 w-2 rounded-full ${
                    availability.hasSufficientData ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                  }`}
                />
                <span>
                  MySQL Observations: <strong>{availability.totalObservations} days</strong>
                </span>
                <span className="text-slate-600">•</span>
                <span>{availability.minDate} to {availability.maxDate}</span>
                <span className="text-slate-600">•</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                    availability.dataProvenance === "empirical_recorded"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  }`}
                  title="Data provenance classification"
                >
                  {availability.provenanceLabel || (availability.dataProvenance === "empirical_recorded" ? "Empirical Production Data" : "Synthetic Baseline (Demo Seed)")}
                </span>
              </div>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => checkDataAvailability(metricName)}
              disabled={loadingAvailability}
              title="Refresh database records"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingAvailability ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
            <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400" />
            <span className="flex-1 font-medium">{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* Insufficient Data State */}
        {availability && !availability.hasSufficientData && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertTriangle className="h-5 w-5" />
              Insufficient Historical Observations
            </div>
            <p className="text-xs text-amber-200 leading-relaxed max-w-2xl">
              {availability.message} To preserve empirical rigor, InsightFlow AI does not fabricate forecasts without sufficient historical observations. Please ingest historical transaction data or run seed migrations.
            </p>
            <div className="pt-2 flex items-center gap-3">
              <a href="/upload">
                <Button size="sm" variant="primary">
                  Upload Historical CSV Records
                  <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </Button>
              </a>
            </div>
          </div>
        )}

        {/* Interactive Forecasting Controls */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg backdrop-blur-md">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            {/* Metric Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Database className="h-3.5 w-3.5 text-indigo-400" />
                Target Business KPI
              </label>
              <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-950 p-1 border border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setMetricName("revenue");
                    handleGenerate("revenue", horizonDays);
                  }}
                  className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                    metricName === "revenue"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Revenue ($)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMetricName("orders");
                    handleGenerate("orders", horizonDays);
                  }}
                  className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                    metricName === "orders"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Order Volume
                </button>
              </div>
            </div>

            {/* Horizon Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-indigo-400" />
                Forecast Horizon
              </label>
              <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-950 p-1 border border-slate-800">
                {[7, 14, 30].map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => {
                      setHorizonDays(h);
                      handleGenerate(metricName, h);
                    }}
                    className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                      horizonDays === h
                        ? "bg-indigo-600 text-white shadow"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {h} Days
                  </button>
                ))}
              </div>
            </div>

            {/* Prediction Interval Confidence */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                Confidence Band
              </label>
              <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-950 p-1 border border-slate-800">
                {[0.95, 0.80].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setConfidenceLevel(c)}
                    className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                      confidenceLevel === c
                        ? "bg-indigo-600 text-white shadow"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {Math.round(c * 100)}% Interval
                  </button>
                ))}
              </div>
            </div>

            {/* Run Button */}
            <div>
              <Button
                variant="primary"
                onClick={() => handleGenerate()}
                disabled={isGenerating || !availability?.hasSufficientData}
                className="w-full gap-2 py-2.5"
              >
                {isGenerating ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                <span>Run Empirical Forecast</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Primary Visualization & Model Telemetry */}
        {forecast && (
          <div className="space-y-6">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <span className="text-[11px] text-slate-400 block font-sans">Selected Champion Model</span>
                <p className="text-base font-bold text-white font-mono mt-1 truncate" title={forecast.selectedModel}>
                  {forecast.selectedModel}
                </p>
                <span className="text-[10px] text-indigo-400 block mt-0.5">
                  Top Holdout RMSE Performer
                </span>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <span className="text-[11px] text-slate-400 block font-sans">Projected Growth Rate</span>
                <p
                  className={`text-xl font-bold font-mono mt-1 flex items-center gap-1 ${
                    forecast.projectedGrowthRate >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {forecast.projectedGrowthRate >= 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {forecast.projectedGrowthRate >= 0 ? `+${forecast.projectedGrowthRate}%` : `${forecast.projectedGrowthRate}%`}
                </p>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  vs previous {forecast.horizonDays} days
                </span>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <span className="text-[11px] text-slate-400 block font-sans">Out-of-Sample RMSE</span>
                <p className="text-xl font-bold text-white font-mono mt-1">
                  {forecast.metricName === "revenue"
                    ? `$${forecast.outOfSampleMetrics.rmse.toLocaleString()}`
                    : `${forecast.outOfSampleMetrics.rmse.toLocaleString()} units`}
                </p>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Holdout Validation Error
                </span>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <span className="text-[11px] text-slate-400 block font-sans">Out-of-Sample MAPE</span>
                <p className="text-xl font-bold text-cyan-400 font-mono mt-1">
                  {forecast.outOfSampleMetrics.mape.toFixed(2)}%
                </p>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Holdout Mean Error %
                </span>
              </div>
            </div>

            {/* Time-Series Chart */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-lg backdrop-blur-md p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                <div>
                  <h3 className="text-sm font-semibold text-white flex flex-wrap items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-cyan-400" />
                    Historical Trajectory & {forecast.horizonDays}-Day Forecast Projection
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-mono font-normal uppercase ${
                        forecast.dataProvenance === "empirical_recorded"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {forecast.provenanceLabel || (forecast.dataProvenance === "empirical_recorded" ? "Empirical Production" : "Synthetic Baseline (Demo Seed)")}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Solid line indicates observed historical actuals; dashed line indicates future projections with shaded confidence bounds
                  </p>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-indigo-400">
                    <span className="h-2 w-3 bg-indigo-500 rounded-sm" /> Historical Actuals
                  </span>
                  <span className="flex items-center gap-1.5 text-cyan-400">
                    <span className="h-2 w-3 border-t-2 border-dashed border-cyan-400" /> Forecast Projection
                  </span>
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <span className="h-2 w-3 bg-emerald-500/30 rounded-sm" /> 95% Confidence Band
                  </span>
                </div>
              </div>

              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) =>
                        forecast.metricName === "revenue"
                          ? `$${(val / 1000).toFixed(0)}k`
                          : `${val}`
                      }
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (active && payload && payload.length) {
                          const dataPoint = payload[0].payload;
                          return (
                            <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 text-xs text-white shadow-xl space-y-1">
                              <p className="font-semibold text-slate-300 font-mono">Date: {dataPoint.fullDate}</p>
                              {dataPoint.actual !== null && (
                                <p className="text-indigo-400 font-mono">
                                  Historical Actual: {forecast.metricName === "revenue" ? `$${dataPoint.actual.toLocaleString()}` : `${dataPoint.actual.toLocaleString()}`}
                                </p>
                              )}
                              {dataPoint.forecast !== null && (
                                <p className="text-cyan-400 font-mono">
                                  Forecasted: {forecast.metricName === "revenue" ? `$${dataPoint.forecast.toLocaleString()}` : `${dataPoint.forecast.toLocaleString()}`}
                                </p>
                              )}
                              {dataPoint.lower !== null && dataPoint.upper !== null && (
                                <p className="text-emerald-400 text-[10px] font-mono">
                                  Confidence Band: [{dataPoint.lower.toLocaleString()} - {dataPoint.upper.toLocaleString()}]
                                </p>
                              )}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />

                    {/* Shaded Confidence Intervals */}
                    <Area
                      type="monotone"
                      dataKey="upper"
                      stroke="none"
                      fill="#10b981"
                      fillOpacity={0.12}
                    />
                    <Area
                      type="monotone"
                      dataKey="lower"
                      stroke="none"
                      fill="#0f172a"
                      fillOpacity={0.8}
                    />

                    {/* Historical Actual Line */}
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      dot={false}
                    />

                    {/* Forecasted Line */}
                    <Line
                      type="monotone"
                      dataKey="forecast"
                      stroke="#06b6d4"
                      strokeWidth={2.5}
                      strokeDasharray="4 4"
                      dot={{ r: 3, fill: "#06b6d4" }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Bottom Grid: Grounded Recommendations & Model Benchmark Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Executive Business Recommendations */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-indigo-400" />
                    Forecast-Grounded Business Recommendations
                  </h4>
                  <Badge variant={forecast.trendDirection === "up" ? "success" : "warning"} size="sm">
                    {forecast.trendDirection.toUpperCase()} TREND
                  </Badge>
                </div>

                <div className="space-y-3">
                  {forecast.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5"
                    >
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>

                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 shrink-0 text-indigo-400" />
                  <span>
                    Recommendations strictly reflect empirical trend trajectories and out-of-sample error bounds; no hallucinated business facts.
                  </span>
                </div>
              </div>

              {/* Candidate Model Comparison Benchmark */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Sliders className="h-4 w-4 text-indigo-400" />
                    Out-of-Sample Model Benchmarks
                  </h4>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Evaluation: Chronological Test Split
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="p-2.5 font-semibold">Algorithm</th>
                        <th className="p-2.5 font-semibold">Holdout MAE</th>
                        <th className="p-2.5 font-semibold">Holdout RMSE</th>
                        <th className="p-2.5 font-semibold">Holdout MAPE</th>
                        <th className="p-2.5 font-semibold text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                      {forecast.candidateEvaluations.map((cand, idx) => (
                        <tr
                          key={idx}
                          className={cand.selected ? "bg-indigo-500/10" : "hover:bg-slate-800/40"}
                        >
                          <td className="p-2.5 font-sans font-medium text-white flex items-center gap-1.5">
                            {cand.modelName}
                          </td>
                          <td className="p-2.5">{cand.mae.toLocaleString()}</td>
                          <td className="p-2.5 font-semibold text-white">{cand.rmse.toLocaleString()}</td>
                          <td className="p-2.5 text-cyan-400">{cand.mape.toFixed(2)}%</td>
                          <td className="p-2.5 text-right font-sans">
                            {cand.selected ? (
                              <Badge variant="purple" size="sm">
                                Selected
                              </Badge>
                            ) : (
                              <span className="text-[10px] text-slate-500">Candidate</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="text-[11px] text-slate-500 font-mono pt-1">
                  Chronological split guarantees zero data leakage between training and evaluation windows.
                </div>
              </div>
            </div>

            {/* Forecast History & Realized Accuracy Audit */}
            {history && history.runs.length > 0 && (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-slate-800">
                  <h4 className="text-xs font-semibold text-white flex items-center gap-2">
                    <History className="h-4 w-4 text-indigo-400" />
                    Saved Forecast Runs & Historical Audits
                  </h4>
                  <span className="text-xs text-slate-400 font-mono">
                    Total Logged Runs: {history.totalCount}
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="p-3 font-semibold">Run ID</th>
                        <th className="p-3 font-semibold">Metric</th>
                        <th className="p-3 font-semibold">Horizon</th>
                        <th className="p-3 font-semibold">Winning Model</th>
                        <th className="p-3 font-semibold">Holdout RMSE</th>
                        <th className="p-3 font-semibold">Growth Pace</th>
                        <th className="p-3 font-semibold">Timestamp</th>
                        <th className="p-3 font-semibold text-right">Audit</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                      {history.runs.map((r) => (
                        <tr key={r.id} className="hover:bg-slate-800/40">
                          <td className="p-3 text-indigo-400">{r.id}</td>
                          <td className="p-3 uppercase">{r.metricName}</td>
                          <td className="p-3">{r.horizonDays}d</td>
                          <td className="p-3 font-sans text-white">{r.modelName}</td>
                          <td className="p-3">{r.rmse.toLocaleString()}</td>
                          <td className="p-3">
                            <span className={r.growthRate >= 0 ? "text-emerald-400" : "text-rose-400"}>
                              {r.growthRate >= 0 ? `+${r.growthRate}%` : `${r.growthRate}%`}
                            </span>
                          </td>
                          <td className="p-3 text-slate-400">{r.createdAt}</td>
                          <td className="p-3 text-right font-sans">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEvaluate(r.id)}
                              className="h-7 text-xs"
                              disabled={isEvaluating}
                            >
                              Evaluate
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Audit Result Display */}
                {evaluation && (
                  <div className="p-4 border-t border-slate-800 bg-slate-950/70 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        Realized Calibration Audit for {evaluation.runId}
                      </span>
                      <Badge variant="purple" size="sm">
                        {evaluation.evaluatedPointsCount} Actuals Recorded
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-300">{evaluation.accuracyStatus}</p>
                    {evaluation.evaluatedPointsCount > 0 && (
                      <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs">
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          Realized MAE: <strong>{evaluation.realizedMae.toLocaleString()}</strong>
                        </div>
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          Realized RMSE: <strong>{evaluation.realizedRmse.toLocaleString()}</strong>
                        </div>
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          Realized MAPE: <strong>{evaluation.realizedMape.toFixed(2)}%</strong>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
