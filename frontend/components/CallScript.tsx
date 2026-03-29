"use client";

import { useState } from "react";

export function CallScript({ script }: { script: string | null }) {
  const [open, setOpen] = useState(false);
  if (!script) return null;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-card/60 backdrop-blur-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <span className="text-[13px] font-medium text-white">Call script</span>
        <span className="text-accent">{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <div className="border-t border-white/[0.06] px-5 py-4">
          <pre className="whitespace-pre-wrap text-[13px] leading-relaxed text-zinc-400">{script}</pre>
          <button
            type="button"
            className="mt-4 text-[13px] font-medium text-accent hover:text-[#f0ff6a]"
            onClick={() => navigator.clipboard.writeText(script)}
          >
            Copy
          </button>
        </div>
      ) : null}
    </div>
  );
}
