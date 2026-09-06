"use client";

import { motion, AnimatePresence } from "framer-motion";

// Pre-computed at module level — identical on server and client, no hydration mismatch.
const WATCH_TICKS = Array.from({ length: 60 }, (_, i) => {
  const a = (i * 6 * Math.PI) / 180;
  const c = Math.cos(a), s = Math.sin(a);
  const r1 = i % 5 === 0 ? 140 : 144;
  return {
    x1: Math.round((160 + c * r1)  * 1e4) / 1e4,
    y1: Math.round((160 + s * r1)  * 1e4) / 1e4,
    x2: Math.round((160 + c * 150) * 1e4) / 1e4,
    y2: Math.round((160 + s * 150) * 1e4) / 1e4,
    w:  i % 5 === 0 ? 1.5 : 0.7,
  };
});
import { useEffect, useState } from "react";
import { Heart, AlertTriangle, Watch } from "lucide-react";
import { Button } from "./ui/Button";

type Mode = "monitoring" | "alert" | "countdown";

export function WatchFace() {
  const [mode, setMode] = useState<Mode>("monitoring");
  const [count, setCount] = useState(15);

  useEffect(() => {
    if (mode !== "countdown") return;
    setCount(15);
    const id = setInterval(() => {
      setCount((c) => {
        if (c <= 1) {
          clearInterval(id);
          setMode("alert");
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [mode]);

  const ringColor =
    mode === "alert" ? "#ff2e6c" : mode === "countdown" ? "#fbbf24" : "#00ffd1";

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        {/* Watch outer body */}
        <div
          className="relative h-[340px] w-[340px] rounded-full p-3"
          style={{
            background:
              "conic-gradient(from 90deg, #1e293b, #0f172a, #1e293b, #0f172a, #1e293b)",
            boxShadow: `0 0 60px ${ringColor}33, inset 0 0 0 1px rgba(148,163,184,0.2)`,
          }}
        >
          <div className="relative h-full w-full rounded-full bg-slate-950 overflow-hidden">
            <svg viewBox="0 0 320 320" className="absolute inset-0 h-full w-full">
              {/* Outer tick ring */}
              <g stroke={ringColor} strokeOpacity="0.5">
                {WATCH_TICKS.map((t, i) => (
                  <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} strokeWidth={t.w} />
                ))}
              </g>

              {/* Countdown ring */}
              {mode === "countdown" && (
                <motion.circle
                  cx="160"
                  cy="160"
                  r="130"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 130}
                  initial={{ strokeDashoffset: 0 }}
                  animate={{ strokeDashoffset: 2 * Math.PI * 130 }}
                  transition={{ duration: 15, ease: "linear" }}
                  transform="rotate(-90 160 160)"
                  style={{ filter: "drop-shadow(0 0 10px #fbbf24)" }}
                />
              )}
            </svg>

            {/* Background flash for alert */}
            {mode === "alert" && (
              <motion.div
                className="absolute inset-4 rounded-full"
                animate={{ opacity: [0.25, 0.55, 0.25] }}
                transition={{ duration: 0.9, repeat: Infinity }}
                style={{ background: "radial-gradient(circle, #ff2e6c, transparent 70%)" }}
              />
            )}

            {/* Face content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8">
              <AnimatePresence mode="wait">
                {mode === "monitoring" && (
                  <motion.div
                    key="m"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center"
                  >
                    <motion.div
                      animate={{ scale: [1, 1.18, 1] }}
                      transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                    >
                      <Heart size={44} className="text-neon-cyan" fill="currentColor" />
                    </motion.div>
                    <div className="mt-4 font-mono text-xs uppercase tracking-[0.3em] text-neon-cyan">
                      Demo monitoring
                    </div>
                    <div className="mt-1 font-mono text-3xl text-white">72 BPM</div>
                    <div className="mt-3 text-[10px] font-mono text-slate-400">
                      Controlled input · stable
                    </div>
                  </motion.div>
                )}

                {mode === "countdown" && (
                  <motion.div
                    key="c"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center"
                  >
                    <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-amber">
                      Demo High-Risk State
                    </div>
                    <div className="mt-2 font-mono text-7xl text-white tabular-nums">
                      {count}
                    </div>
                    <div className="mt-1 text-[11px] text-slate-400">
                      Alerting caregiver in
                    </div>
                  </motion.div>
                )}

                {mode === "alert" && (
                  <motion.div
                    key="a"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center"
                  >
                    <motion.div
                      animate={{ scale: [1, 1.15, 1] }}
                      transition={{ duration: 0.7, repeat: Infinity }}
                    >
                      <AlertTriangle size={52} className="text-neon-pink" />
                    </motion.div>
                    <div className="mt-3 font-mono text-base uppercase tracking-[0.3em] text-neon-pink neon-text-pink">
                      Demo Alert State
                    </div>
                    <div className="mt-2 text-[11px] text-slate-300">
                      Proposed caregiver escalation
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Crown */}
        <div className="absolute -right-1 top-1/2 h-10 w-2 -translate-y-1/2 rounded-r bg-slate-700" />
      </div>

      {mode === "countdown" && (
        <Button variant="amber" onClick={() => setMode("monitoring")}>
          Cancel Alert
        </Button>
      )}

      <div className="flex flex-wrap gap-2 justify-center">
        <Button variant="cyan" onClick={() => setMode("monitoring")}>
          <Watch size={14} /> Monitor
        </Button>
        <Button variant="amber" onClick={() => setMode("countdown")}>
          Start Countdown
        </Button>
        <Button variant="pink" onClick={() => setMode("alert")}>
          Show Alert
        </Button>
      </div>
    </div>
  );
}
