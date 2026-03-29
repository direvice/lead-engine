/**
 * Browser: use NEXT_PUBLIC_API_URL when set (Vercel → your FastAPI host).
 * Empty → same-origin /api (Next dev rewrites to localhost:8000).
 */
export function getPublicApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim() || "";
  return raw.replace(/\/$/, "");
}

export function apiUrl(path: string): string {
  const base = getPublicApiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}
