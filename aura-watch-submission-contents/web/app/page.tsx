"use client";

import { motion } from "framer-motion";
import { Brain, Activity, Watch, Cpu, Zap, AlertTriangle } from "lucide-react";
import { Hero } from "@/components/Hero";
import { EEGWaveform } from "@/components/EEGWaveform";
import { RiskGauge } from "@/components/RiskGauge";
import { ArchitectureDiagram } from "@/components/ArchitectureDiagram";
import { WatchFace } from "@/components/WatchFace";
import { InferenceSimulator } from "@/components/InferenceSimulator";
import { FootprintChart } from "@/components/FootprintChart";
import { NeuralBackground } from "@/components/NeuralBackground";
import { SectionHeader } from "@/components/SectionHeader";
import { useState } from "react";

const navItems = [
  { id: "monitor", label: "Monitor", icon: Activity },
  { id: "architecture", label: "Architecture", icon: Brain },
  { id: "watch", label: "Watch", icon: Watch },
  { id: "simulator", label: "Simulator", icon: Zap },
  { id: "footprint", label: "Footprint", icon: Cpu },
];

export default function Page() {
  const [demoRisk, setDemoRisk] = useState(0.32);

  return (
    <main className="relative min-h-screen text-slate-200">
      <NeuralBackground />

      {/* Top nav */}
      <header className="fixed top-0 inset-x-0 z-40 backdrop-blur-md bg-slate-950/40 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-6 md:px-10 py-3 flex items-center justify-between">
          <a href="#hero" className="flex items-center gap-2">
            <div className="relative h-7 w-7">
              <div className="absolute inset-0 rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet shadow-neon" />
              <div className="absolute inset-[3px] rounded bg-slate-950 flex items-center justify-center">
                <Brain size={14} className="text-neon-cyan" />
              </div>
            </div>
            <span className="font-mono text-sm tracking-widest text-white">
              AURA<span className="text-neon-cyan">·</span>WATCH
            </span>
          </a>
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-widest text-slate-400 hover:text-neon-cyan hover:bg-neon-cyan/5 transition-colors"
              >
                <Icon size={12} />
                {label}
              </a>
            ))}
          </nav>
          <div className="hidden md:flex items-center gap-2 rounded-full border border-neon-green/30 bg-neon-green/5 px-3 py-1">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-green opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-neon-green" />
            </span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-neon-green">
              SYSTEM ONLINE
            </span>
          </div>
        </div>
      </header>

      <Hero />

      {/* MONITOR */}
      <section id="monitor" className="relative py-20 px-6 md:px-10 max-w-7xl mx-auto">
        <SectionHeader
          kicker="Section 01 · Live Monitor"
          title="Cortical Telemetry"
          subtitle="Realtime EEG and pre-ictal risk fused into a single neural dashboard."
        />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="grid lg:grid-cols-[1.7fr_1fr] gap-6"
        >
          <EEGWaveform />
          <div className="glass p-6 flex flex-col items-center justify-center gap-4">
            <RiskGauge value={demoRisk} />
            <div className="flex gap-2">
              {[0.18, 0.45, 0.82].map((v) => (
                <button
                  key={v}
                  onClick={() => setDemoRisk(v)}
                  className="rounded-md border border-slate-700 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-slate-300 hover:border-neon-cyan hover:text-neon-cyan transition-colors"
                >
                  {v < 0.4 ? "stable" : v < 0.75 ? "elevated" : "alert"}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* ARCHITECTURE */}
      <section id="architecture" className="relative py-20 px-6 md:px-10 max-w-7xl mx-auto">
        <SectionHeader
          kicker="Section 02 · Architecture"
          title="Knowledge Distillation"
          subtitle="A Transformer teacher (661K) compresses its understanding into a tiny 37.5K student that lives on the watch."
        />
        <ArchitectureDiagram />
      </section>

      {/* WATCH */}
      <section id="watch" className="relative py-20 px-6 md:px-10 max-w-7xl mx-auto">
        <SectionHeader
          kicker="Section 03 · Wearable"
          title="On-Wrist Experience"
          subtitle="Three states, one mission: detect, warn, alert. All offline."
        />
        <div className="grid lg:grid-cols-[auto_1fr] gap-12 items-center">
          <WatchFace />
          <div className="space-y-4 max-w-md">
            {[
              {
                icon: Activity,
                color: "text-neon-cyan",
                title: "Monitoring",
                desc: "Continuous 5-second EEG windows + biometrics evaluated every 1s on-device.",
              },
              {
                icon: AlertTriangle,
                color: "text-neon-amber",
                title: "Pre-Ictal Countdown",
                desc: "Risk crosses 0.75 → 15s window for the user to cancel a false positive before caregiver alert.",
              },
              {
                icon: Watch,
                color: "text-neon-pink",
                title: "Alert",
                desc: "Caregiver SMS + GPS location dispatched. Local vibration + audio cue to bystanders.",
              },
            ].map(({ icon: Icon, color, title, desc }) => (
              <div key={title} className="glass-inner p-4 flex gap-3">
                <Icon className={`${color} mt-0.5 shrink-0`} size={20} />
                <div>
                  <div className="text-white font-medium">{title}</div>
                  <div className="text-slate-400 text-sm mt-1">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SIMULATOR */}
      <section id="simulator" className="relative py-20 px-6 md:px-10 max-w-7xl mx-auto">
        <SectionHeader
          kicker="Section 04 · Inference"
          title="Try the Model"
          subtitle="POSTs to /api/infer — same heuristic shape as the deployed RGF-Net."
        />
        <InferenceSimulator />
      </section>

      {/* FOOTPRINT */}
      <section id="footprint" className="relative py-20 px-6 md:px-10 max-w-7xl mx-auto">
        <SectionHeader
          kicker="Section 05 · Footprint"
          title="Why It Fits on a Watch"
          subtitle="RGF-Net is over 13,000× smaller than GPT-2 small — and it runs in under half a second."
        />
        <FootprintChart />
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-8 px-6 md:px-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
            Aura Watch · Hackathon Build · {new Date().getFullYear()}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-slate-600">
            RGF-Net · 37,554 params · 36.7 KB · &lt;500ms · 90%+ sensitivity
          </div>
        </div>
      </footer>
    </main>
  );
}
