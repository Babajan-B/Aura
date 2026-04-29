"use client";

import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect } from "react";

interface RiskGaugeProps {
  value: number; // 0..1
  label?: string;
}

const RADIUS = 120;
const STROKE = 18;
const CIRC = Math.PI * RADIUS; // semicircle length

function colorFor(v: number): string {
  if (v < 0.4) return "#22ee9b";
  if (v < 0.75) return "#fbbf24";
  return "#ff2e6c";
}

export function RiskGauge({ value, label }: RiskGaugeProps) {
  const clamped = Math.max(0, Math.min(1, value));
  const mv = useMotionValue(0);
  const dash = useTransform(mv, (v) => `${v * CIRC} ${CIRC}`);
  const display = useTransform(mv, (v) => (v * 100).toFixed(1));

  useEffect(() => {
    const ctrl = animate(mv, clamped, { duration: 0.9, ease: "easeOut" });
    return () => ctrl.stop();
  }, [clamped, mv]);

  const stroke = colorFor(clamped);
  const status =
    clamped < 0.4
      ? "STABLE"
      : clamped < 0.75
      ? "ELEVATED"
      : "PRE-ICTAL ALERT";

  return (
    <div className="relative flex flex-col items-center justify-center">
      <svg viewBox="0 0 280 170" className="w-full max-w-sm">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22ee9b" />
            <stop offset="55%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#ff2e6c" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <path
          d={`M 20 150 A ${RADIUS} ${RADIUS} 0 0 1 260 150`}
          stroke="rgba(148,163,184,0.15)"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
        />
        {/* Gradient backdrop */}
        <path
          d={`M 20 150 A ${RADIUS} ${RADIUS} 0 0 1 260 150`}
          stroke="url(#gaugeGrad)"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
          strokeOpacity="0.18"
        />
        {/* Animated value arc */}
        <motion.path
          d={`M 20 150 A ${RADIUS} ${RADIUS} 0 0 1 260 150`}
          stroke={stroke}
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
          style={{ strokeDasharray: dash, filter: "url(#glow)" }}
        />

        {/* Threshold tick at 0.75 */}
        {(() => {
          const a = Math.PI * (1 - 0.75);
          const x1 = 140 + Math.cos(a) * (RADIUS - STROKE);
          const y1 = 150 - Math.sin(a) * (RADIUS - STROKE);
          const x2 = 140 + Math.cos(a) * (RADIUS + 4);
          const y2 = 150 - Math.sin(a) * (RADIUS + 4);
          return (
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#ff2e6c"
              strokeWidth={2}
              strokeDasharray="2 2"
            />
          );
        })()}

        {/* Center text */}
        <text
          x="140"
          y="120"
          textAnchor="middle"
          fill="#fff"
          fontSize="44"
          fontFamily="ui-monospace"
          fontWeight="600"
        >
          <motion.tspan>{display}</motion.tspan>%
        </text>
        <text
          x="140"
          y="142"
          textAnchor="middle"
          fill="rgba(148,163,184,0.8)"
          fontSize="10"
          fontFamily="ui-monospace"
          letterSpacing="3"
        >
          PRE-ICTAL RISK
        </text>
      </svg>

      <div
        className="mt-2 rounded-full border px-3 py-1 font-mono text-[11px] tracking-widest"
        style={{
          color: stroke,
          borderColor: `${stroke}55`,
          boxShadow: `0 0 14px ${stroke}55`,
        }}
      >
        {label ?? status}
      </div>
    </div>
  );
}
