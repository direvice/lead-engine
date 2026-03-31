"use client";

import { motion } from "framer-motion";

export function RevenueCallout({
  amount,
  subtitle,
  analysisNote,
}: {
  amount: number;
  subtitle?: string | null;
  /** Shown when amount is 0 (e.g. analysis not run yet). */
  analysisNote?: string | null;
}) {
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-2xl border border-accent/25 bg-gradient-to-br from-accent/[0.08] to-transparent p-6 ring-1 ring-inset ring-white/[0.04]"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-accent/10 blur-2xl" />
      <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-500">
        Revenue surface
      </p>
      <p className="mt-3 text-4xl font-semibold tabular-nums tracking-tight text-accent sm:text-5xl">
        {formatted}
        <span className="ml-1 text-lg font-normal text-zinc-500">/mo</span>
      </p>
      <p className="mt-2 text-[14px] text-zinc-400">Conservative modeled opportunity</p>
      {amount <= 0 && analysisNote ? (
        <p className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/[0.06] px-3 py-2 text-[13px] leading-relaxed text-amber-100/80">
          {analysisNote}
        </p>
      ) : null}
      {subtitle ? <p className="mt-4 text-[13px] leading-relaxed text-zinc-500">{subtitle}</p> : null}
    </motion.div>
  );
}
