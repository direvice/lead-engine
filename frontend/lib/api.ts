import { apiUrl } from "./api-base";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(apiUrl(path), {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

export function getStats() {
  return fetchJson<import("./types").Stats>("/api/stats");
}

export function getLeads(params: Record<string, string | number | undefined>) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") q.set(k, String(v));
  });
  return fetchJson<{ items: import("./types").Lead[]; count: number }>(`/api/leads?${q}`);
}

export function getLead(id: number) {
  return fetchJson<import("./types").Lead>(`/api/leads/${id}`);
}

export function patchLead(id: number, body: { status?: string; notes?: string }) {
  return fetchJson<import("./types").Lead>(`/api/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function startScan(body: {
  location: string;
  radius_miles: number;
  categories: string[];
}) {
  return fetchJson<{ job_id: number; status: string }>("/api/scan", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function scanStatus(jobId: number) {
  return fetchJson<{
    id: number;
    status: string;
    progress_current: number;
    progress_total: number;
    message: string | null;
    leads_found: number;
  }>(`/api/scan/${jobId}`);
}

export function botStatus() {
  return fetchJson<{ message: string; next_scan_hint: string }>("/api/bot-status");
}

export function analyticsSummary() {
  return fetchJson<{ funnel: Record<string, number> }>("/api/analytics/summary");
}

export function teachLead(id: number, signal: "good_target" | "bad_target") {
  return fetchJson<{ ok: boolean; pattern?: string; bucket?: { good: number; bad: number } }>(
    `/api/leads/${id}/teach`,
    { method: "POST", body: JSON.stringify({ signal }) }
  );
}

export type IntelligenceBrief = {
  learned_signals_stored: number;
  pattern_updates: number;
  top_patterns: {
    pattern: string;
    good: number;
    bad: number;
    n: number;
    net_confidence: number;
  }[];
  coaching_hint: string;
};

export function getIntelligenceBrief() {
  return fetchJson<IntelligenceBrief>("/api/intelligence/brief");
}
