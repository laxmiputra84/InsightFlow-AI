import React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
}

export function Input({ className, icon, ...props }: InputProps) {
  if (icon) {
    return (
      <div className="relative flex items-center w-full">
        <div className="absolute left-3.5 text-slate-500 pointer-events-none flex items-center justify-center">
          {icon}
        </div>
        <input
          className={cn(
            "w-full rounded-xl border border-white/[0.06] bg-[var(--surface-1)] py-2.5 pl-10 pr-4 text-[13px] text-slate-100 placeholder:text-slate-600 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition-all duration-200",
            className
          )}
          {...props}
        />
      </div>
    );
  }

  return (
    <input
      className={cn(
        "w-full rounded-xl border border-white/[0.06] bg-[var(--surface-1)] px-3.5 py-2.5 text-[13px] text-slate-100 placeholder:text-slate-600 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition-all duration-200",
        className
      )}
      {...props}
    />
  );
}
