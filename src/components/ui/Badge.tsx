import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "info" | "outline" | "purple";
  size?: "sm" | "md";
}

export function Badge({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-slate-800/50 text-slate-300 border-white/[0.06]",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    danger: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    info: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    purple: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    outline: "border-white/[0.08] text-slate-300 bg-transparent",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] font-bold",
    md: "px-2.5 py-1 text-[11px] font-bold",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border transition-colors uppercase tracking-wider",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
