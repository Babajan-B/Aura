"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

type Variant = "cyan" | "pink" | "amber" | "ghost";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md";
}

const variantStyles: Record<Variant, string> = {
  cyan:
    "border-neon-cyan/40 text-neon-cyan hover:bg-neon-cyan/10 hover:shadow-neon hover:border-neon-cyan",
  pink:
    "border-neon-pink/40 text-neon-pink hover:bg-neon-pink/10 hover:shadow-neonPink hover:border-neon-pink",
  amber:
    "border-neon-amber/40 text-neon-amber hover:bg-neon-amber/10 hover:border-neon-amber",
  ghost:
    "border-slate-700 text-slate-300 hover:bg-slate-800/60 hover:text-white",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "cyan", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center gap-2 rounded-md border bg-slate-950/40 font-mono uppercase tracking-wider transition-all duration-200",
          "active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none",
          size === "sm" ? "px-3 py-1.5 text-[11px]" : "px-4 py-2 text-xs",
          variantStyles[variant],
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
