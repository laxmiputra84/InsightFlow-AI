import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  variant?: "default" | "elevated" | "bordered";
}

export function Card({ className, interactive, variant = "default", children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/[0.05] bg-[var(--card)] p-5 backdrop-blur-sm transition-all duration-300",
        variant === "elevated" && "bg-[var(--card-elevated)] shadow-lg",
        variant === "bordered" && "border-white/[0.08]",
        interactive && "hover-lift hover:border-white/[0.08] cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-center justify-between pb-4 border-b border-white/[0.04]", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-[15px] font-bold tracking-tight text-white", className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-[12px] text-slate-500 leading-relaxed mt-0.5", className)} {...props}>
      {children}
    </p>
  );
}
