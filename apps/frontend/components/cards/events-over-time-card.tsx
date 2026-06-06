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
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { getMetrics } from "@/lib/api";
import { formatBucketLabel, type Interval } from "@/lib/time";
import { useAsyncFetch } from "@/hooks/use-async-fetch";
import { EVENTS_CHART_CONFIG } from "./shared";

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
  const { data, loading, updating, error } = useAsyncFetch(
    () => getMetrics({ type: type === "all" ? undefined : type, from, to, interval }),
    [type, from, to, interval, refreshNonce],
  );

  const total = React.useMemo(
    () => data?.series.reduce<number>((sum, p) => sum + p.count, 0) ?? 0,
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
          <ChartContainer config={EVENTS_CHART_CONFIG}>
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
