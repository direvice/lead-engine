"use client";

import { useEffect, useState } from "react";
import { AppShell } from "./AppShell";
import { botStatus } from "@/lib/api";
import { useApiConnection } from "./SystemStatus";

export function Providers({ children }: { children: React.ReactNode }) {
  const [botLine, setBotLine] = useState("");
  const { connected } = useApiConnection();

  useEffect(() => {
    const tick = () =>
      botStatus()
        .then((b) => setBotLine(b.message || "Idle"))
        .catch(() => setBotLine("Unreachable"));
    tick();
    const id = setInterval(tick, 4000);
    return () => clearInterval(id);
  }, []);

  return (
    <AppShell botLine={botLine} apiConnected={connected}>
      {children}
    </AppShell>
  );
}
