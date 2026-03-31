"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AudioPlayer } from "@/components/AudioPlayer";
import { CallScript } from "@/components/CallScript";
import { CompetitorCard } from "@/components/CompetitorCard";
import { IssueList } from "@/components/IssueList";
import { RevenueCallout } from "@/components/RevenueCallout";
import { ScoreRing } from "@/components/ScoreRing";
import { getLead, patchLead, queueAnalyzeLead, teachLead } from "@/lib/api";
import { staticFileUrl } from "@/lib/assets";
import { googleMapsUrl, googleSearchUrl, normalizeWebsiteUrl } from "@/lib/outreach-links";
import type { Lead } from "@/lib/types";

export default function LeadDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [lead, setLead] = useState<Lead | null>(null);
  const [notes, setNotes] = useState("");
  const [teachMsg, setTeachMsg] = useState<string | null>(null);
  const [analyzeMsg, setAnalyzeMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getLead(id).then((L) => {
      setLead(L);
      setNotes(L.notes || "");
    });
  }, [id]);

  if (!lead) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4">
        <div className="h-8 w-8 animate-pulse rounded-full bg-accent/20" />
        <p className="text-[13px] text-zinc-500">Loading dossier…</p>
        <Link href="/" className="text-[12px] text-zinc-600 hover:text-accent">
          ← Command
        </Link>
      </div>
    );
  }

  const comps = (lead.competitors || []) as {
    name?: string;
    rating?: number;
    review_count?: number;
  }[];

  const web = normalizeWebsiteUrl(lead.website);
  const maps = googleMapsUrl(lead);
  const analyzed = Boolean(lead.last_analyzed_at);
  const listingBlurb = [
    lead.category,
    lead.google_rating != null ? `${lead.google_rating}★` : null,
    lead.review_count != null ? `${lead.review_count} reviews` : null,
    lead.address,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="space-y-10">
      <div>
        <Link href="/" className="text-[12px] text-zinc-600 transition hover:text-accent">
          ← Command
        </Link>
        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mt-4">
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-600">Dossier</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {lead.business_name}
          </h1>
          <p className="mt-2 text-[14px] text-zinc-500">
            <span className="text-zinc-400">{lead.category}</span>
            {lead.address ? <span className="text-zinc-700"> · </span> : null}
            {lead.address}
          </p>
          {lead.phone ? (
            <a
              href={`tel:${lead.phone}`}
              className="mt-3 inline-block text-xl font-medium tracking-tight text-accent hover:text-[#f0ff6a]"
            >
              {lead.phone}
            </a>
          ) : null}

          <div className="mt-5 flex flex-wrap gap-2">
            {web ? (
              <a
                href={web}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-2 text-[13px] font-semibold text-accent transition hover:bg-accent/20"
              >
                Website ↗
              </a>
            ) : (
              <span className="rounded-xl border border-white/[0.08] px-4 py-2 text-[13px] text-zinc-600">
                No website URL
              </span>
            )}
            {maps ? (
              <a
                href={maps}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-white/[0.12] bg-white/[0.04] px-4 py-2 text-[13px] font-medium text-zinc-200 transition hover:border-white/[0.2] hover:text-white"
              >
                Google Maps ↗
              </a>
            ) : null}
            <a
              href={googleSearchUrl(lead.business_name, lead.address)}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-[13px] text-zinc-300 transition hover:border-white/[0.12] hover:text-white"
            >
              Search business ↗
            </a>
            <button
              type="button"
              className="rounded-xl border border-white/[0.12] bg-white/[0.06] px-4 py-2 text-[13px] font-medium text-white transition hover:bg-white/[0.1]"
              onClick={() =>
                queueAnalyzeLead(lead.id)
                  .then(() => {
                    setAnalyzeMsg("Analysis queued — wait ~30–90s, then refresh this page.");
                    setTimeout(() => setAnalyzeMsg(null), 8000);
                  })
                  .catch(() => setAnalyzeMsg("Could not queue — check API / Playwright on host."))
              }
            >
              Re-run analysis
            </button>
          </div>
          {analyzeMsg ? <p className="mt-3 text-[12px] text-zinc-500">{analyzeMsg}</p> : null}
          {!analyzed ? (
            <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-amber-200/70">
              No completed analysis on record. Scores and AI blocks fill in after the pipeline runs (Playwright scrape +
              scoring + model). Use Re-run analysis, or Command → Fill in missing analysis for a batch.
            </p>
          ) : null}
          {listingBlurb ? (
            <p className="mt-3 max-w-2xl text-[13px] text-zinc-600">
              <span className="font-medium text-zinc-500">Listing snapshot · </span>
              {listingBlurb}
            </p>
          ) : null}
        </motion.div>
      </div>

      <div className="grid gap-10 lg:grid-cols-[1.55fr_1fr]">
        <div className="space-y-10">
          <RevenueCallout
            amount={lead.revenue_opportunity_monthly || 0}
            subtitle={lead.revenue_opportunity_desc}
            analysisNote={
              !analyzed
                ? "Revenue and scores are modeled after a full analysis. Queue Re-run analysis above."
                : lead.scrape_error
                  ? `Scrape note: ${lead.scrape_error.slice(0, 200)}${lead.scrape_error.length > 200 ? "…" : ""}`
                  : null
            }
          />

          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-600">Scores</p>
            <div className="mt-4 flex flex-wrap gap-6">
              <ScoreRing label="Opportunity" value={lead.opportunity_score ?? 0} />
              <ScoreRing label="Tech debt" value={lead.technical_debt_score ?? 0} />
              <ScoreRing label="Urgency" value={lead.urgency_score ?? 0} />
              <ScoreRing label="SEO" value={lead.seo_score ?? 0} />
              <ScoreRing label="Mobile" value={lead.mobile_score ?? 0} />
            </div>
            <p className="mt-4 text-[12px] text-zinc-600">
              PageSpeed mobile {lead.pagespeed_mobile ?? "—"} · desktop {lead.pagespeed_desktop ?? "—"}
              {lead.load_time_ms != null ? ` · first paint ~${lead.load_time_ms}ms` : ""}
            </p>
            {!analyzed ? (
              <p className="mt-2 text-[12px] text-zinc-600">Scores stay at 0 until analysis completes.</p>
            ) : null}
          </div>

          {lead.features?.smb_fit ? (
            <section>
              <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">
                SMB fit (automated)
              </h2>
              <div className="mt-4 rounded-2xl border border-white/[0.06] bg-card/50 p-4">
                <div className="flex flex-wrap gap-2 text-[12px]">
                  <span
                    className={
                      lead.features.smb_fit.target_tier === "ideal_smb"
                        ? "rounded-full bg-emerald-500/15 px-2.5 py-1 font-medium text-emerald-200 ring-1 ring-emerald-500/25"
                        : lead.features.smb_fit.target_tier === "likely_chain"
                          ? "rounded-full bg-rose-500/15 px-2.5 py-1 font-medium text-rose-200 ring-1 ring-rose-500/25"
                          : "rounded-full bg-amber-500/15 px-2.5 py-1 font-medium text-amber-200 ring-1 ring-amber-500/25"
                    }
                  >
                    {lead.features.smb_fit.target_tier === "ideal_smb"
                      ? "Ideal local target"
                      : lead.features.smb_fit.target_tier === "likely_chain"
                        ? "Likely chain — skip?"
                        : "Borderline"}
                  </span>
                  <span className="rounded-full bg-white/[0.06] px-2.5 py-1 text-zinc-400">
                    Fit index · {lead.features.smb_fit.smb_fit_index ?? "—"}
                  </span>
                  <span className="rounded-full bg-white/[0.06] px-2.5 py-1 text-zinc-400">
                    Simplicity · {lead.features.smb_fit.simplicity_score ?? "—"}
                  </span>
                  <span className="rounded-full bg-white/[0.06] px-2.5 py-1 text-zinc-400">
                    Fixability · {lead.features.smb_fit.fixability_score ?? "—"}
                  </span>
                </div>
                {lead.features.smb_fit.reasons?.length ? (
                  <ul className="mt-4 space-y-1.5 text-[13px] leading-relaxed text-zinc-500">
                    {lead.features.smb_fit.reasons.map((r, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-accent/70">·</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </section>
          ) : null}

          {lead.features?.ai_smb_intel ? (
            <section>
              <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">
                Easy wins & positioning
              </h2>
              <div className="mt-4 space-y-4">
                {lead.features.ai_smb_intel.tech_simplicity_note ? (
                  <p className="text-[13px] leading-relaxed text-zinc-500">
                    <span className="font-medium text-zinc-400">Stack: </span>
                    {lead.features.ai_smb_intel.tech_simplicity_note}
                  </p>
                ) : null}
                {lead.features.ai_smb_intel.chain_verdict ? (
                  <p className="text-[13px] text-zinc-500">
                    <span className="font-medium text-zinc-400">Chain check: </span>
                    {lead.features.ai_smb_intel.chain_verdict.replace(/_/g, " ")}
                    {lead.features.ai_smb_intel.ideal_client_for_solo_dev === false ? (
                      <span className="ml-2 text-rose-300/90">· Not ideal for solo dev</span>
                    ) : null}
                  </p>
                ) : null}
                {lead.features.ai_smb_intel.what_not_to_sell ? (
                  <p className="text-[13px] leading-relaxed text-zinc-500">
                    <span className="font-medium text-zinc-400">Don&apos;t pitch: </span>
                    {lead.features.ai_smb_intel.what_not_to_sell}
                  </p>
                ) : null}
                {lead.features.ai_smb_intel.easy_wins?.length ? (
                  <ul className="space-y-4">
                    {lead.features.ai_smb_intel.easy_wins.map((w, i) => (
                      <li
                        key={i}
                        className="rounded-xl border border-white/[0.06] bg-black/20 px-4 py-3 text-[13px] leading-relaxed text-zinc-400"
                      >
                        <p className="font-medium text-white">{w.fix || "Fix"}</p>
                        {w.why_it_matters ? (
                          <p className="mt-1 text-zinc-500">{w.why_it_matters}</p>
                        ) : null}
                        <p className="mt-2 text-[12px] text-zinc-600">
                          {w.effort ? <span className="text-accent/80">Effort · {w.effort}</span> : null}
                          {w.how_you_fix_it ? (
                            <span className="mt-1 block text-zinc-500">{w.how_you_fix_it}</span>
                          ) : null}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </section>
          ) : null}

          <section>
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">Issues</h2>
            <div className="mt-4">
              <IssueList
                issues={lead.issues}
                emptyHint={
                  lead.scrape_error
                    ? `Scrape/load: ${lead.scrape_error}. After a successful run, issues populate from HTML + PageSpeed.`
                    : !analyzed
                      ? "Run analysis to generate structured issues from the live site."
                      : null
                }
              />
            </div>
          </section>

          {lead.pagespeed_opportunities && lead.pagespeed_opportunities.length > 0 ? (
            <section>
              <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">
                PageSpeed opportunities
              </h2>
              <p className="mt-2 text-[12px] text-zinc-600">
                Actionable Lighthouse hints (often quick wins: images, fonts, unused JS).
              </p>
              <ul className="mt-4 space-y-3">
                {lead.pagespeed_opportunities.map((o) => (
                  <li
                    key={o.id || o.title}
                    className="rounded-xl border border-white/[0.06] bg-black/15 px-4 py-3 text-[13px] leading-relaxed text-zinc-400"
                  >
                    <p className="font-medium text-zinc-200">{o.title}</p>
                    {o.description ? (
                      <p className="mt-1 text-[12px] text-zinc-500">{o.description}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section>
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">Competitors</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {comps.length ? (
                comps.slice(0, 3).map((c, i) => (
                  <CompetitorCard key={i} name={c.name || "—"} rating={c.rating} review_count={c.review_count} />
                ))
              ) : (
                <p className="col-span-full text-[13px] text-zinc-600">
                  No competitor list yet. The engine uses Google Places nearby search when{" "}
                  <code className="rounded bg-white/[0.06] px-1 font-mono text-[11px]">GOOGLE_PLACES_API_KEY</code> is set
                  and coordinates exist.
                </p>
              )}
            </div>
            {lead.competitive_gaps?.length ? (
              <ul className="mt-4 space-y-2 text-[13px] leading-relaxed text-zinc-500">
                {lead.competitive_gaps.map((g, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-accent/80">·</span>
                    {g}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>

          <section>
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-zinc-500">Capture</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {lead.desktop_screenshot_path ? (
                <img
                  src={staticFileUrl(lead.desktop_screenshot_path, "screenshots") || ""}
                  alt="Desktop"
                  className="rounded-2xl border border-white/[0.06] bg-black/20"
                />
              ) : null}
              {lead.mobile_screenshot_path ? (
                <img
                  src={staticFileUrl(lead.mobile_screenshot_path, "screenshots") || ""}
                  alt="Mobile"
                  className="rounded-2xl border border-white/[0.06] bg-black/20"
                />
              ) : null}
              {!lead.desktop_screenshot_path && !lead.mobile_screenshot_path ? (
                <p className="col-span-full text-[13px] text-zinc-600">
                  No screenshots yet — captured during site analysis when Playwright runs successfully.
                </p>
              ) : null}
            </div>
          </section>
        </div>

        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-2xl border border-white/[0.06] bg-card/70 p-5 backdrop-blur-sm">
            <h3 className="text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-500">Teach the model</h3>
            <p className="mt-2 text-[12px] leading-relaxed text-zinc-600">
              Your labels tune ranking for similar businesses (pattern = SMB tier + site builder).
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-lg bg-emerald-500/15 px-3 py-1.5 text-[12px] font-medium text-emerald-200 ring-1 ring-emerald-500/25 transition hover:bg-emerald-500/25"
                onClick={() =>
                  teachLead(lead.id, "good_target")
                    .then(() => {
                      setTeachMsg("Saved · good target for your practice");
                      setTimeout(() => setTeachMsg(null), 3200);
                    })
                    .catch(() => setTeachMsg("Could not save — check API"))
                }
              >
                👍 Good target
              </button>
              <button
                type="button"
                className="rounded-lg bg-rose-500/15 px-3 py-1.5 text-[12px] font-medium text-rose-200 ring-1 ring-rose-500/25 transition hover:bg-rose-500/25"
                onClick={() =>
                  teachLead(lead.id, "bad_target")
                    .then(() => {
                      setTeachMsg("Saved · will dampen similar profiles");
                      setTimeout(() => setTeachMsg(null), 3200);
                    })
                    .catch(() => setTeachMsg("Could not save — check API"))
                }
              >
                👎 Bad fit
              </button>
            </div>
            {teachMsg ? <p className="mt-2 text-[11px] text-zinc-500">{teachMsg}</p> : null}
          </div>

          <div className="rounded-2xl border border-white/[0.06] bg-card/70 p-5 backdrop-blur-sm">
            <h3 className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent">Intelligence</h3>
            <p className="mt-3 text-[14px] leading-relaxed text-zinc-400">
              {lead.ai_summary ||
                (!analyzed
                  ? "Summary appears after the AI pass. If this stays empty, the model may be unavailable (configure Ollama or GEMINI_API_KEY on the API host) or analysis never finished."
                  : "No summary stored for this lead.")}
            </p>
            {lead.ai_urgency_reason ? (
              <p className="mt-3 text-[12px] leading-relaxed text-zinc-500">
                <span className="font-medium text-zinc-400">Urgency · </span>
                {lead.ai_urgency_reason}
              </p>
            ) : null}
            <p className="mt-5 text-[11px] font-medium uppercase tracking-wider text-zinc-600">Pitch</p>
            <p className="mt-2 text-[14px] font-medium leading-relaxed text-white">
              {lead.ai_pitch ||
                (!analyzed
                  ? "Cold-call opener will generate after analysis."
                  : "—")}
            </p>
            <div className="mt-4 space-y-1 text-[12px] text-zinc-600">
              <p>Service · {lead.ai_recommended_service || "—"}</p>
              <p>Estimate · {lead.ai_estimated_value || "—"}</p>
            </div>
            <button
              type="button"
              className="mt-4 text-[13px] font-medium text-accent hover:text-[#f0ff6a]"
              onClick={() => navigator.clipboard.writeText(lead.ai_pitch || "")}
            >
              Copy pitch
            </button>
            {lead.email_pitch ? (
              <>
                <p className="mt-5 text-[11px] font-medium uppercase tracking-wider text-zinc-600">Email draft</p>
                <p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap text-[12px] leading-relaxed text-zinc-500">
                  {lead.email_pitch}
                </p>
                <button
                  type="button"
                  className="mt-2 text-[12px] font-medium text-zinc-400 hover:text-accent"
                  onClick={() => navigator.clipboard.writeText(lead.email_pitch || "")}
                >
                  Copy email
                </button>
              </>
            ) : null}
          </div>

          <CallScript script={lead.call_script} />

          <AudioPlayer src={staticFileUrl(lead.audio_briefing_path, "audio") || ""} />

          <div className="rounded-2xl border border-white/[0.06] bg-card/70 p-5 backdrop-blur-sm">
            <h3 className="text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-500">Pipeline</h3>
            <select
              className="input-intel mt-3"
              value={lead.status}
              onChange={(e) => patchLead(lead.id, { status: e.target.value }).then(setLead)}
            >
              {["new", "contacted", "interested", "won", "skip"].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <textarea
              className="input-intel mt-3 min-h-[100px] resize-y font-mono text-[12px] leading-relaxed"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={() => patchLead(lead.id, { notes }).then(setLead)}
              placeholder="Notes — autosave on blur"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {lead.phone ? (
              <button
                type="button"
                className="rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-[13px] text-zinc-300 transition hover:border-white/[0.12] hover:text-white"
                onClick={() => navigator.clipboard.writeText(lead.phone || "")}
              >
                Copy phone
              </button>
            ) : null}
            {web ? (
              <a
                href={web}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-[13px] text-zinc-300 transition hover:border-accent/30 hover:text-accent"
              >
                Website
              </a>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
