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
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { getTop } from "@/lib/api";
import { useAsyncFetch } from "@/hooks/use-async-fetch";
import { TOP_N, TOP_TYPES_CHART_CONFIG } from "./shared";

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
  const { data, loading, updating, error } = useAsyncFetch(
    () => getTop({ from, to, limit: TOP_N }),
    [from, to, refreshNonce],
  );

  const items = data?.items ?? null;

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
          <ChartContainer config={TOP_TYPES_CHART_CONFIG}>
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
