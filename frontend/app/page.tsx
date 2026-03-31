"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { LeadCard } from "@/components/LeadCard";
import { getPublicApiBase } from "@/lib/api-base";
import { getLeads, getStats, leadsExportCsvUrl } from "@/lib/api";
import { useApiConnection } from "@/components/SystemStatus";
import type { Lead, Stats } from "@/lib/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [q, setQ] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState<"lead_score" | "smb_fit" | "newest" | "revenue">("lead_score");
  const [smbTier, setSmbTier] = useState("");
  const [hideChains, setHideChains] = useState(true);
  const [preferStatic, setPreferStatic] = useState(true);
  const [autopilot, setAutopilot] = useState(true);
  const { connected } = useApiConnection();

  useEffect(() => {
    getStats().then(setStats).catch(() => setStats(null));
  }, []);

  useEffect(() => {
    if (autopilot) {
      getLeads({
        autopilot: true,
        q: q || undefined,
        limit: 80,
      })
        .then((r) => setLeads(r.items))
        .catch(() => setLeads([]));
      return;
    }
    getLeads({
      min_score: minScore,
      q: q || undefined,
      status: status || undefined,
      sort,
      smb_tier: smbTier || undefined,
      exclude_likely_chain: hideChains || undefined,
      prefer_static: preferStatic || undefined,
      limit: 80,
    })
      .then((r) => setLeads(r.items))
      .catch(() => setLeads([]));
  }, [q, minScore, status, sort, smbTier, hideChains, preferStatic, autopilot]);

  const hero = useMemo(() => {
    if (!stats) return null;
    const fmt = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(stats.total_monthly_opportunity);
    return { fmt, n: stats.total_leads };
  }, [stats]);

  const apiBase = typeof window !== "undefined" ? getPublicApiBase() : "";

  return (
    <div className="space-y-10">
      {connected === false ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-amber-500/20 bg-amber-500/[0.06] px-5 py-4 text-sm text-amber-100/90"
        >
          <p className="font-medium text-amber-200">Backend not reachable</p>
          <p className="mt-1 text-[13px] leading-relaxed text-amber-100/70">
            On Vercel, set{" "}
            <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-[12px] text-accent">
              NEXT_PUBLIC_API_URL
            </code>{" "}
            to your FastAPI base URL. Add the same origin to{" "}
            <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-[12px]">CORS_ORIGINS</code>{" "}
            in the API <code className="font-mono text-[12px]">.env</code>.
          </p>
        </motion.div>
      ) : null}

      <section className="animate-fade-up">
        <p className="text-[11px] font-medium uppercase tracking-[0.25em] text-zinc-600">Overview</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          {hero ? (
            <>
              <span className="text-zinc-400">{hero.n.toLocaleString()}</span>{" "}
              <span className="text-zinc-600">leads</span>
              <span className="mx-2 text-zinc-700">·</span>
              <span className="text-accent">{hero.fmt}</span>
              <span className="text-zinc-600"> / mo surface</span>
            </>
          ) : (
            "Loading intelligence…"
          )}
        </h1>
        <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-zinc-500">
          Autopilot ranks independent locals, hides heavy JS app shells from the queue, and surfaces
          brochure-style sites the engine can actually fix—then AI writes the pitch.
        </p>
      </section>

      {stats ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Corpus", stats.total_leads.toLocaleString()],
            ["7d new", stats.new_this_week.toLocaleString()],
            [
              "Opportunity",
              new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(stats.total_monthly_opportunity),
            ],
            ["Mean score", String(stats.avg_lead_score)],
          ].map(([k, v], i) => (
            <motion.div
              key={k}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-2xl border border-white/[0.06] bg-card/80 p-4 shadow-card backdrop-blur-sm"
            >
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">{k}</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums text-white">{v}</p>
            </motion.div>
          ))}
        </div>
      ) : null}

      <section className="space-y-4">
        <div className="flex flex-col gap-4 rounded-2xl border border-white/[0.06] bg-card/40 p-4 shadow-card backdrop-blur-sm sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 flex-1">
              <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
                Search
              </label>
              <input
                className="input-intel mt-2"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Business name…"
              />
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-600 sm:text-right">
                Queue mode
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setAutopilot(true)}
                  className={`rounded-xl px-4 py-2.5 text-[13px] font-semibold transition ${
                    autopilot
                      ? "bg-accent text-zinc-950 shadow-[0_0_24px_-4px_rgba(232,255,71,0.45)]"
                      : "bg-white/[0.06] text-zinc-300 ring-1 ring-white/[0.08] hover:bg-white/[0.09]"
                  }`}
                >
                  Autopilot queue
                </button>
                <button
                  type="button"
                  onClick={() => setAutopilot(false)}
                  className={`rounded-xl px-4 py-2.5 text-[13px] font-medium transition ${
                    !autopilot
                      ? "bg-white/[0.1] text-white ring-1 ring-accent/25"
                      : "bg-white/[0.04] text-zinc-500 ring-1 ring-white/[0.06] hover:text-zinc-300"
                  }`}
                >
                  Manual filters
                </button>
              </div>
            </div>
          </div>

          {autopilot ? (
            <p className="text-[13px] leading-relaxed text-zinc-500">
              <span className="text-zinc-400">Active:</span> chains deprioritized · app-like / SPA shells filtered out
              · ranked by score, then static-site fit, then SMB index. Re-analyze older rows to populate site shape
              signals.
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-3 border-t border-white/[0.06] pt-4">
            {apiBase ? (
              <a
                href={leadsExportCsvUrl(
                  autopilot
                    ? { autopilot: true }
                    : {
                        minScore,
                        excludeLikelyChain: hideChains,
                        preferStatic: preferStatic,
                      }
                )}
                className="inline-flex items-center rounded-lg bg-white/[0.06] px-3 py-2 text-[13px] font-medium text-accent ring-1 ring-white/[0.08] transition hover:bg-white/[0.1]"
                target="_blank"
                rel="noreferrer"
              >
                Export CSV
              </a>
            ) : null}
          </div>

          {!autopilot ? (
            <div className="space-y-4 border-t border-white/[0.06] pt-4">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
                    Min score · {minScore}
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={minScore}
                    onChange={(e) => setMinScore(Number(e.target.value))}
                    className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-full bg-zinc-800 accent-accent"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
                    Pipeline
                  </label>
                  <select
                    className="input-intel mt-2"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                  >
                    <option value="">All states</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="interested">Interested</option>
                    <option value="won">Won</option>
                    <option value="skip">Skip</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
                    Sort
                  </label>
                  <select
                    className="input-intel mt-2"
                    value={sort}
                    onChange={(e) => setSort(e.target.value as typeof sort)}
                  >
                    <option value="lead_score">Lead score</option>
                    <option value="smb_fit">SMB fit index</option>
                    <option value="revenue">Revenue</option>
                    <option value="newest">Newest</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
                    SMB tier
                  </label>
                  <select
                    className="input-intel mt-2"
                    value={smbTier}
                    onChange={(e) => setSmbTier(e.target.value)}
                  >
                    <option value="">Any</option>
                    <option value="ideal_smb">Ideal local</option>
                    <option value="borderline">Borderline</option>
                    <option value="likely_chain">Likely chain</option>
                  </select>
                </div>
              </div>
              <div className="flex flex-wrap gap-6 text-[13px] text-zinc-500">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={hideChains}
                    onChange={(e) => setHideChains(e.target.checked)}
                    className="rounded border-zinc-600 bg-zinc-900 accent-accent"
                  />
                  Hide likely chains
                </label>
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferStatic}
                    onChange={(e) => setPreferStatic(e.target.checked)}
                    className="rounded border-zinc-600 bg-zinc-900 accent-accent"
                  />
                  Prefer brochure / static HTML (drop app-like)
                </label>
              </div>
            </div>
          ) : null}
        </div>

        <div className="space-y-3 pt-2">
          {leads.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/[0.08] px-6 py-16 text-center">
              <p className="text-sm font-medium text-zinc-400">No leads in view</p>
              <p className="mt-2 text-[13px] text-zinc-600">
                {stats && stats.total_leads > 0 ? (
                  <>
                    You have <span className="text-zinc-500">{stats.total_leads}</span> in the corpus —
                    {autopilot ? (
                      <>
                        {" "}
                        Autopilot hides SPA-style sites; switch to{" "}
                        <span className="text-zinc-500">Manual filters</span> to see everything, or re-run analysis
                        for site-shape data.
                      </>
                    ) : (
                      <>
                        {" "}
                        try lowering <span className="text-zinc-500">min score</span> or toggling filters.
                      </>
                    )}
                  </>
                ) : (
                  <>Run a scan to populate the corpus.</>
                )}
              </p>
              <Link
                href="/scan"
                className="mt-6 inline-flex rounded-lg bg-white/[0.06] px-4 py-2 text-[13px] font-medium text-white ring-1 ring-white/[0.08] transition hover:bg-white/[0.1]"
              >
                Start scan
              </Link>
            </div>
          ) : (
            leads.map((l, idx) => (
              <motion.div
                key={l.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(idx * 0.03, 0.4) }}
              >
                <LeadCard lead={l} />
              </motion.div>
            ))
          )}
        </div>
      </section>

      {apiBase ? (
        <p className="text-center text-[10px] text-zinc-700">
          API · <span className="font-mono text-zinc-600">{apiBase}</span>
        </p>
      ) : null}
    </div>
  );
}
