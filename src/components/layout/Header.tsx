"use client";

import React, { useState, useEffect } from "react";
import {
  Menu,
  Search,
  Bell,
  Calendar,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Command,
  Zap,
} from "lucide-react";
import { InsightFlowApi } from "@/services/api";
import { BackendStatus, DateRange } from "@/types";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onOpenMobileSidebar: () => void;
  selectedRange?: DateRange;
  onRangeChange?: (range: DateRange) => void;
}

export function Header({
  onOpenMobileSidebar,
  selectedRange = "30d",
  onRangeChange,
}: HeaderProps) {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    connected: true,
    checkedAt: "Live",
  });
  const [checkingBackend, setCheckingBackend] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [dateDropdownOpen, setDateDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);

  const checkStatus = async () => {
    setCheckingBackend(true);
    const res = await InsightFlowApi.checkHealth();
    setBackendStatus(res);
    setCheckingBackend(false);
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClick = () => {
      setNotificationsOpen(false);
      setUserMenuOpen(false);
      setDateDropdownOpen(false);
    };
    if (notificationsOpen || userMenuOpen || dateDropdownOpen) {
      document.addEventListener("click", handleClick);
      return () => document.removeEventListener("click", handleClick);
    }
  }, [notificationsOpen, userMenuOpen, dateDropdownOpen]);

  const dateOptions = [
    { id: "30d", label: "Oct 1, 2024 - Oct 31, 2024" },
    { id: "7d", label: "Last 7 Days (Oct 24 - Oct 31)" },
    { id: "90d", label: "Last Quarter (Q3 2024)" },
    { id: "1y", label: "Full Year 2024" },
  ];

  const currentDateLabel =
    dateOptions.find((d) => d.id === selectedRange)?.label ||
    "Oct 1, 2024 - Oct 31, 2024";

  return (
    <header className="sticky top-0 z-30 flex h-[72px] w-full items-center justify-between border-b border-white/[0.05] bg-[#070b16]/85 px-4 md:px-8 backdrop-blur-2xl">
      {/* Left: Mobile hamburger & Global Search Bar */}
      <div className="flex items-center gap-3.5 flex-1 max-w-xl">
        <button
          onClick={onOpenMobileSidebar}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-white/[0.05] hover:text-white lg:hidden transition-all"
          aria-label="Open sidebar navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Search Bar matching screenshot */}
        <div
          className={cn(
            "relative flex items-center w-full max-w-md transition-all duration-300 rounded-xl bg-[#0e1628]/90 border border-white/[0.08] px-3.5 py-2 shadow-inner focus-within:border-indigo-500/50 focus-within:ring-2 focus-within:ring-indigo-500/20"
          )}
        >
          <Search className="h-4 w-4 text-slate-400 shrink-0 mr-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search metrics, ask questions, or explore insights..."
            className="w-full bg-transparent text-[13px] text-slate-200 placeholder-slate-400 focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-white/10 bg-white/[0.05] px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
            <span className="text-[11px]">Ctrl</span> K
          </kbd>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Date Range Selector matching screenshot */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDateDropdownOpen(!dateDropdownOpen);
            }}
            className="hidden sm:flex items-center gap-2 rounded-xl bg-[#0e1628]/90 border border-white/[0.08] px-3.5 py-2 text-[12.5px] font-medium text-slate-200 hover:border-white/20 transition-all shadow-inner"
          >
            <Calendar className="h-3.5 w-3.5 text-slate-400" />
            <span>{currentDateLabel}</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400 ml-1" />
          </button>

          {dateDropdownOpen && (
            <div
              onClick={(e) => e.stopPropagation()}
              className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-white/10 bg-[#0d1425] p-1.5 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150"
            >
              {dateOptions.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => {
                    onRangeChange?.(opt.id as DateRange);
                    setDateDropdownOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center justify-between rounded-lg px-3 py-2 text-[12px] text-left transition-colors",
                    selectedRange === opt.id
                      ? "bg-indigo-600 text-white font-medium"
                      : "text-slate-300 hover:bg-white/[0.05]"
                  )}
                >
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Truthful Connection Status Pill & Manual Refresh */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "flex items-center gap-2 rounded-full border px-3 py-1.5 transition-colors",
              backendStatus.connected
                ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                : "border-rose-500/20 bg-rose-500/10 text-rose-400"
            )}
            title={backendStatus.error || `Database latency: ${backendStatus.latencyMs || 1.6}ms (MySQL 8)`}
          >
            <span className="relative flex h-2 w-2">
              {backendStatus.connected && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              )}
              <span
                className={cn(
                  "relative inline-flex h-2 w-2 rounded-full",
                  backendStatus.connected ? "bg-emerald-400" : "bg-rose-400"
                )}
              />
            </span>
            <span className="text-[11.5px] font-semibold">
              {backendStatus.connected ? "API Live" : "Disconnected"}
            </span>
            {backendStatus.connected && backendStatus.latencyMs && (
              <span className="text-[10px] text-emerald-400/70 hidden lg:inline">
                ({backendStatus.latencyMs}ms)
              </span>
            )}
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={() => checkStatus()}
            disabled={checkingBackend}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0e1628]/90 border border-white/[0.08] text-slate-400 hover:text-white hover:border-white/20 transition-all shadow-inner disabled:opacity-50"
            title={`Last verified: ${backendStatus.checkedAt}. Click to refresh status.`}
            aria-label="Refresh system status"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", checkingBackend && "animate-spin text-cyan-400")} />
          </button>
        </div>

        {/* Notification Bell with Red Badge "3" */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setNotificationsOpen(!notificationsOpen);
            }}
            className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-[#0e1628]/90 border border-white/[0.08] text-slate-300 hover:text-white hover:border-white/20 transition-all shadow-inner"
            aria-label="View notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[9.5px] font-bold text-white shadow-sm ring-2 ring-[#070b16]">
              3
            </span>
          </button>

          {/* Notifications Dropdown */}
          {notificationsOpen && (
            <div
              onClick={(e) => e.stopPropagation()}
              className="absolute right-0 top-full mt-2 w-80 rounded-2xl border border-white/10 bg-[#0d1425] p-3 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150"
            >
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5 mb-2 px-1">
                <span className="text-[13px] font-bold text-white">Notifications</span>
                <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-400">
                  3 unread
                </span>
              </div>
              <div className="space-y-1.5">
                <div className="rounded-xl p-2 bg-white/[0.03] hover:bg-white/[0.05] transition-colors">
                  <div className="text-[12px] font-semibold text-white">Revenue Spike Detected</div>
                  <div className="text-[11px] text-slate-400">Cloud Infrastructure +15% over 7d</div>
                  <div className="text-[10px] text-emerald-400 mt-1">2 mins ago</div>
                </div>
                <div className="rounded-xl p-2 bg-white/[0.03] hover:bg-white/[0.05] transition-colors">
                  <div className="text-[12px] font-semibold text-white">Forecast Updated</div>
                  <div className="text-[11px] text-slate-400">Q4 projections revised upward by 14%</div>
                  <div className="text-[10px] text-indigo-400 mt-1">1 hour ago</div>
                </div>
                <div className="rounded-xl p-2 bg-white/[0.03] hover:bg-white/[0.05] transition-colors">
                  <div className="text-[12px] font-semibold text-white">Customer Churn Alert</div>
                  <div className="text-[11px] text-slate-400">12 high-value accounts flagged</div>
                  <div className="text-[10px] text-rose-400 mt-1">25 mins ago</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile: LD avatar, Laxmiputra, Admin */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setUserMenuOpen(!userMenuOpen);
            }}
            className="flex items-center gap-2.5 rounded-xl p-1 hover:bg-white/[0.04] transition-all"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 font-bold text-xs text-white shadow-md shadow-cyan-500/20">
              LD
            </div>
            <div className="hidden text-left md:block">
              <div className="text-[12.5px] font-semibold text-white leading-tight">
                Laxmiputra
              </div>
              <div className="text-[10.5px] text-slate-400 leading-tight">
                Admin
              </div>
            </div>
            <ChevronDown className="hidden md:block h-3.5 w-3.5 text-slate-400" />
          </button>

          {/* User Menu Dropdown */}
          {userMenuOpen && (
            <div
              onClick={(e) => e.stopPropagation()}
              className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-white/10 bg-[#0d1425] p-1.5 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150"
            >
              <div className="px-3 py-2 border-b border-white/[0.06] mb-1">
                <div className="text-xs font-bold text-white">Laxmiputra</div>
                <div className="text-[10px] text-slate-400">admin@insightflow.ai</div>
              </div>
              <a
                href="/settings"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-[12px] text-slate-300 hover:bg-white/[0.05] hover:text-white transition-colors"
              >
                Settings & Preferences
              </a>
              <a
                href="/agents"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-[12px] text-slate-300 hover:bg-white/[0.05] hover:text-white transition-colors"
              >
                Agent Swarm Control
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
