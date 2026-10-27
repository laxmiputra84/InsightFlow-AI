import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.06] bg-[var(--surface-0)]/50 p-12 text-center",
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/8 text-indigo-400 border border-indigo-500/15 mb-5">
        <Icon className="h-7 w-7" />
      </div>
      <h4 className="text-[15px] font-bold text-slate-200">{title}</h4>
      <p className="mt-2 max-w-sm text-[12px] text-slate-500 leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
