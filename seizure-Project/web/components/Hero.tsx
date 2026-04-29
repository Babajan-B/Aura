"use client";

import { motion } from "framer-motion";

// Pre-computed at module level — identical on server and client, no hydration mismatch.
const BRAIN_TICKS = Array.from({ length: 36 }, (_, i) => {
  const a = (i * 10 * Math.PI) / 180;
  const c = Math.cos(a), s = Math.sin(a);
  const r2 = i % 3 === 0 ? 152 : 148;
  return {
    x1: Math.round((160 + c * 145) * 1e4) / 1e4,
    y1: Math.round((160 + s * 145) * 1e4) / 1e4,
    x2: Math.round((160 + c * r2)  * 1e4) / 1e4,
    y2: Math.round((160 + s * r2)  * 1e4) / 1e4,
  };
});
import { Brain, Cpu, Activity, Zap } from "lucide-react";
import { StatCard } from "./StatCard";

export function Hero() {
  return (
    <section
      id="hero"
      className="relative min-h-[92vh] pt-24 pb-16 px-6 md:px-10 max-w-7xl mx-auto"
    >
      <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-12 items-center">
        {/* Left: copy */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 rounded-full border border-neon-cyan/30 bg-neon-cyan/5 px-3 py-1 mb-5"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-cyan opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-neon-cyan" />
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-neon-cyan">
              On-Device · Wear OS · RGF-Net
            </span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white leading-[1.05]">
            Aura <span className="neon-text text-neon-cyan">Watch</span>
            <br />
            <span className="text-slate-300 text-3xl md:text-5xl font-medium">
              Pre-Ictal Guardian
            </span>
          </h1>

          <p className="mt-6 max-w-xl text-slate-400 text-base md:text-lg leading-relaxed">
            A neural sentinel on your wrist. Streams 19-channel EEG at 256 Hz,
            fuses 6 biometrics, and predicts the pre-ictal window before a
            seizure strikes — entirely on-device, entirely private.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#monitor"
              className="rounded-md border border-neon-cyan/50 bg-neon-cyan/10 px-5 py-2.5 font-mono text-xs uppercase tracking-widest text-neon-cyan hover:bg-neon-cyan/20 hover:shadow-neon transition-all"
            >
              Open Live Monitor
            </a>
            <a
              href="#simulator"
              className="rounded-md border border-slate-700 px-5 py-2.5 font-mono text-xs uppercase tracking-widest text-slate-300 hover:text-white hover:border-slate-500 transition-all"
            >
              Run Inference
            </a>
          </div>
        </motion.div>

        {/* Right: brain SVG */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.2 }}
          className="relative flex items-center justify-center"
        >
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_center,rgba(0,255,209,0.18),transparent_60%)] blur-2xl" />
          <BrainSVG />
        </motion.div>
      </div>

      {/* Stats row */}
      <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Parameters"
          value={37554}
          formatter={(n) => Math.round(n).toLocaleString()}
          accent="cyan"
          icon={<Cpu size={16} />}
        />
        <StatCard
          label="Model Size"
          value={36.7}
          unit="KB"
          decimals={1}
          accent="violet"
          icon={<Brain size={16} />}
        />
        <StatCard
          label="Latency"
          value={500}
          unit="ms"
          formatter={(n) => `<${Math.round(n)}`}
          accent="amber"
          icon={<Zap size={16} />}
        />
        <StatCard
          label="Sensitivity"
          value={90}
          unit="%+"
          accent="pink"
          icon={<Activity size={16} />}
        />
      </div>
    </section>
  );
}

function BrainSVG() {
  return (
    <motion.svg
      viewBox="0 0 320 320"
      className="w-72 h-72 md:w-96 md:h-96"
      initial={{ rotate: -3 }}
      animate={{ rotate: [-3, 3, -3] }}
      transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
    >
      <defs>
        <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#00ffd1" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#00ffd1" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="brainStroke" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00ffd1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>

      <circle cx="160" cy="160" r="140" fill="url(#bgGlow)" />

      <motion.g
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        style={{ transformOrigin: "160px 160px" }}
      >
        {/* Stylized brain hemispheres */}
        <path
          d="M160 60 C 110 60, 70 100, 80 150 C 60 160, 60 200, 90 220 C 100 250, 140 260, 160 250 C 180 260, 220 250, 230 220 C 260 200, 260 160, 240 150 C 250 100, 210 60, 160 60 Z"
          fill="none"
          stroke="url(#brainStroke)"
          strokeWidth="2.2"
        />
        <path
          d="M160 70 L 160 250"
          stroke="rgba(0,255,209,0.35)"
          strokeWidth="1.4"
          strokeDasharray="3 4"
        />
        <path
          d="M100 130 C 130 110, 150 130, 160 150"
          stroke="#00ffd1"
          strokeWidth="1.4"
          fill="none"
        />
        <path
          d="M220 130 C 190 110, 170 130, 160 150"
          stroke="#00ffd1"
          strokeWidth="1.4"
          fill="none"
        />
        <path
          d="M95 180 C 130 195, 150 175, 160 195"
          stroke="#8b5cf6"
          strokeWidth="1.4"
          fill="none"
        />
        <path
          d="M225 180 C 190 195, 170 175, 160 195"
          stroke="#8b5cf6"
          strokeWidth="1.4"
          fill="none"
        />
      </motion.g>

      {/* electrodes */}
      {[
        [80, 150],
        [160, 70],
        [240, 150],
        [120, 230],
        [200, 230],
        [160, 250],
      ].map(([x, y], i) => (
        <motion.circle
          key={i}
          cx={x}
          cy={y}
          r={4}
          fill="#00ffd1"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{
            duration: 1.6,
            delay: i * 0.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* outer ring ticks */}
      <g stroke="#00ffd1" strokeOpacity="0.4">
        {BRAIN_TICKS.map((t, i) => (
          <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} />
        ))}
      </g>
    </motion.svg>
  );
}
