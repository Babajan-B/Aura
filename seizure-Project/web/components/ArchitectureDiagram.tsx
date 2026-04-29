"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Brain, Cpu, Sparkles } from "lucide-react";
import { cn } from "@/lib/cn";

type Selected = "teacher" | "student" | null;

const details: Record<Exclude<Selected, null>, { title: string; bullets: string[] }> = {
  teacher: {
    title: "Teacher · Transformer (661K params)",
    bullets: [
      "Multi-head attention over 19-channel EEG patches",
      "Trained on TUSZ + CHB-MIT + Siena (95k+ windows)",
      "Used only at training time — never ships to device",
      "Provides soft-label distribution for KD loss",
    ],
  },
  student: {
    title: "Student · RGF-Net (37,554 params)",
    bullets: [
      "Depthwise-separable temporal conv + lightweight GRU head",
      "Fuses 6 biometrics via tiny MLP (age, sex, hr, hrv, hrs, adherence)",
      "INT8 quantized → 36.7 KB model file",
      "<500ms inference on Wear OS @ 256 Hz, 5s window",
    ],
  },
};

export function ArchitectureDiagram() {
  const [sel, setSel] = useState<Selected>(null);

  return (
    <div className="glass p-6 md:p-8">
      <div className="grid md:grid-cols-[1fr_auto_1fr] gap-6 items-stretch">
        <ArchBox
          label="Teacher"
          subtitle="Transformer · 661K params"
          icon={<Brain size={22} />}
          accent="violet"
          active={sel === "teacher"}
          onClick={() => setSel(sel === "teacher" ? null : "teacher")}
        />

        <KDArrow />

        <ArchBox
          label="Student"
          subtitle="RGF-Net · 37,554 params"
          icon={<Cpu size={22} />}
          accent="cyan"
          active={sel === "student"}
          onClick={() => setSel(sel === "student" ? null : "student")}
        />
      </div>

      <AnimatePresence mode="wait">
        {sel && (
          <motion.div
            key={sel}
            initial={{ opacity: 0, y: 12, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden mt-6"
          >
            <div className="glass-inner p-5">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-neon-cyan" />
                <h4 className="text-white font-medium">{details[sel].title}</h4>
              </div>
              <ul className="grid md:grid-cols-2 gap-2">
                {details[sel].bullets.map((b) => (
                  <li
                    key={b}
                    className="text-slate-400 text-sm flex items-start gap-2 font-mono"
                  >
                    <span className="text-neon-cyan mt-1">›</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <p className="mt-5 text-center font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500">
        Click a box to inspect — Knowledge distillation pipeline
      </p>
    </div>
  );
}

interface BoxProps {
  label: string;
  subtitle: string;
  icon: React.ReactNode;
  accent: "violet" | "cyan";
  active: boolean;
  onClick: () => void;
}

function ArchBox({ label, subtitle, icon, accent, active, onClick }: BoxProps) {
  const accentClasses =
    accent === "cyan"
      ? "border-neon-cyan/40 text-neon-cyan"
      : "border-neon-violet/40 text-neon-violet";
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative rounded-xl border-2 p-6 text-left transition-all bg-slate-950/60",
        accentClasses,
        active && "shadow-neon ring-2 ring-current/30"
      )}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-current/10">{icon}</div>
        <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-400">
          {label}
        </span>
      </div>
      <div className="text-white font-medium text-lg">{subtitle}</div>
      <div className="mt-3 text-xs text-slate-500 font-mono">
        {active ? "▼ collapse" : "▸ expand details"}
      </div>
    </motion.button>
  );
}

function KDArrow() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-[120px] px-2">
      <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-cyan/80 mb-2">
        KD Loss
      </div>
      <svg viewBox="0 0 200 60" className="w-full max-w-[200px]">
        <defs>
          <linearGradient id="arrG" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#00ffd1" />
          </linearGradient>
        </defs>
        <line
          x1="6"
          y1="30"
          x2="194"
          y2="30"
          stroke="url(#arrG)"
          strokeWidth="2"
        />
        <polygon points="194,30 184,24 184,36" fill="#00ffd1" />
        {/* particles */}
        {[0, 1, 2, 3].map((i) => (
          <motion.circle
            key={i}
            cx="0"
            cy="30"
            r="3"
            fill="#00ffd1"
            initial={{ cx: 6, opacity: 0 }}
            animate={{ cx: [6, 184, 184], opacity: [0, 1, 0] }}
            transition={{
              duration: 2.4,
              delay: i * 0.55,
              repeat: Infinity,
              ease: "linear",
            }}
            style={{ filter: "drop-shadow(0 0 6px #00ffd1)" }}
          />
        ))}
      </svg>
      <div className="mt-1 font-mono text-[9px] tracking-widest text-slate-500">
        soft labels · T=4
      </div>
    </div>
  );
}
