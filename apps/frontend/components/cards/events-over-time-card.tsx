"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { getMetrics } from "@/lib/api";
import type { MetricsResponse } from "@/lib/types";
import { formatBucketLabel, type Interval } from "@/lib/time";

const chartConfig = {
  count: {
    label: "Events",
    color: "hsl(var(--primary))",
  },
} satisfies ChartConfig;

export interface EventsOverTimeCardProps {
  type: string;
  from: string;
  to: string;
  interval: Interval;
  refreshNonce: number;
}

export function EventsOverTimeCard({
  type,
  from,
  to,
  interval,
  refreshNonce,
}: EventsOverTimeCardProps) {
  const [data, setData] = React.useState<MetricsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [updating, setUpdating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    setError(null);
    setData((prev) => {
      if (prev) setUpdating(true);
      else setLoading(true);
      return prev;
    });

    getMetrics({
      type: type === "all" ? undefined : type,
      from,
      to,
      interval,
    })
      .then((res) => {
        if (cancelled) return;
        setData(res);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load metrics");
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
        setUpdating(false);
      });

    return () => {
      cancelled = true;
    };
  }, [type, from, to, interval, refreshNonce]);

  const total = React.useMemo(
    () => data?.series.reduce((sum, p) => sum + p.count, 0) ?? 0,
    [data],
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">
            Events over time
          </CardTitle>
          {updating && (
            <span className="text-xs text-muted-foreground">Updating…</span>
          )}
        </div>
        {loading && !data ? (
          <Skeleton className="h-9 w-24" />
        ) : (
          <div className="text-3xl font-semibold tabular-nums">
            {total.toLocaleString()}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {loading && !data ? (
          <Skeleton className="aspect-video w-full" />
        ) : error && !data ? (
          <div className="flex aspect-video items-center justify-center text-sm text-muted-foreground">
            {error}
          </div>
        ) : (
          <ChartContainer config={chartConfig}>
            <AreaChart
              data={data?.series ?? []}
              margin={{ left: 0, right: 12, top: 4 }}
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="bucket"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={24}
                tickFormatter={(value: string) =>
                  formatBucketLabel(value, interval)
                }
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    labelFormatter={(_, payload) => {
                      const bucket = payload?.[0]?.payload?.bucket as
                        | string
                        | undefined;
                      return bucket
                        ? formatBucketLabel(bucket, interval)
                        : "";
                    }}
                  />
                }
              />
              <Area
                dataKey="count"
                type="monotone"
                fill="var(--color-count)"
                fillOpacity={0.2}
                stroke="var(--color-count)"
                strokeWidth={2}
              />
            </AreaChart>
          </ChartContainer>
        )}
        <p className="mt-3 text-xs text-muted-foreground">
          Eventually consistent — rollups may lag a few seconds.
        </p>
      </CardContent>
    </Card>
  );
}
