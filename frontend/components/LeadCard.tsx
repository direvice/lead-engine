"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Lead } from "@/lib/types";
import { googleMapsUrl, googleSearchUrl, normalizeWebsiteUrl } from "@/lib/outreach-links";
import { ScoreRing } from "./ScoreRing";

function money(n: number | null | undefined) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function formatAnalyzedAt(iso: string | null | undefined) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return null;
  }
}

export function LeadCard({ lead }: { lead: Lead }) {
  const score = lead.lead_score ?? 0;
  const rev = lead.revenue_opportunity_monthly ?? 0;
  const loc = (lead.address || "").split(",").slice(-2).join(",").trim();
  const web = normalizeWebsiteUrl(lead.website);
  const maps = googleMapsUrl(lead);
  const analyzed = Boolean(lead.last_analyzed_at);
  const ratingLine =
    lead.google_rating != null
      ? `${lead.google_rating.toFixed(1)}★${lead.review_count != null ? ` · ${lead.review_count} reviews` : ""}`
      : null;

  const insight =
    lead.ai_biggest_problem ||
    lead.ai_summary ||
    lead.revenue_opportunity_desc ||
    (!analyzed
      ? "Full analysis not saved yet — use “Fill in missing analysis” on Command or open dossier → Re-run analysis."
      : lead.scrape_error
        ? `Last scrape: ${lead.scrape_error.slice(0, 120)}${lead.scrape_error.length > 120 ? "…" : ""}`
        : "Listing captured; open dossier for full intelligence.");

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
          {ratingLine ? (
            <>
              <span className="text-zinc-700">·</span>
              <span className="text-zinc-400">{ratingLine}</span>
            </>
          ) : null}
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
          {lead.features?.builder ? (
            <span className="rounded bg-white/[0.06] px-1.5 py-0.5 text-[10px] font-medium text-zinc-400">
              {lead.features.builder}
            </span>
          ) : null}
        </p>

        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[12px]">
          {web ? (
            <a
              href={web}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-accent hover:text-[#f0ff6a]"
              onClick={(e) => e.stopPropagation()}
            >
              Website ↗
            </a>
          ) : lead.no_website ? (
            <span className="text-zinc-600">No website on file</span>
          ) : (
            <span className="text-zinc-600">No URL</span>
          )}
          {maps ? (
            <a
              href={maps}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-zinc-400 hover:text-white"
              onClick={(e) => e.stopPropagation()}
            >
              Maps ↗
            </a>
          ) : null}
          <a
            href={googleSearchUrl(lead.business_name, lead.address)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 hover:text-zinc-300"
            onClick={(e) => e.stopPropagation()}
          >
            Google ↗
          </a>
          {lead.phone ? (
            <a href={`tel:${lead.phone}`} className="text-zinc-400 hover:text-accent" onClick={(e) => e.stopPropagation()}>
              Call
            </a>
          ) : null}
        </div>

        <p className="mt-3 line-clamp-2 text-[13px] leading-relaxed text-zinc-500">{insight}</p>
        {formatAnalyzedAt(lead.last_analyzed_at) ? (
          <p className="mt-1.5 text-[11px] text-zinc-700">Analyzed · {formatAnalyzedAt(lead.last_analyzed_at)}</p>
        ) : (
          <p className="mt-1.5 text-[11px] text-amber-200/50">Not analyzed yet</p>
        )}
      </div>
      <div className="flex items-center gap-6 sm:justify-end">
        <ScoreRing label="Score" value={score} size={56} />
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-zinc-600">Monthly Δ</p>
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
