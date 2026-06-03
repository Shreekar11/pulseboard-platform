export type Period = "24h" | "7d" | "30d";
export type Interval = "hour" | "day";

export interface TimeRange {
  from: string; // ISO UTC
  to: string; // ISO UTC
}

export function periodToRange(period: Period): TimeRange {
  const now = new Date();
  const to = now.toISOString();
  const fromDate = new Date(now);
  if (period === "24h") fromDate.setHours(fromDate.getHours() - 24);
  else if (period === "7d") fromDate.setDate(fromDate.getDate() - 7);
  else fromDate.setDate(fromDate.getDate() - 30);
  return { from: fromDate.toISOString(), to };
}

export const PERIOD_OPTIONS: { label: string; value: Period }[] = [
  { label: "Last 24 hours", value: "24h" },
  { label: "Last 7 days", value: "7d" },
  { label: "Last 30 days", value: "30d" },
];

export const INTERVAL_OPTIONS: { label: string; value: Interval }[] = [
  { label: "Hour", value: "hour" },
  { label: "Day", value: "day" },
];

export function formatBucketLabel(bucket: string, interval: Interval): string {
  const d = new Date(bucket);
  if (interval === "hour") {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}
