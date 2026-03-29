"use client";

export function AudioPlayer({ src, label }: { src: string; label?: string }) {
  if (!src) return null;
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur-sm">
      <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        {label || "Briefing"}
      </p>
      <p className="mt-1 text-[12px] text-zinc-600">Listen while en route</p>
      <audio controls className="mt-4 w-full accent-accent" src={src}>
        <track kind="captions" />
      </audio>
    </div>
  );
}
