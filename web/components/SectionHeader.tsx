"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

interface SectionHeaderProps {
  kicker?: string;
  title: string;
  subtitle?: string;
  align?: "left" | "center";
  className?: string;
}

export function SectionHeader({
  kicker,
  title,
  subtitle,
  align = "left",
  className,
}: SectionHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn(
        "mb-10",
        align === "center" ? "text-center mx-auto max-w-2xl" : "",
        className
      )}
    >
      {kicker && (
        <div
          className={cn(
            "mb-3 font-mono text-[11px] uppercase tracking-[0.32em] text-neon-cyan/80",
            align === "center" ? "justify-center" : "",
            "flex items-center gap-2"
          )}
        >
          <span className="inline-block h-px w-8 bg-neon-cyan/60" />
          {kicker}
        </div>
      )}
      <h2 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
        {title}
        <span className="ml-2 inline-block h-2 w-2 rounded-full bg-neon-cyan shadow-neon align-middle" />
      </h2>
      {subtitle && (
        <p className="mt-3 text-slate-400 text-sm md:text-base max-w-2xl">
          {subtitle}
        </p>
      )}
      <div className="mt-4 h-px w-24 bg-gradient-to-r from-neon-cyan via-neon-violet to-transparent" />
    </motion.div>
  );
}
