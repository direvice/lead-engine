import Link from "next/link";
import { DigestPreview } from "@/components/DigestPreview";
import { getPublicApiBase } from "@/lib/api-base";

export default function SettingsPage() {
  const configured = getPublicApiBase();

  return (
    <div className="mx-auto max-w-xl space-y-10">
      <div>
        <p className="text-[11px] font-medium uppercase tracking-[0.25em] text-zinc-600">System</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Configuration</h1>
        <p className="mt-3 text-[15px] leading-relaxed text-zinc-500">
          Secrets stay on the server. The UI only needs a public API base on Vercel.
        </p>
      </div>

      <section className="rounded-2xl border border-white/[0.06] bg-card/60 p-6 backdrop-blur-sm">
        <h2 className="text-[13px] font-medium text-white">Vercel</h2>
        <p className="mt-2 text-[13px] leading-relaxed text-zinc-500">
          Set <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-[12px] text-accent">NEXT_PUBLIC_API_URL</code>{" "}
          to your deployed FastAPI origin (no trailing slash). Example:{" "}
          <code className="font-mono text-[11px] text-zinc-400">https://api.yourdomain.com</code>
        </p>
        <p className="mt-4 text-[12px] text-zinc-600">
          Build-time: this page SSR sees{" "}
          <span className="font-mono text-zinc-500">{configured || "(empty — dev rewrites)"}</span>
        </p>
      </section>

      <section className="rounded-2xl border border-white/[0.06] bg-card/60 p-6 backdrop-blur-sm">
        <h2 className="text-[13px] font-medium text-white">API server</h2>
        <ul className="mt-3 list-inside list-disc space-y-2 text-[13px] text-zinc-500">
          <li>
            <code className="font-mono text-zinc-400">CORS_ORIGINS</code> must include your Vercel URL
          </li>
          <li>
            <code className="font-mono text-zinc-400">GEOAPIFY_API_KEY</code> optional — replaces Google for Places-style discovery + geocode (free tier at geoapify.com)
          </li>
          <li>
            <code className="font-mono text-zinc-400">GOOGLE_PLACES_API_KEY</code> optional (Places + PageSpeed); or use OSM/Yelp/Geoapify only
          </li>
          <li>Ollama or Gemini for AI layers</li>
          <li>Optional Gmail vars for digest</li>
        </ul>
      </section>

      <section className="rounded-2xl border border-white/[0.06] bg-card/60 p-6 backdrop-blur-sm">
        <h2 className="text-[13px] font-medium text-white">Digest</h2>
        <div className="mt-3">
          <DigestPreview />
        </div>
      </section>

      <p className="text-center text-[12px] text-zinc-600">
        <Link href="/" className="text-zinc-400 hover:text-white">
          ← Command
        </Link>
      </p>
    </div>
  );
}
