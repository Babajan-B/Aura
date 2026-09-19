"use client";

import { useEffect, useRef, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface Point {
  t: number;
  c1: number;
  c2: number;
  c3: number;
  c4: number;
}

const WINDOW = 80;
const CHANNELS = [
  { key: "c1", color: "#00ffd1", name: "Fp1" },
  { key: "c2", color: "#8b5cf6", name: "Cz" },
  { key: "c3", color: "#fbbf24", name: "T7" },
  { key: "c4", color: "#ff2e6c", name: "O1" },
] as const;

export function EEGWaveform() {
  const [data, setData] = useState<Point[]>(() => seed());
  const tickRef = useRef(WINDOW);

  useEffect(() => {
    const id = setInterval(() => {
      tickRef.current += 1;
      const t = tickRef.current;
      const next: Point = {
        t,
        c1: Math.sin(t / 4) * 0.6 + Math.sin(t / 1.2) * 0.25 + jitter(),
        c2: Math.cos(t / 5) * 0.7 + Math.sin(t / 0.9) * 0.2 + jitter(),
        c3: Math.sin(t / 3.2 + 1.3) * 0.55 + Math.cos(t / 1.6) * 0.3 + jitter(),
        c4: Math.cos(t / 4.5 + 0.7) * 0.65 + Math.sin(t / 1.1) * 0.22 + jitter(),
      };
      setData((prev) => [...prev.slice(1), next]);
    }, 90);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="glass p-4 md:p-6 relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-cyan/80">
            Live EEG Stream · 256 Hz · 19ch
          </div>
          <div className="text-white text-lg font-medium mt-1">
            Cortical Activity Monitor
          </div>
        </div>
        <div className="flex gap-3">
          {CHANNELS.map((c) => (
            <div key={c.key} className="flex items-center gap-1.5">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: c.color, boxShadow: `0 0 8px ${c.color}` }}
              />
              <span className="font-mono text-[10px] text-slate-400">{c.name}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: -28 }}>
            <defs>
              {CHANNELS.map((c) => (
                <linearGradient key={c.key} id={`g-${c.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={c.color} stopOpacity={0.5} />
                  <stop offset="100%" stopColor={c.color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.08)" vertical={false} />
            <XAxis
              dataKey="t"
              stroke="rgba(148,163,184,0.4)"
              tick={{ fontSize: 10, fontFamily: "ui-monospace" }}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="rgba(148,163,184,0.4)"
              tick={{ fontSize: 10, fontFamily: "ui-monospace" }}
              domain={[-1.6, 1.6]}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(2,6,23,0.95)",
                border: "1px solid rgba(0,255,209,0.3)",
                fontFamily: "ui-monospace",
                fontSize: 11,
              }}
              labelStyle={{ color: "#00ffd1" }}
            />
            {CHANNELS.map((c) => (
              <Area
                key={c.key}
                type="monotone"
                dataKey={c.key}
                stroke={c.color}
                strokeWidth={1.6}
                fill={`url(#g-${c.key})`}
                isAnimationActive={false}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function seed(): Point[] {
  const arr: Point[] = [];
  for (let t = 0; t < WINDOW; t++) {
    arr.push({
      t,
      c1: Math.sin(t / 4) * 0.6,
      c2: Math.cos(t / 5) * 0.7,
      c3: Math.sin(t / 3.2 + 1.3) * 0.55,
      c4: Math.cos(t / 4.5 + 0.7) * 0.65,
    });
  }
  return arr;
}

function jitter() {
  return (Math.random() - 0.5) * 0.12;
}
