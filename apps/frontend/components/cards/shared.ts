import type { ChartConfig } from "@/components/ui/chart";

export const TOP_N = 10;

export const EVENTS_CHART_CONFIG = {
  count: { label: "Events", color: "hsl(var(--primary))" },
} satisfies ChartConfig;

export const TOP_TYPES_CHART_CONFIG = {
  count: { label: "Count", color: "hsl(var(--primary))" },
} satisfies ChartConfig;
