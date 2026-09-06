"use client";

import * as Slider from "@radix-ui/react-slider";
import { motion } from "framer-motion";
import { useState } from "react";
import { AlertTriangle, CheckCircle2, FlaskConical, Loader2 } from "lucide-react";
import { Button } from "./ui/Button";
import { cn } from "@/lib/cn";

interface Inputs { heartRate: number; movement: number; temperature: number; }
interface DemoResult { score: number; state: string; demo: boolean; disclaimer: string; }

export function InferenceSimulator() {
  const [inputs, setInputs] = useState<Inputs>({ heartRate: 76, movement: 20, temperature: 36.8 });
  const [repeatedPattern, setRepeatedPattern] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DemoResult | null>(null);

  const update = <K extends keyof Inputs>(key: K, value: number) => setInputs((previous) => ({ ...previous, [key]: value }));
  const run = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/infer", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...inputs, repeatedPattern }) });
      setResult((await response.json()) as DemoResult);
    } finally { setLoading(false); }
  };
  const isAlert = (result?.score ?? 0) >= 0.75;

  return <div className="glass p-6 md:p-8 grid md:grid-cols-2 gap-8">
    <div className="space-y-5">
      <div className="font-mono text-[10px] uppercase tracking-widest text-neon-cyan">Controlled wearable inputs</div>
      <SliderRow label="Heart rate" value={inputs.heartRate} min={40} max={180} step={1} unit="bpm" onValueChange={(v) => update("heartRate", v)} />
      <SliderRow label="Movement intensity" value={inputs.movement} min={0} max={100} step={1} unit="%" onValueChange={(v) => update("movement", v)} />
      <SliderRow label="Temperature" value={inputs.temperature} min={33} max={40} step={0.1} unit="°C" decimals={1} onValueChange={(v) => update("temperature", v)} />
      <label className="flex items-center justify-between rounded-md border border-neon-amber/30 bg-neon-amber/5 px-4 py-3 cursor-pointer">
        <span className="font-mono text-xs uppercase tracking-widest text-neon-amber">Repeat high-risk pattern</span>
        <input type="checkbox" checked={repeatedPattern} onChange={(event) => setRepeatedPattern(event.target.checked)} className="h-4 w-4 accent-amber-400" />
      </label>
      <Button variant="cyan" onClick={run} disabled={loading} className="w-full">{loading ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}{loading ? "Running demo…" : "Run controlled demo"}</Button>
      <p className="text-xs leading-relaxed text-slate-500">This deterministic demonstration exercises the interface and alert workflow. It does not run the offline EEG model and is not a medical prediction.</p>
    </div>
    <div className="glass-inner p-6 flex flex-col justify-center">
      <div className="font-mono text-[10px] uppercase tracking-widest text-neon-cyan">Demonstration result</div>
      {result ? <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-5">
        <div className="font-mono text-5xl text-white">{(result.score * 100).toFixed(1)}<span className="text-2xl text-slate-500">%</span></div>
        <div className="h-2.5 rounded-full bg-slate-800 overflow-hidden"><div className={cn("h-full rounded-full", isAlert ? "bg-neon-pink" : "bg-neon-cyan")} style={{ width: `${result.score * 100}%` }} /></div>
        <div className={cn("flex items-center gap-2 rounded-md border px-4 py-3", isAlert ? "border-neon-pink/50 bg-neon-pink/10 text-neon-pink" : "border-neon-green/40 bg-neon-green/5 text-neon-green")}>{isAlert ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}<span className="font-mono text-sm">{result.state}</span></div>
        <p className="text-sm text-slate-400">{result.disclaimer}</p>
      </motion.div> : <div className="mt-6 text-sm leading-relaxed text-slate-400">Adjust the controlled inputs and run the demonstration to view monitoring, elevated-risk and high-risk interface states.</div>}
    </div>
  </div>;
}

function SliderRow({ label, value, min, max, step, unit, decimals = 0, onValueChange }: { label: string; value: number; min: number; max: number; step: number; unit: string; decimals?: number; onValueChange: (value: number) => void }) {
  return <div><div className="flex items-baseline justify-between mb-2"><span className="font-mono text-[11px] uppercase tracking-widest text-slate-400">{label}</span><span className="font-mono text-sm text-neon-cyan">{value.toFixed(decimals)} <span className="text-xs text-slate-500">{unit}</span></span></div><Slider.Root className="relative flex h-5 w-full touch-none select-none items-center" value={[value]} min={min} max={max} step={step} onValueChange={(next) => onValueChange(next[0])}><Slider.Track className="relative h-1 w-full grow rounded-full bg-slate-800"><Slider.Range className="absolute h-full rounded-full bg-neon-cyan" /></Slider.Track><Slider.Thumb className="block h-4 w-4 rounded-full border-2 border-neon-cyan bg-slate-950" aria-label={label} /></Slider.Root></div>;
}
