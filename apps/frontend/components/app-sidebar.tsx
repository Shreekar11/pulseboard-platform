"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { HealthDot } from "@/components/health-dot";
import { FireEvents } from "@/components/fire-events";
import type { TimeRange } from "@/lib/time";

const SERVICES = ["AWS us-east-1", "GCP europe-west1", "Azure eastus"] as const;

interface AppSidebarProps {
  firedCount: number;
  range: TimeRange;
  onFired: (count: number) => void;
}

export function AppSidebar({ firedCount, range, onFired }: AppSidebarProps) {
  return (
    <aside className="flex h-full w-56 flex-col border-r bg-background">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-4">
        <span className="text-base font-bold tracking-tight">⚡ PulseBoard</span>
      </div>

      {/* Cosmetic service selector — echoes ClickHouse, no real behavior */}
      <div className="px-3 pb-2">
        <Select defaultValue={SERVICES[0]}>
          <SelectTrigger className="h-7 w-full text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SERVICES.map((s) => (
              <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Separator />

      {/* Nav */}
      <nav className="px-3 py-2">
        <div className="flex items-center gap-2 rounded-md bg-accent px-2 py-1.5 text-xs font-medium text-accent-foreground">
          <span>Overview</span>
        </div>
      </nav>

      <Separator />

      {/* Fire Events */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <FireEvents range={range} onFired={onFired} />
      </div>

      <Separator />

      {/* Footer */}
      <div className="px-4 py-3 space-y-1">
        <HealthDot />
        <p className="text-xs text-muted-foreground">
          fired: <span className="font-medium text-foreground">{firedCount}</span>
        </p>
      </div>
    </aside>
  );
}
