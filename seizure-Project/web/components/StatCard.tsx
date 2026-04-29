"use client";

import { motion, useInView, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";

interface StatCardProps {
  label: string;
  value: number;
  unit?: string;
  decimals?: number;
  formatter?: (n: number) => string;
  accent?: "cyan" | "pink" | "amber" | "violet";
  icon?: React.ReactNode;
}

const accentMap = {
  cyan: "text-neon-cyan border-neon-cyan/30",
  pink: "text-neon-pink border-neon-pink/30",
  amber: "text-neon-amber border-neon-amber/30",
  violet: "text-neon-violet border-neon-violet/30",
} as const;

export function StatCard({
  label,
  value,
  unit,
  decimals = 0,
  formatter,
  accent = "cyan",
  icon,
}: StatCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const count = useMotionValue(0);
  const display = useTransform(count, (latest) => {
    if (formatter) return formatter(latest);
    return latest.toFixed(decimals);
  });

  useEffect(() => {
    if (inView) {
      const controls = animate(count, value, {
        duration: 1.6,
        ease: "easeOut",
      });
      return () => controls.stop();
    }
  }, [inView, value, count]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className={cn(
        "glass relative overflow-hidden p-5 group",
        "hover:border-neon-cyan/40 transition-colors"
      )}
    >
      <div className="scanline absolute inset-0 opacity-20" />
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.28em] text-slate-400">
          {label}
        </span>
        {icon && <span className={cn("opacity-80", accentMap[accent])}>{icon}</span>}
      </div>
      <div className="flex items-baseline gap-1.5">
        <motion.span
          className={cn(
            "font-mono text-3xl md:text-4xl font-semibold neon-text",
            accentMap[accent].split(" ")[0]
          )}
        >
          {display}
        </motion.span>
        {unit && (
          <span className="text-slate-400 text-sm font-mono">{unit}</span>
        )}
      </div>
      <div
        className={cn(
          "absolute -bottom-px left-4 right-4 h-px bg-gradient-to-r",
          accent === "cyan" && "from-transparent via-neon-cyan to-transparent",
          accent === "pink" && "from-transparent via-neon-pink to-transparent",
          accent === "amber" && "from-transparent via-neon-amber to-transparent",
          accent === "violet" && "from-transparent via-neon-violet to-transparent"
        )}
      />
    </motion.div>
  );
}
