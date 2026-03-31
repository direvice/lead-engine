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
        <p className="mt-1 flex flex-wrap items-center gap-2 text-[13px] text-zinc-500">
          <span className="text-zinc-400">{lead.category || "Business"}</span>
          {loc ? <span className="text-zinc-700">·</span> : null}
          {loc || ""}
          {lead.features?.smb_fit?.target_tier === "ideal_smb" ? (
            <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-emerald-300/90">
              SMB
            </span>
          ) : null}
          {lead.features?.smb_fit?.target_tier === "likely_chain" ? (
            <span className="rounded bg-rose-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-rose-300/90">
              Chain?
            </span>
          ) : null}
          {lead.features?.site_intel?.archetype === "brochure_static" ? (
            <span className="rounded bg-sky-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-sky-200/90">
              Brochure site
            </span>
          ) : null}
          {lead.features?.site_intel?.archetype === "app_like" ? (
            <span className="rounded bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-violet-200/90">
              App-like
            </span>
          ) : null}
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
