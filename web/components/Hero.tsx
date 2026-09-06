"use client";

import { motion } from "framer-motion";
import { Activity, BarChart3, HeartPulse, ShieldCheck } from "lucide-react";
import { StatCard } from "./StatCard";

export function Hero() {
  return (
    <section id="hero" className="relative min-h-[88vh] pt-28 pb-16 px-6 md:px-10 max-w-7xl mx-auto">
      <div className="grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
          <div className="inline-flex items-center gap-2 rounded-md border border-neon-cyan/30 bg-neon-cyan/5 px-3 py-1 mb-5">
            <ShieldCheck size={14} className="text-neon-cyan" />
            <span className="font-mono text-[11px] uppercase tracking-widest text-neon-cyan">
              Research prototype · controlled demonstration
            </span>
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-white leading-[1.05]">
            Aura <span className="neon-text text-neon-cyan">Watch</span>
            <br />
            <span className="text-slate-300 text-3xl md:text-5xl font-medium">Wearable seizure-safety companion</span>
          </h1>
          <p className="mt-6 max-w-2xl text-slate-400 text-base md:text-lg leading-relaxed">
            A proposed watch-and-phone workflow that monitors wearable signals, demonstrates repeated-risk confirmation, gives the user a 15-second cancellation window, and can support caregiver alerts. The current applications use controlled simulated wearable inputs.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="#simulator" className="rounded-md border border-neon-cyan/50 bg-neon-cyan/10 px-5 py-2.5 font-mono text-xs uppercase tracking-widest text-neon-cyan hover:bg-neon-cyan/20 transition-colors">Open prototype demo</a>
            <a href="#validation" className="rounded-md border border-slate-700 px-5 py-2.5 font-mono text-xs uppercase tracking-widest text-slate-300 hover:text-white hover:border-slate-500 transition-colors">View validation</a>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8 }}>
          <div className="glass p-7 md:p-9">
            <div className="font-mono text-[10px] uppercase tracking-widest text-neon-cyan">Current evidence boundary</div>
            <div className="mt-4 space-y-5">
              <BoundaryRow icon={<BarChart3 size={20} />} title="Offline EEG model" text="Three signal-only models evaluated on a held-out set of 1,295 windows." />
              <BoundaryRow icon={<Activity size={20} />} title="Mobile and watch prototype" text="Interactive monitoring, risk display, countdown, cancellation and alert states." />
              <BoundaryRow icon={<HeartPulse size={20} />} title="Not yet integrated" text="A wearable model trained on synchronized IMU, PPG, temperature and seizure-event data is still required." />
            </div>
          </div>
        </motion.div>
      </div>
      <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Held-out windows" value={1295} formatter={(n) => Math.round(n).toLocaleString()} accent="cyan" icon={<Activity size={16} />} />
        <StatCard label="ROC-AUC" value={0.932} decimals={3} accent="violet" icon={<BarChart3 size={16} />} />
        <StatCard label="Sensitivity" value={94.3} unit="%" decimals={1} accent="amber" icon={<HeartPulse size={16} />} />
        <StatCard label="Specificity" value={73.7} unit="%" decimals={1} accent="pink" icon={<ShieldCheck size={16} />} />
      </div>
    </section>
  );
}

function BoundaryRow({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <div className="flex gap-3 border-b border-slate-800 pb-5 last:border-0 last:pb-0"><div className="mt-0.5 text-neon-cyan">{icon}</div><div><div className="font-medium text-white">{title}</div><p className="mt-1 text-sm leading-relaxed text-slate-400">{text}</p></div></div>;
}
