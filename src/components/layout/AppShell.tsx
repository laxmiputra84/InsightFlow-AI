"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { DateRange } from "@/types";

interface AppShellProps {
  children: React.ReactNode;
  selectedRange?: DateRange;
  onRangeChange?: (range: DateRange) => void;
}

export function AppShell({
  children,
  selectedRange,
  onRangeChange,
}: AppShellProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#070b16] text-slate-200 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Sidebar */}
      <Sidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          isCollapsed ? "lg:pl-[76px]" : "lg:pl-[260px]"
        }`}
      >
        <Header
          onOpenMobileSidebar={() => setMobileOpen(true)}
          selectedRange={selectedRange}
          onRangeChange={onRangeChange}
        />
        <main className="flex-1 w-full max-w-[1800px] mx-auto p-4 sm:p-6 lg:p-7 space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}
