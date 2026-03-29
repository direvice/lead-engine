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
import { analyticsSummary, getLeads } from "@/lib/api";

const COLORS = ["#e8ff47", "#c4d93a", "#9ca3af", "#52525b", "#3f3f46", "#27272a"];

export default function AnalyticsPage() {
  const [funnel, setFunnel] = useState<Record<string, number>>({});
  const [cats, setCats] = useState<{ name: string; value: number }[]>([]);

  useEffect(() => {
    analyticsSummary().then((r) => setFunnel(r.funnel));
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
