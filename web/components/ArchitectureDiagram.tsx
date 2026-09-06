"use client";

import { Activity, BellRing, BrainCircuit, ShieldCheck, Watch } from "lucide-react";

const steps = [
  { icon: Watch, number: "01", title: "Sense", text: "Collect accelerometer, gyroscope and PPG/heart-rate signals. Temperature is optional." },
  { icon: BrainCircuit, number: "02", title: "Assess", text: "The Android/edge layer preprocesses windows. A future validated wearable model will estimate risk." },
  { icon: ShieldCheck, number: "03", title: "Confirm", text: "Repeated high-risk readings trigger vibration and a 15-second ‘I’m OK’ cancellation window." },
  { icon: BellRing, number: "04", title: "Alert", text: "Without a response, the phone can attempt an SMS containing GPS, event time and risk information." },
];

export function ArchitectureDiagram() {
  return <div className="space-y-5">
    <div className="grid md:grid-cols-4 gap-4">
      {steps.map(({ icon: Icon, number, title, text }, index) => <div key={title} className="glass p-5 relative">
        <div className="flex items-center justify-between"><span className="font-mono text-xs text-neon-cyan">{number}</span><Icon size={22} className={index === 3 ? "text-neon-amber" : "text-neon-cyan"} /></div>
        <h3 className="mt-5 text-xl font-semibold text-white">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-400">{text}</p>
      </div>)}
    </div>
    <div className="glass-inner p-4 flex gap-3 text-sm text-slate-300"><Activity size={18} className="shrink-0 text-neon-amber" /><p><strong className="text-white">Scientific boundary:</strong> the offline EEG classifier and wearable demonstration are separate. EEG-derived performance cannot be transferred directly to IMU, PPG or temperature inputs.</p></div>
  </div>;
}
