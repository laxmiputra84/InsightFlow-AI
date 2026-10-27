"use client";

import React from "react";
import {
  DollarSign,
  ShoppingCart,
  Users,
  BarChart3,
  TrendingUp,
  ArrowUp,
  ArrowDown,
  Sparkles,
} from "lucide-react";
import { KpiMetric } from "@/types";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  metric: KpiMetric;
  className?: string;
}

const THEMES: Record<
  string,
  {
    iconBg: string;
    iconColor: string;
    pillBg: string;
    pillText: string;
    waveStroke: string;
    glowColor: string;
    defaultIcon: React.ReactNode;
  }
> = {
  total_revenue: {
    iconBg: "bg-emerald-500/15 border-emerald-500/30",
    iconColor: "text-emerald-400",
    pillBg: "bg-emerald-500/10 border-emerald-500/20",
    pillText: "text-emerald-400",
    waveStroke: "#10b981",
    glowColor: "rgba(16, 185, 129, 0.15)",
    defaultIcon: <DollarSign className="h-5 w-5" />,
  },
  total_orders: {
    iconBg: "bg-blue-500/15 border-blue-500/30",
    iconColor: "text-blue-400",
    pillBg: "bg-blue-500/10 border-blue-500/20",
    pillText: "text-blue-400",
    waveStroke: "#3b82f6",
    glowColor: "rgba(59, 130, 246, 0.15)",
    defaultIcon: <ShoppingCart className="h-5 w-5" />,
  },
  active_customers: {
    iconBg: "bg-purple-500/15 border-purple-500/30",
    iconColor: "text-purple-400",
    pillBg: "bg-purple-500/10 border-purple-500/20",
    pillText: "text-purple-400",
    waveStroke: "#a855f7",
    glowColor: "rgba(168, 85, 247, 0.15)",
    defaultIcon: <Users className="h-5 w-5" />,
  },
  growth_rate: {
    iconBg: "bg-amber-500/15 border-amber-500/30",
    iconColor: "text-amber-400",
    pillBg: "bg-amber-500/10 border-amber-500/20",
    pillText: "text-amber-400",
    waveStroke: "#f59e0b",
    glowColor: "rgba(245, 158, 11, 0.15)",
    defaultIcon: <BarChart3 className="h-5 w-5" />,
  },
};

export function KpiCard({ metric, className }: KpiCardProps) {
  const theme = THEMES[metric.id] || {
    iconBg: "bg-indigo-500/15 border-indigo-500/30",
    iconColor: "text-indigo-400",
    pillBg: "bg-indigo-500/10 border-indigo-500/20",
    pillText: "text-indigo-400",
    waveStroke: "#6366f1",
    glowColor: "rgba(99, 102, 241, 0.15)",
    defaultIcon: <Sparkles className="h-5 w-5" />,
  };

  const isPositive = metric.changePercent >= 0;

  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0c1222]/90 p-5 transition-all duration-300 hover:border-white/15 hover:shadow-xl hover:-translate-y-0.5",
        className
      )}
    >
      <div className="flex items-start gap-4">
        {/* Left Glowing Icon Box */}
        <div
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border shadow-lg transition-transform duration-300 group-hover:scale-105",
            theme.iconBg,
            theme.iconColor
          )}
        >
          {theme.defaultIcon}
        </div>

        {/* Metric Details */}
        <div className="flex-1 min-w-0">
          <div className="text-[12px] font-medium text-slate-400 tracking-tight">
            {metric.label}
          </div>
          <div className="mt-1 text-2xl font-bold tracking-tight text-white">
            {metric.value}
          </div>

          {/* Trend Pill + Period */}
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-semibold",
                theme.pillBg,
                theme.pillText
              )}
            >
              {isPositive ? (
                <ArrowUp className="h-3 w-3" />
              ) : (
                <ArrowDown className="h-3 w-3" />
              )}
              {isPositive ? `+${metric.changePercent}%` : `${metric.changePercent}%`}
            </span>
            <span className="text-[11px] text-slate-400 font-normal">
              vs previous period
            </span>
          </div>
        </div>
      </div>

      {/* Ambient bottom wave SVG */}
      <div className="absolute -bottom-1 left-0 right-0 h-10 pointer-events-none opacity-40 group-hover:opacity-75 transition-opacity duration-300 overflow-hidden">
        <svg
          viewBox="0 0 300 40"
          className="w-full h-full preserve-3d"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0 32C50 32 70 12 120 22C170 32 200 15 250 18C280 20 300 28 300 28V40H0V32Z"
            fill={`url(#grad-${metric.id})`}
            opacity="0.3"
          />
          <path
            d="M0 32C50 32 70 12 120 22C170 32 200 15 250 18C280 20 300 28 300 28"
            stroke={theme.waveStroke}
            strokeWidth="2"
            strokeLinecap="round"
          />
          <defs>
            <linearGradient id={`grad-${metric.id}`} x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
              <stop stopColor={theme.waveStroke} />
              <stop offset="1" stopColor="transparent" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
