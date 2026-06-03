"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

type HealthState = "healthy" | "unhealthy" | "unknown";

export function HealthDot() {
  const [health, setHealth] = useState<HealthState>("unknown");

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        await getHealth();
        if (!cancelled) setHealth("healthy");
      } catch {
        if (!cancelled) setHealth("unhealthy");
      }
    }

    check();
    const id = setInterval(check, 10_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const color =
    health === "healthy"
      ? "bg-green-500"
      : health === "unhealthy"
      ? "bg-red-500"
      : "bg-yellow-400";

  const label =
    health === "healthy" ? "healthy" : health === "unhealthy" ? "unhealthy" : "checking…";

  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  );
}
