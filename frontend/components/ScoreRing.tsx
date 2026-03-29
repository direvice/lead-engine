"use client";

import { useId } from "react";
import { motion } from "framer-motion";

export function ScoreRing({
  label,
  value,
  size = 72,
}: {
  label: string;
  value: number;
  size?: number;
}) {
  const fid = useId().replace(/:/g, "");
  const v = Math.min(100, Math.max(0, value));
  const stroke = 3;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  const color = v >= 70 ? "#e8ff47" : v >= 45 ? "#c4d93a" : "#a3a3a3";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          <defs>
            <filter id={`glow-${fid}`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={stroke}
            fill="none"
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={stroke}
            fill="none"
            strokeDasharray={c}
            filter={v >= 60 ? `url(#glow-${fid})` : undefined}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-[11px] font-semibold tabular-nums text-white">
          {Math.round(v)}
        </span>
      </div>
      <span className="text-[9px] font-medium uppercase tracking-[0.2em] text-zinc-600">{label}</span>
    </div>
  );
}
