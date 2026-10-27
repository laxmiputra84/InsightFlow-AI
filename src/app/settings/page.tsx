"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  User,
  Shield,
  Server,
  Bell,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Key,
  Globe,
  Sliders,
  Save,
  AlertCircle,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { InsightFlowApi } from "@/services/api";
import { BackendStatus } from "@/types";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"profile" | "preferences" | "backend" | "security">("profile");

  // Profile form state
  const [profile, setProfile] = useState({
    name: "Sarah Jenkins",
    email: "sarah.jenkins@enterprise-bi.ai",
    company: "InsightFlow Analytics Inc.",
    role: "Chief Data Officer",
    department: "Executive Business Intelligence",
  });

  // App preferences
  const [preferences, setPreferences] = useState({
    currency: "USD",
    theme: "dark",
    aiModel: "Claude 3.5 Sonnet (Optimized for BI Decomposition)",
    autoRunDailyAnalysis: true,
    emailAlerts: true,
    anomalyThresholdPercent: 10,
  });

  // Backend connection state
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  );
  const [apiToken, setApiToken] = useState("");
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const testConnection = async () => {
    setIsTestingConnection(true);
    const res = await InsightFlowApi.checkHealth();
    setBackendStatus(res);
    setIsTestingConnection(false);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedKey = sessionStorage.getItem("insightflow_session_key") || localStorage.getItem("insightflow_api_key");
      if (storedKey) setApiToken(storedKey);
    }
    testConnection();
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      if (apiToken.trim()) {
        sessionStorage.setItem("insightflow_session_key", apiToken.trim());
        localStorage.removeItem("insightflow_api_key");
      } else {
        sessionStorage.removeItem("insightflow_session_key");
        localStorage.removeItem("insightflow_api_key");
      }
    }
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-5xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Settings className="h-5 w-5 text-indigo-400" />
              Settings & Platform Configuration
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage user profile, model parameters, and configure FastAPI backend connectivity
            </p>
          </div>

          {saveSuccess && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
              <CheckCircle2 className="h-4 w-4" />
              Configuration saved successfully
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
          {[
            { id: "profile", label: "User Profile & Org", icon: User },
            { id: "backend", label: "FastAPI Backend & API", icon: Server },
            { id: "preferences", label: "AI Models & Analytics", icon: Sliders },
            { id: "security", label: "Authentication & Security", icon: Shield },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all shrink-0 ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Profile */}
        {activeTab === "profile" && (
          <form onSubmit={handleSave} className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-lg backdrop-blur-md space-y-5">
              <div className="flex items-center gap-4 pb-5 border-b border-slate-800">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white font-bold text-xl shadow-lg shadow-indigo-500/20">
                  SJ
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{profile.name}</h3>
                  <p className="text-xs text-slate-400">{profile.role} • {profile.department}</p>
                  <span className="inline-block mt-1.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 text-[10px] font-semibold">
                    Enterprise Administrator
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Work Email
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Organization / Company
                  </label>
                  <input
                    type="text"
                    value={profile.company}
                    onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Department
                  </label>
                  <input
                    type="text"
                    value={profile.department}
                    onChange={(e) => setProfile({ ...profile, department: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800">
                <Button type="submit" variant="primary" size="sm" className="gap-2">
                  <Save className="h-3.5 w-3.5" />
                  Save Profile Changes
                </Button>
              </div>
            </div>
          </form>
        )}

        {/* Tab 2: Backend & API */}
        {activeTab === "backend" && (
          <div className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-lg backdrop-blur-md space-y-5">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Server className="h-4 w-4 text-indigo-400" />
                  FastAPI Backend Server Connection
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  InsightFlow AI frontend communicates with a Python FastAPI backend for statistical analytics, Prophet forecasting, and multi-agent coordination.
                </p>
              </div>

              {/* Status Banner */}
              <div
                className={`rounded-xl border p-4 flex items-center justify-between gap-3 ${
                  backendStatus?.connected
                    ? "border-emerald-500/25 bg-emerald-500/5 text-emerald-300"
                    : "border-amber-500/25 bg-amber-500/5 text-amber-300"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`h-3 w-3 rounded-full ${
                      backendStatus?.connected
                        ? "bg-emerald-400 animate-pulse"
                        : "bg-amber-400"
                    }`}
                  />
                  <div>
                    <h4 className="text-xs font-bold">
                      {backendStatus?.connected
                        ? `Connected to FastAPI (${backendStatus.latencyMs}ms latency)`
                        : "FastAPI Backend is Currently Offline"}
                    </h4>
                    <p className="text-[11px] text-slate-300 mt-0.5">
                      {backendStatus?.connected
                        ? `Server version ${backendStatus.version || "1.0.0"} online and accepting requests.`
                        : `Requests gracefully fall back to local demo data. Start your FastAPI server on ${apiUrl} to connect.`}
                    </p>
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={testConnection}
                  disabled={isTestingConnection}
                  className="gap-2 text-xs shrink-0"
                >
                  <RefreshCw
                    className={`h-3 w-3 ${isTestingConnection ? "animate-spin" : ""}`}
                  />
                  Ping Backend
                </Button>
              </div>

              {/* Form settings */}
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Backend API Base URL (Configured via NEXT_PUBLIC_API_URL)
                  </label>
                  <input
                    type="text"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  />
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Default: http://localhost:8000 or production server endpoint
                  </span>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    FastAPI Session API Key / Bearer Token (Optional)
                  </label>
                  <input
                    type="password"
                    value={apiToken}
                    onChange={(e) => setApiToken(e.target.value)}
                    placeholder="Enter production API key..."
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  />
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Stored in ephemeral browser session memory for current tab; never baked into client bundles.
                  </span>
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800">
                <Button onClick={handleSave} variant="primary" size="sm" className="gap-2">
                  <Save className="h-3.5 w-3.5" />
                  Save Backend Settings
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Preferences */}
        {activeTab === "preferences" && (
          <div className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-lg backdrop-blur-md space-y-5">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-cyan-400" />
                  AI Models & Statistical Preferences
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Configure default reasoning parameters and analytical models used by the agent swarm
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Primary Agent LLM Backbone
                  </label>
                  <select
                    value={preferences.aiModel}
                    onChange={(e) =>
                      setPreferences({ ...preferences, aiModel: e.target.value })
                    }
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="Claude 3.5 Sonnet (Optimized for BI Decomposition)">
                      Claude 3.5 Sonnet (Optimized for BI Decomposition)
                    </option>
                    <option value="GPT-4o (High-Throughput Synthesis)">
                      GPT-4o (High-Throughput Synthesis)
                    </option>
                    <option value="Gemini 1.5 Pro (Long-Context Analytics)">
                      Gemini 1.5 Pro (Long-Context Analytics)
                    </option>
                    <option value="Llama 3 70B (Self-Hosted on FastAPI)">
                      Llama 3 70B (Self-Hosted on FastAPI)
                    </option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Default Reporting Currency
                  </label>
                  <select
                    value={preferences.currency}
                    onChange={(e) =>
                      setPreferences({ ...preferences, currency: e.target.value })
                    }
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="CAD">CAD ($)</option>
                  </select>
                </div>

                <div className="pt-2 space-y-3">
                  <label className="flex items-center gap-2.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.autoRunDailyAnalysis}
                      onChange={(e) =>
                        setPreferences({
                          ...preferences,
                          autoRunDailyAnalysis: e.target.checked,
                        })
                      }
                      className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-xs text-slate-200">
                      Automatically execute daily EDA & anomaly detection at 00:00 UTC
                    </span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.emailAlerts}
                      onChange={(e) =>
                        setPreferences({ ...preferences, emailAlerts: e.target.checked })
                      }
                      className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-xs text-slate-200">
                      Send instant notification when Root Cause Agent catches critical anomalies
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800">
                <Button onClick={handleSave} variant="primary" size="sm" className="gap-2">
                  <Save className="h-3.5 w-3.5" />
                  Save Preferences
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Security & Auth */}
        {activeTab === "security" && (
          <div className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-lg backdrop-blur-md space-y-5">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Shield className="h-4 w-4 text-emerald-400" />
                  Authentication & Security Architecture
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  InsightFlow AI is engineered to integrate cleanly with enterprise SSO (SAML/Okta), OAuth2, and FastAPI JWT authentication.
                </p>
              </div>

              <div className="space-y-3">
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-white">OAuth2 / OIDC Single Sign-On</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Ready for Okta, Google Workspace, or Azure Active Directory integration
                      </p>
                    </div>
                    <Badge variant="outline" size="sm">
                      Ready for Hook
                    </Badge>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-white">Role-Based Access Control (RBAC)</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Current role: Chief Data Officer (Full Read / Write / Pipeline Execution permissions)
                      </p>
                    </div>
                    <Badge variant="success" size="sm">
                      Enforced
                    </Badge>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-white">Client-Side Credential Safety</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Zero sensitive API keys or database connection strings are exposed in frontend client code
                      </p>
                    </div>
                    <Badge variant="success" size="sm">
                      Compliant
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
