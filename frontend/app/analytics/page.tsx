"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { analyticsSummary, getIntelligenceBrief, getLeads, type IntelligenceBrief } from "@/lib/api";

const COLORS = ["#e8ff47", "#c4d93a", "#9ca3af", "#52525b", "#3f3f46", "#27272a"];

export default function AnalyticsPage() {
  const [funnel, setFunnel] = useState<Record<string, number>>({});
  const [cats, setCats] = useState<{ name: string; value: number }[]>([]);
  const [brief, setBrief] = useState<IntelligenceBrief | null>(null);

  useEffect(() => {
    analyticsSummary().then((r) => setFunnel(r.funnel));
    getIntelligenceBrief().then(setBrief).catch(() => setBrief(null));
    getLeads({ limit: 500, sort: "newest", min_score: 0 }).then((r) => {
      const m: Record<string, number> = {};
      r.items.forEach((L) => {
        const k = L.category || "unknown";
        m[k] = (m[k] || 0) + 1;
      });
      setCats(
        Object.entries(m)
          .map(([name, value]) => ({ name, value }))
          .sort((a, b) => b.value - a.value)
          .slice(0, 8)
      );
    });
  }, []);

  const funnelData = Object.entries(funnel).map(([stage, count]) => ({ stage, count }));

  return (
    <div className="space-y-10">
      <div>
        <p className="text-[11px] font-medium uppercase tracking-[0.25em] text-zinc-600">Signals</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Analytics</h1>
        <p className="mt-3 max-w-lg text-[15px] text-zinc-500">
          Pipeline density and category distribution across your corpus.
        </p>
      </div>

      {brief ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-accent/20 bg-accent/[0.04] p-5 backdrop-blur-sm"
        >
          <h2 className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent">Learning layer</h2>
          <p className="mt-3 text-[14px] leading-relaxed text-zinc-300">{brief.coaching_hint}</p>
          <p className="mt-2 text-[12px] text-zinc-600">
            {brief.learned_signals_stored} stored signals · {brief.pattern_updates} pattern updates
          </p>
          {brief.top_patterns.length ? (
            <ul className="mt-4 space-y-2 border-t border-white/[0.06] pt-4 text-[12px] text-zinc-500">
              {brief.top_patterns.slice(0, 5).map((p) => (
                <li key={p.pattern} className="flex flex-wrap justify-between gap-2 font-mono text-[11px]">
                  <span className="text-zinc-400">{p.pattern}</span>
                  <span>
                    +{p.good} / −{p.bad} · net {p.net_confidence > 0 ? "+" : ""}
                    {p.net_confidence}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </motion.div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur-sm"
        >
          <h2 className="text-[13px] font-medium text-zinc-400">Pipeline</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="stage" stroke="#52525b" tick={{ fill: "#71717a", fontSize: 11 }} />
                <YAxis stroke="#52525b" tick={{ fill: "#71717a", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0c0c0c",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#fafafa" }}
                />
                <Bar dataKey="count" fill="#e8ff47" radius={[6, 6, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-2xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur-sm"
        >
          <h2 className="text-[13px] font-medium text-zinc-400">Categories</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={cats}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={88}
                  paddingAngle={2}
                >
                  {cats.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#0c0c0c",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <p className="text-center text-[12px] text-zinc-600">
        <Link href="/" className="text-zinc-400 hover:text-white">
          ← Command
        </Link>
      </p>
    </div>
  );
}
