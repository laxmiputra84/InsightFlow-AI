import React from "react";
import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-white/[0.04] border border-white/[0.03]",
        className
      )}
      {...props}
    />
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/[0.05] bg-[var(--card)] p-5 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-9 w-9 rounded-xl" />
      </div>
      <Skeleton className="h-8 w-32 mt-2" />
      <div className="flex items-center gap-2.5 pt-1">
        <Skeleton className="h-5 w-14 rounded-lg" />
        <Skeleton className="h-3 w-24" />
      </div>
      <Skeleton className="h-12 w-full rounded-xl mt-2" />
    </div>
  );
}

export function AgentCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/[0.05] bg-[var(--card)] p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="h-11 w-11 rounded-xl" />
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-3 w-40" />
          </div>
        </div>
        <Skeleton className="h-5 w-14 rounded-lg" />
      </div>
      <Skeleton className="h-10 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-16 rounded-md" />
        <Skeleton className="h-5 w-20 rounded-md" />
        <Skeleton className="h-5 w-14 rounded-md" />
      </div>
      <div className="pt-3 border-t border-white/[0.04] flex justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-28" />
      </div>
    </div>
  );
}
