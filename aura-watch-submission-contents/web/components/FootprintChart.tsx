"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Row {
  name: string;
  kb: number;
  highlight?: boolean;
  note: string;
}

const data: Row[] = [
  { name: "RGF-Net", kb: 37, highlight: true, note: "Aura Watch · on-device" },
  { name: "MobileNet v2", kb: 4 * 1024, note: "Mobile vision baseline" },
  { name: "BERT-base", kb: 440 * 1024, note: "NLP encoder" },
  { name: "GPT-2 small", kb: 500 * 1024, note: "Causal LM" },
];

function fmt(kb: number): string {
  if (kb < 1024) return `${kb} KB`;
  if (kb < 1024 * 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${(kb / 1024 / 1024).toFixed(1)} GB`;
}

export function FootprintChart() {
  return (
    <div className="glass p-6 md:p-8">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-neon-cyan/80">
            Model Footprint · log scale
          </div>
          <div className="text-white text-lg font-medium mt-1">
            On-Device vs. Server-Class Models
          </div>
        </div>
        <div className="font-mono text-[10px] tracking-widest text-slate-500">
          smaller is better
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 8, right: 90, bottom: 8, left: 4 }}
          >
            <defs>
              <linearGradient id="barCyan" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00ffd1" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
              <linearGradient id="barDim" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#334155" />
                <stop offset="100%" stopColor="#475569" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.08)" horizontal={false} />
            <XAxis
              type="number"
              scale="log"
              domain={[10, 600 * 1024]}
              stroke="rgba(148,163,184,0.4)"
              tick={{ fontSize: 10, fontFamily: "ui-monospace" }}
              tickFormatter={(v) => fmt(Number(v))}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="rgba(148,163,184,0.6)"
              tick={{ fontSize: 12, fontFamily: "ui-monospace", fill: "#cbd5e1" }}
              width={110}
            />
            <Tooltip
              cursor={{ fill: "rgba(0,255,209,0.05)" }}
              contentStyle={{
                background: "rgba(2,6,23,0.95)",
                border: "1px solid rgba(0,255,209,0.3)",
                fontFamily: "ui-monospace",
                fontSize: 11,
              }}
              formatter={(v: number) => [fmt(v), "Size"]}
            />
            <Bar dataKey="kb" radius={[6, 6, 6, 6]} barSize={26}
              label={{
                position: "right",
                formatter: (v: number) => fmt(v),
                fill: "#cbd5e1",
                fontSize: 11,
                fontFamily: "ui-monospace",
              }}
            >
              {data.map((row, i) => (
                <Cell
                  key={i}
                  fill={row.highlight ? "url(#barCyan)" : "url(#barDim)"}
                  style={
                    row.highlight
                      ? { filter: "drop-shadow(0 0 10px rgba(0,255,209,0.5))" }
                      : undefined
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        {data.map((d) => (
          <div
            key={d.name}
            className={`rounded-lg border p-3 ${
              d.highlight
                ? "border-neon-cyan/40 bg-neon-cyan/5"
                : "border-slate-800 bg-slate-900/40"
            }`}
          >
            <div className="font-mono text-[10px] uppercase tracking-widest text-slate-400">
              {d.name}
            </div>
            <div
              className={`font-mono text-base mt-1 ${
                d.highlight ? "text-neon-cyan" : "text-slate-200"
              }`}
            >
              {fmt(d.kb)}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">{d.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
