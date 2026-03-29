"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Lead } from "@/lib/types";
import { ScoreRing } from "./ScoreRing";

function money(n: number | null | undefined) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

export function LeadCard({ lead }: { lead: Lead }) {
  const score = lead.lead_score ?? 0;
  const rev = lead.revenue_opportunity_monthly ?? 0;
  const loc = (lead.address || "").split(",").slice(-2).join(",").trim();

  return (
    <motion.div
      layout
      whileHover={{ borderColor: "rgba(232, 255, 71, 0.15)" }}
      className="group grid grid-cols-1 gap-5 rounded-2xl border border-white/[0.06] bg-card/60 p-5 shadow-card backdrop-blur-sm transition-colors sm:grid-cols-[1fr_auto_auto]"
    >
      <div className="min-w-0">
        <Link
          href={`/leads/${lead.id}`}
          className="text-lg font-semibold tracking-tight text-white transition group-hover:text-accent"
        >
          {lead.business_name}
        </Link>
        <p className="mt-1 text-[13px] text-zinc-500">
          <span className="text-zinc-400">{lead.category || "Business"}</span>
          {loc ? <span className="text-zinc-700"> · </span> : null}
          {loc || ""}
        </p>
        <p className="mt-3 line-clamp-2 text-[13px] leading-relaxed text-zinc-500">
          {lead.ai_biggest_problem || lead.revenue_opportunity_desc || "Awaiting analysis."}
        </p>
      </div>
      <div className="flex items-center gap-6 sm:justify-end">
        <ScoreRing label="Score" value={score} size={56} />
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-zinc-600">
            Monthly Δ
          </p>
          <p className="mt-1 text-xl font-semibold tabular-nums tracking-tight text-accent">
            {money(rev)}
            <span className="text-sm font-normal text-zinc-600">/mo</span>
          </p>
        </div>
      </div>
      <div className="flex flex-col items-start gap-2 sm:items-end sm:justify-center">
        <span className="rounded-full bg-accent/10 px-3 py-1 text-[11px] font-medium text-accent ring-1 ring-accent/20">
          {lead.ai_recommended_service || "Website fixes"}
        </span>
        <span className="text-[11px] text-zinc-600">{lead.ai_estimated_value || "—"}</span>
        <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500">
          {lead.status}
        </span>
        <Link
          href={`/leads/${lead.id}`}
          className="text-[13px] font-medium text-zinc-400 transition hover:text-white"
        >
          Open dossier →
        </Link>
      </div>
    </motion.div>
  );
}
