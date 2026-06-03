export type Period = "24h" | "7d" | "30d";
export type Interval = "hour" | "day" | "week";

export interface TimeRange {
  from: string; // ISO UTC
  to: string; // ISO UTC
}

export function periodToRange(period: Period): TimeRange {
  const now = new Date();
  const MS: Record<Period, number> = {
    "24h": 24 * 60 * 60_000,
    "7d": 7 * 24 * 60 * 60_000,
    "30d": 30 * 24 * 60 * 60_000,
  };
  return {
    from: new Date(now.getTime() - MS[period]).toISOString(),
    to: now.toISOString(),
  };
}

export const PERIOD_OPTIONS: { label: string; value: Period }[] = [
  { label: "Last 24 hours", value: "24h" },
  { label: "Last 7 days", value: "7d" },
  { label: "Last 30 days", value: "30d" },
];

export const INTERVAL_OPTIONS: { label: string; value: Interval }[] = [
  { label: "Hour", value: "hour" },
  { label: "Day", value: "day" },
  { label: "Week", value: "week" },
];

export function formatBucketLabel(bucket: string, interval: Interval): string {
  const d = new Date(bucket);
  if (interval === "hour") {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}
