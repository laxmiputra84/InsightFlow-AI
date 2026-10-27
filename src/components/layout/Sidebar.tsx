"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BrainCircuit,
  UploadCloud,
  Bot,
  FileSpreadsheet,
  Settings,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Sparkles,
  Database,
  Search,
  LineChart,
  Lightbulb,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const NAV_ITEMS = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "AI Analytics",
    href: "/analytics",
    icon: BrainCircuit,
    badge: "NLP",
  },
  {
    name: "Forecasting",
    href: "/forecast",
    icon: TrendingUp,
    badge: "ML",
  },
];

const OPERATIONS_ITEMS = [
  {
    name: "Data Upload",
    href: "/upload",
    icon: UploadCloud,
    badge: null,
  },
  {
    name: "AI Agents",
    href: "/agents",
    icon: Bot,
    badge: "4",
  },
  {
    name: "Reports",
    href: "/reports",
    icon: FileSpreadsheet,
    badge: null,
  },
];

const SYSTEM_ITEMS = [
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
    badge: null,
  },
];

const SWARM_AGENTS = [
  {
    name: "Analytics Agent",
    status: "Online",
    icon: Database,
    color: "from-blue-500 to-indigo-600",
  },
  {
    name: "RAG Agent",
    status: "Online",
    icon: Search,
    color: "from-cyan-400 to-blue-500",
  },
  {
    name: "Forecast Agent",
    status: "Online",
    icon: LineChart,
    color: "from-sky-400 to-indigo-500",
  },
  {
    name: "Insights Agent",
    status: "Online",
    icon: Lightbulb,
    color: "from-amber-400 to-orange-500",
  },
];

export function Sidebar({
  isCollapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onCloseMobile,
}: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-40 flex flex-col border-r transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
          "border-white/[0.06] bg-[#070b16] backdrop-blur-2xl",
          isCollapsed ? "w-[76px]" : "w-[260px]",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* ── Brand Header ──────────────────────── */}
        <div className="flex h-[72px] items-center justify-between px-4 border-b border-white/[0.05]">
          <Link
            href="/"
            className="flex items-center gap-3 overflow-hidden group"
            onClick={onCloseMobile}
          >
            {/* Cyan/Blue Glowing Waves Icon */}
            <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-shadow">
              <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-[#070b16]">
                <svg
                  className="h-5 w-5 text-cyan-400"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 13.5C5.5 8.5 8.5 7 12 12C15.5 17 18.5 15.5 21 10.5"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M3 18C5.5 13 8.5 11.5 12 16.5C15.5 21.5 18.5 20 21 15"
                    stroke="url(#cyan-grad)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.6"
                  />
                  <defs>
                    <linearGradient id="cyan-grad" x1="3" y1="18" x2="21" y2="15" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#38bdf8" />
                      <stop offset="1" stopColor="#818cf8" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>

            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-[15px] font-bold tracking-tight text-white flex items-center">
                  InsightFlow AI
                </span>
                <span className="text-[9.5px] font-bold uppercase tracking-[0.14em] text-cyan-400/90">
                  Autonomous BI Agent
                </span>
              </div>
            )}
          </Link>

          {/* Collapse toggle */}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="hidden lg:flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-white/[0.05] hover:text-white transition-all"
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
          )}
        </div>

        {/* ── Navigation ────────────────────────── */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin">
          {/* Main Items */}
          <div className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-medium transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30"
                      : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon
                    className={cn(
                      "h-[18px] w-[18px] shrink-0 transition-colors",
                      isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                    )}
                  />
                  {!isCollapsed && (
                    <span className="flex-1 truncate">{item.name}</span>
                  )}
                  {!isCollapsed && item.badge && (
                    <span
                      className={cn(
                        "rounded-md px-1.5 py-0.5 text-[10px] font-bold tracking-wider",
                        isActive
                          ? "bg-white/20 text-white"
                          : "bg-slate-800/80 text-cyan-400 border border-slate-700/60"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Operations Section */}
          <div className="space-y-1">
            {!isCollapsed && (
              <div className="px-3 pb-1.5">
                <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Operations
                </span>
              </div>
            )}
            {OPERATIONS_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-medium transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30"
                      : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon
                    className={cn(
                      "h-[18px] w-[18px] shrink-0 transition-colors",
                      isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                    )}
                  />
                  {!isCollapsed && (
                    <span className="flex-1 truncate">{item.name}</span>
                  )}
                  {!isCollapsed && item.badge && (
                    <span
                      className={cn(
                        "flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-bold",
                        isActive
                          ? "bg-white/20 text-white"
                          : "bg-slate-800 text-slate-300 border border-slate-700/80"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* System Section */}
          <div className="space-y-1">
            {!isCollapsed && (
              <div className="px-3 pb-1.5">
                <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  System
                </span>
              </div>
            )}
            {SYSTEM_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-medium transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30"
                      : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon
                    className={cn(
                      "h-[18px] w-[18px] shrink-0 transition-colors",
                      isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                    )}
                  />
                  {!isCollapsed && (
                    <span className="flex-1 truncate">{item.name}</span>
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* ── Agent Swarm Widget (Matches screenshot) ── */}
        <div className="p-3 border-t border-white/[0.05]">
          {!isCollapsed ? (
            <div className="rounded-2xl border border-white/[0.06] bg-[#0c1222]/80 p-3 shadow-inner">
              {/* Header */}
              <div className="flex items-center gap-2 mb-2.5 px-0.5">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
                </span>
                <span className="text-[11.5px] font-bold text-white tracking-tight">
                  Agent Swarm
                </span>
                <span className="ml-auto text-[10px] font-semibold text-emerald-400">
                  18 Agents Online
                </span>
              </div>

              {/* Agent list */}
              <div className="space-y-1.5">
                {SWARM_AGENTS.map((agent) => {
                  const AgentIcon = agent.icon;
                  return (
                    <div
                      key={agent.name}
                      className="flex items-center justify-between rounded-lg px-2 py-1 hover:bg-white/[0.03] transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <div
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded bg-gradient-to-tr text-white",
                            agent.color
                          )}
                        >
                          <AgentIcon className="h-2.5 w-2.5" />
                        </div>
                        <span className="text-[11px] text-slate-300 truncate">
                          {agent.name}
                        </span>
                      </div>
                      <span className="text-[10px] font-medium text-emerald-400">
                        {agent.status}
                      </span>
                    </div>
                  );
                })}

                {/* +14 more agents */}
                <div className="flex items-center justify-between rounded-lg px-2 py-1 text-slate-400 hover:text-slate-300 transition-colors">
                  <div className="flex items-center gap-2">
                    <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded bg-slate-800 text-slate-400">
                      <Plus className="h-2.5 w-2.5" />
                    </div>
                    <span className="text-[11px] text-slate-400">
                      +14 more agents
                    </span>
                  </div>
                  <span className="text-[10px] font-medium text-emerald-400">
                    Online
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex justify-center py-2" title="18 Agents Online">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-400" />
              </span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
