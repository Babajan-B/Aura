"use client";

import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const comparison = [
  { model: "HistGradientBoosting", auroc: 0.926, auprc: 0.981 },
  { model: "Extra Trees", auroc: 0.918, auprc: 0.978 },
  { model: "Random Forest", auroc: 0.932, auprc: 0.982 },
];

export function FootprintChart() {
  return <div className="grid lg:grid-cols-[1.5fr_1fr] gap-6">
    <div className="glass p-6 md:p-8">
      <div className="font-mono text-[10px] uppercase tracking-widest text-neon-cyan">Held-out model comparison</div>
      <div className="mt-5 h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={comparison} margin={{ top: 20, right: 10, left: -12, bottom: 28 }}><CartesianGrid stroke="rgba(148,163,184,0.10)" vertical={false} /><XAxis dataKey="model" tick={{ fill: "#94a3b8", fontSize: 11 }} interval={0} angle={-8} textAnchor="end" /><YAxis domain={[0.7, 1]} tick={{ fill: "#94a3b8", fontSize: 10 }} /><Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155" }} /><Legend /><Bar dataKey="auroc" name="ROC-AUC" fill="#00ffd1" radius={[4,4,0,0]} /><Bar dataKey="auprc" name="PR-AUC" fill="#fbbf24" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer></div>
    </div>
    <div className="glass p-6 md:p-8">
      <div className="font-mono text-[10px] uppercase tracking-widest text-neon-cyan">Random Forest test result</div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        {[['TN','165'],['FP','59'],['FN','61'],['TP','1,010']].map(([label,value], index) => <div key={label} className={`rounded-md border p-4 text-center ${index === 3 ? 'border-neon-cyan/50 bg-neon-cyan/10' : 'border-slate-700 bg-slate-900/50'}`}><div className="font-mono text-xs text-slate-400">{label}</div><div className="mt-1 text-2xl font-semibold text-white">{value}</div></div>)}
      </div>
      <dl className="mt-6 space-y-3 text-sm">{[['Sensitivity','94.3%'],['Specificity','73.7%'],['F1 score','0.944'],['Brier score','0.072'],['ECE','0.092']].map(([label,value]) => <div key={label} className="flex justify-between border-b border-slate-800 pb-2"><dt className="text-slate-400">{label}</dt><dd className="font-mono text-white">{value}</dd></div>)}</dl>
      <p className="mt-5 text-xs leading-relaxed text-neon-amber">Cross-dataset ROC-AUC: CHB-MIT 0.971; TUSZ 0.780. External and prospective validation remain required.</p>
    </div>
  </div>;
}
