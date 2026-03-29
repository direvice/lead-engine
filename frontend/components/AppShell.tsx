"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const nav = [
  { href: "/", label: "Command" },
  { href: "/scan", label: "Run" },
  { href: "/analytics", label: "Signals" },
  { href: "/settings", label: "System" },
];

export function AppShell({
  children,
  botLine,
  apiConnected,
}: {
  children: React.ReactNode;
  botLine?: string;
  apiConnected?: boolean | null;
}) {
  const pathname = usePathname();

  return (
    <div className="relative min-h-screen mesh-bg">
      <div className="pointer-events-none fixed inset-0 grid-overlay" aria-hidden />

      <header className="sticky top-0 z-50 glass-nav">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="group flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 ring-1 ring-accent/25">
              <span className="h-2 w-2 rounded-full bg-accent shadow-glow animate-pulse-soft" />
            </span>
            <div className="leading-tight">
              <span className="block text-[13px] font-semibold tracking-tight text-white group-hover:text-accent transition-colors">
                Lead Engine
              </span>
              <span className="block text-[10px] uppercase tracking-[0.2em] text-zinc-600">
                Autonomous
              </span>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 sm:flex" aria-label="Main">
            {nav.map(({ href, label }) => {
              const active =
                href === "/"
                  ? pathname === "/"
                  : pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  className="relative px-3 py-2 text-[13px] font-medium text-zinc-500 transition-colors hover:text-zinc-200"
                >
                  {active ? (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-lg bg-white/[0.06] ring-1 ring-white/[0.06]"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  ) : null}
                  <span className="relative z-10">{label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            {apiConnected === false ? (
              <span className="hidden text-[11px] text-amber-400/90 sm:block" title="Set NEXT_PUBLIC_API_URL on Vercel">
                API offline
              </span>
            ) : null}
            <div className="hidden max-w-[200px] truncate text-right text-[11px] text-zinc-500 lg:block">
              {botLine ? (
                <>
                  <span className="text-zinc-600">State · </span>
                  <span className="text-zinc-400">{botLine}</span>
                </>
              ) : (
                <span className="text-zinc-600">Synchronizing…</span>
              )}
            </div>
            <Link
              href="/scan"
              className="rounded-lg bg-accent px-3 py-2 text-[12px] font-semibold text-black transition hover:bg-[#f0ff6a] sm:px-4"
            >
              Scan
            </Link>
          </div>
        </div>

        <nav className="flex border-t border-white/[0.04] px-4 py-2 sm:hidden" aria-label="Mobile">
          <div className="flex w-full justify-between gap-1">
            {nav.map(({ href, label }) => {
              const active =
                href === "/"
                  ? pathname === "/"
                  : pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`rounded-md px-2 py-1.5 text-[11px] font-medium ${
                    active ? "bg-white/10 text-white" : "text-zinc-500"
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl px-4 pb-20 pt-8 sm:px-6 sm:pt-10">{children}</main>

      <footer className="relative z-10 border-t border-white/[0.04] py-6 text-center text-[11px] text-zinc-600">
        Lead Engine · local intelligence layer
      </footer>
    </div>
  );
}
