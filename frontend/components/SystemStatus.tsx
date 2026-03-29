"use client";

import { useEffect, useState } from "react";
import { getPublicApiBase } from "@/lib/api-base";
import { getStats } from "@/lib/api";

export function useApiConnection() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    getStats()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  return { connected, hasConfiguredUrl: Boolean(getPublicApiBase()) };
}
