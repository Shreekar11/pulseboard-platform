"use client";

import * as React from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

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
import { getTop } from "@/lib/api";
import type { TopItem } from "@/lib/types";

const chartConfig = {
  count: {
    label: "Events",
    color: "hsl(var(--primary))",
  },
} satisfies ChartConfig;

export interface TopEventTypesCardProps {
  from: string;
  to: string;
  refreshNonce: number;
}

export function TopEventTypesCard({
  from,
  to,
  refreshNonce,
}: TopEventTypesCardProps) {
  const [items, setItems] = React.useState<TopItem[] | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [updating, setUpdating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    setError(null);
    setItems((prev) => {
      if (prev) setUpdating(true);
      else setLoading(true);
      return prev;
    });

    getTop({ from, to, limit: 10 })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load top types",
        );
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
        setUpdating(false);
      });

    return () => {
      cancelled = true;
    };
  }, [from, to, refreshNonce]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">
            Top event types
          </CardTitle>
          {updating && (
            <span className="text-xs text-muted-foreground">Updating…</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading && !items ? (
          <Skeleton className="aspect-video w-full" />
        ) : error && !items ? (
          <div className="flex aspect-video items-center justify-center text-sm text-muted-foreground">
            {error}
          </div>
        ) : items && items.length === 0 ? (
          <div className="flex aspect-video items-center justify-center text-sm text-muted-foreground">
            No events in this range yet.
          </div>
        ) : (
          <ChartContainer config={chartConfig}>
            <BarChart
              data={items ?? []}
              layout="vertical"
              margin={{ left: 0, right: 12 }}
            >
              <CartesianGrid horizontal={false} />
              <XAxis type="number" hide />
              <YAxis
                dataKey="type"
                type="category"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                width={96}
              />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent hideLabel />}
              />
              <Bar
                dataKey="count"
                fill="var(--color-count)"
                radius={4}
              />
            </BarChart>
          </ChartContainer>
        )}
        <p className="mt-3 text-xs text-muted-foreground">
          Eventually consistent — rollups may lag a few seconds.
        </p>
      </CardContent>
    </Card>
  );
}
