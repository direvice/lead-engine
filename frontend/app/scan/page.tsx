"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { scanStatus, startScan } from "@/lib/api";

const DEFAULT_CATS = ["restaurant", "cafe", "beauty_salon", "hair_care"];

export default function ScanPage() {
  const [location, setLocation] = useState("Geneva, IL");
  const [radius, setRadius] = useState(15);
  const [cats, setCats] = useState(DEFAULT_CATS.join(", "));
  const [jobId, setJobId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    if (jobId == null) return;
    const id = setInterval(() => {
      scanStatus(jobId)
        .then((s) => {
          setStatus(
            `${s.message ?? ""} · ${s.progress_current}/${s.progress_total} · ${s.leads_found} analyzed`
          );
          if (s.status === "done" || s.status === "failed") clearInterval(id);
        })
        .catch(() => clearInterval(id));
    }, 3000);
    return () => clearInterval(id);
  }, [jobId]);

  return (
    <div className="mx-auto max-w-lg space-y-10">
      <div>
        <p className="text-[11px] font-medium uppercase tracking-[0.25em] text-zinc-600">Execute</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Run scan</h1>
        <p className="mt-3 text-[15px] leading-relaxed text-zinc-500">
          No Google key? Geocoding uses free OpenStreetMap (Nominatim). Discovery uses OSM, Yelp (optional
          key), Yellowpages, and Places only if you set a Google key.
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-5 rounded-2xl border border-white/[0.06] bg-card/60 p-6 backdrop-blur-sm"
      >
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
            Location
          </label>
          <input
            className="input-intel mt-2"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
            Radius (mi)
          </label>
          <input
            type="number"
            className="input-intel mt-2"
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">
            Categories
          </label>
          <input
            className="input-intel mt-2 font-mono text-[13px]"
            value={cats}
            onChange={(e) => setCats(e.target.value)}
            placeholder="Comma-separated Place types"
          />
        </div>
        <button
          type="button"
          className="w-full rounded-xl bg-accent py-3.5 text-[14px] font-semibold text-black transition hover:bg-[#f0ff6a]"
          onClick={async () => {
            const list = cats
              .split(",")
              .map((c) => c.trim())
              .filter(Boolean);
            try {
              const r = await startScan({ location, radius_miles: radius, categories: list });
              setJobId(r.job_id);
              setStatus("Job accepted…");
            } catch {
              setStatus("Failed to start — check API and keys.");
            }
          }}
        >
          Start scan
        </button>
        {status ? (
          <p className="text-center text-[12px] leading-relaxed text-zinc-500">{status}</p>
        ) : null}
      </motion.div>

      <p className="text-center text-[12px] text-zinc-600">
        <Link href="/" className="text-zinc-400 hover:text-white">
          ← Command
        </Link>
      </p>
    </div>
  );
}
