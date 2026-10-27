import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const variantStyles = {
    primary:
      "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/15 active:scale-[0.98] border border-indigo-500/30 hover:shadow-lg hover:shadow-indigo-600/20",
    secondary:
      "bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-slate-100 border border-white/[0.06] active:scale-[0.98]",
    outline:
      "border border-white/[0.08] hover:border-white/[0.12] text-slate-300 hover:text-white hover:bg-white/[0.03]",
    ghost:
      "text-slate-400 hover:text-slate-100 hover:bg-white/[0.04]",
    danger:
      "bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/15 border border-rose-500/30 active:scale-[0.98]",
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-[12px] rounded-lg gap-1.5",
    md: "px-4 py-2 text-[13px] rounded-xl gap-2",
    lg: "px-5 py-2.5 text-sm rounded-xl gap-2.5 font-semibold",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 select-none focus-visible:outline-2 focus-visible:outline-indigo-500/50 focus-visible:outline-offset-2",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="h-4 w-4 animate-spin text-current" />}
      {children}
    </button>
  );
}
