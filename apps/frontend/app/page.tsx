"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { TopBar } from "@/components/top-bar";
import { EventsOverTimeCard } from "@/components/cards/events-over-time-card";
import { TopEventTypesCard } from "@/components/cards/top-event-types-card";
import { ServiceDetailsCard } from "@/components/cards/service-details-card";
import {
  RecentActivityCard,
  type RecentActivityEvent,
} from "@/components/cards/recent-activity-card";
import type { Interval, Period } from "@/lib/time";
import { periodToRange } from "@/lib/time";
import type { EventType } from "@/lib/events";

export default function DashboardPage() {
  // ── Controls ──────────────────────────────────────────────────
  const [interval, setInterval] = useState<Interval>("hour");
  const [period, setPeriod] = useState<Period>("24h");
  const [eventType, setEventType] = useState<EventType>("all");

  // ── Derived time range ────────────────────────────────────────
  // Recomputed on every render; period changes → new range.
  const { from, to } = useMemo(() => periodToRange(period), [period]);

  // ── Refresh nonce ─────────────────────────────────────────────
  const [refreshNonce, setRefreshNonce] = useState(0);
  const autoRefreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const bumpNonce = useCallback(() => {
    setRefreshNonce((n) => n + 1);
  }, []);

  // ── Session counters + activity log ───────────────────────────
  const [firedCount, setFiredCount] = useState(0);
  // FireEvents only surfaces a count (not the event objects), so the activity
  // log stays empty for now — RecentActivityCard renders its own empty state.
  const activityLog = useMemo<RecentActivityEvent[]>(() => [], []);

  // Called by FireEvents after any fire/seed action.
  // count: number of events successfully fired (1 for single, N for seed, 1 for dup).
  const handleFired = useCallback(
    (count: number) => {
      setFiredCount((c) => c + count);
      // Auto-refetch ~2s after any fire to let the rollup worker catch up.
      if (autoRefreshTimer.current) clearTimeout(autoRefreshTimer.current);
      autoRefreshTimer.current = setTimeout(bumpNonce, 2000);
    },
    [bumpNonce],
  );

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      if (autoRefreshTimer.current) clearTimeout(autoRefreshTimer.current);
    };
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <AppSidebar
        firedCount={firedCount}
        range={{ from, to }}
        onFired={handleFired}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar
          interval={interval}
          period={period}
          eventType={eventType}
          onIntervalChange={setInterval}
          onPeriodChange={setPeriod}
          onEventTypeChange={setEventType}
          onRefresh={bumpNonce}
        />

        <main className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-3 gap-4">
            {/* Wide left column: charts */}
            <div className="col-span-2 space-y-4">
              <EventsOverTimeCard
                type={eventType}
                from={from}
                to={to}
                interval={interval}
                refreshNonce={refreshNonce}
              />
              <TopEventTypesCard
                from={from}
                to={to}
                refreshNonce={refreshNonce}
              />
            </div>

            {/* Narrow right column: details + activity */}
            <div className="col-span-1 space-y-4">
              <ServiceDetailsCard />
              <RecentActivityCard events={activityLog} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
