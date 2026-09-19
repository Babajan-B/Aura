"use client";

import * as Slider from "@radix-ui/react-slider";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Zap, AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "./ui/Button";
import { cn } from "@/lib/cn";

interface Inputs {
  age: number;
  sex: number;
  hr: number;
  hrv: number;
  hoursSinceSeizure: number;
  medicationAdherence: number;
}

interface InferResult {
  risk: number;
  label: string;
  latency_ms: number;
}

const defaults: Inputs = {
  age: 32,
  sex: 0,
  hr: 78,
  hrv: 48,
  hoursSinceSeizure: 24,
  medicationAdherence: 0.9,
};

export function InferenceSimulator() {
  const [inputs, setInputs] = useState<Inputs>(defaults);
  const [inject, setInject] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InferResult | null>(null);

  const update = <K extends keyof Inputs>(k: K, v: number) =>
    setInputs((p) => ({ ...p, [k]: v }));

  const run = async () => {
    setLoading(true);
    try {
      const r = await fetch("/api/infer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...inputs, injectSeizure: inject }),
      });
      const data = (await r.json()) as InferResult;
      setResult(data);
    } catch {
      setResult({ risk: 0, label: "ERROR", latency_ms: 0 });
    } finally {
      setLoading(false);
    }
  };

  const isAlert = (result?.risk ?? 0) >= 0.75;

  return (
    <div className="glass p-6 md:p-8 grid md:grid-cols-[1fr_1fr] gap-8">
      <div className="space-y-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-cyan/80">
          Biometric Inputs
        </div>

        <SliderRow label="Age" value={inputs.age} min={5} max={90} step={1}
          onValueChange={(v) => update("age", v)} unit="yr" />
        <SliderRow label="Sex (0 = F, 1 = M)" value={inputs.sex} min={0} max={1} step={1}
          onValueChange={(v) => update("sex", v)} />
        <SliderRow label="Heart Rate" value={inputs.hr} min={40} max={180} step={1}
          onValueChange={(v) => update("hr", v)} unit="bpm" warn={inputs.hr > 110} />
        <SliderRow label="HRV (RMSSD)" value={inputs.hrv} min={5} max={120} step={1}
          onValueChange={(v) => update("hrv", v)} unit="ms" warn={inputs.hrv < 30} />
        <SliderRow label="Hours Since Last Seizure" value={inputs.hoursSinceSeizure}
          min={0} max={168} step={1} onValueChange={(v) => update("hoursSinceSeizure", v)}
          unit="h" warn={inputs.hoursSinceSeizure < 6} />
        <SliderRow label="Medication Adherence" value={inputs.medicationAdherence}
          min={0} max={1} step={0.05} onValueChange={(v) => update("medicationAdherence", v)}
          decimals={2} warn={inputs.medicationAdherence < 0.5} />

        <label className="flex items-center justify-between rounded-lg border border-neon-pink/30 bg-neon-pink/5 px-4 py-3 cursor-pointer">
          <span className="font-mono text-xs text-neon-pink uppercase tracking-widest">
            Inject Seizure Pattern
          </span>
          <span
            className={cn(
              "relative h-5 w-10 rounded-full transition-colors",
              inject ? "bg-neon-pink" : "bg-slate-700"
            )}
            onClick={() => setInject((v) => !v)}
            role="switch"
            aria-checked={inject}
          >
            <motion.span
              className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow"
              animate={{ left: inject ? 22 : 2 }}
              transition={{ type: "spring", stiffness: 400, damping: 28 }}
            />
          </span>
          <input type="checkbox" hidden checked={inject}
            onChange={(e) => setInject(e.target.checked)} />
        </label>

        <Button variant="cyan" onClick={run} disabled={loading} className="w-full">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
          {loading ? "Running RGF-Net…" : "Run Inference"}
        </Button>
      </div>

      <div className="space-y-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-cyan/80">
          Inference Result
        </div>

        <AnimatePresence mode="wait">
          {result ? (
            <motion.div
              key={result.risk + "-" + result.latency_ms}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={cn(
                "glass-inner p-5 space-y-5",
                isAlert ? "border-neon-pink/40" : "border-neon-cyan/20"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="font-mono text-xs uppercase tracking-[0.3em] text-slate-400">
                  Pre-Ictal Risk
                </div>
                <div className="rounded-md border border-slate-700 bg-slate-900/60 px-2 py-1 font-mono text-[10px] text-neon-cyan">
                  {result.latency_ms} ms
                </div>
              </div>

              <div className="font-mono text-5xl text-white">
                {(result.risk * 100).toFixed(1)}
                <span className="text-2xl text-slate-500">%</span>
              </div>

              <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${result.risk * 100}%` }}
                  transition={{ duration: 0.7, ease: "easeOut" }}
                  className="h-full rounded-full"
                  style={{
                    background: isAlert
                      ? "linear-gradient(90deg, #fbbf24, #ff2e6c)"
                      : "linear-gradient(90deg, #22ee9b, #00ffd1)",
                    boxShadow: isAlert
                      ? "0 0 14px #ff2e6c"
                      : "0 0 14px #00ffd1",
                  }}
                />
              </div>

              <div
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-4 py-3",
                  isAlert
                    ? "border-neon-pink/50 bg-neon-pink/10 text-neon-pink"
                    : "border-neon-green/40 bg-neon-green/5 text-neon-green"
                )}
              >
                {isAlert ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
                <span className="font-mono text-sm tracking-wider">
                  {result.label}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1 text-[11px] font-mono text-slate-500">
                <div>Threshold · 0.75</div>
                <div className="text-right">RGF-Net · 37,554 params</div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass-inner p-8 text-center"
            >
              <div className="mx-auto mb-3 h-12 w-12 rounded-full border border-neon-cyan/30 flex items-center justify-center">
                <Zap size={20} className="text-neon-cyan" />
              </div>
              <p className="text-slate-400 text-sm">
                Adjust the biometrics on the left and run inference to see the
                model's prediction.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

interface SliderRowProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onValueChange: (v: number) => void;
  unit?: string;
  decimals?: number;
  warn?: boolean;
}

function SliderRow({
  label,
  value,
  min,
  max,
  step,
  onValueChange,
  unit,
  decimals = 0,
  warn,
}: SliderRowProps) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="font-mono text-[11px] uppercase tracking-widest text-slate-400">
          {label}
        </span>
        <span
          className={cn(
            "font-mono text-sm",
            warn ? "text-neon-pink" : "text-neon-cyan"
          )}
        >
          {value.toFixed(decimals)}
          {unit && <span className="text-slate-500 text-xs ml-1">{unit}</span>}
        </span>
      </div>
      <Slider.Root
        className="relative flex h-5 w-full touch-none select-none items-center"
        value={[value]}
        min={min}
        max={max}
        step={step}
        onValueChange={(v) => onValueChange(v[0])}
      >
        <Slider.Track className="relative h-1 w-full grow rounded-full bg-slate-800">
          <Slider.Range
            className={cn(
              "absolute h-full rounded-full",
              warn
                ? "bg-gradient-to-r from-neon-amber to-neon-pink"
                : "bg-gradient-to-r from-neon-violet to-neon-cyan"
            )}
          />
        </Slider.Track>
        <Slider.Thumb
          className={cn(
            "block h-4 w-4 rounded-full border-2 bg-slate-950 transition-shadow",
            warn
              ? "border-neon-pink shadow-neonPink"
              : "border-neon-cyan shadow-neon"
          )}
          aria-label={label}
        />
      </Slider.Root>
    </div>
  );
}
