"use client";

import * as React from "react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface RecentActivityEvent {
  event_id: string;
  type: string;
  ts: string;
}

export interface RecentActivityCardProps {
  events: RecentActivityEvent[];
}

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function RecentActivityCard({ events }: RecentActivityCardProps) {
  const recent = React.useMemo(
    () => [...events].slice(-10).reverse(),
    [events],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        {recent.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No events fired yet. Use the sidebar to fire some events.
          </p>
        ) : (
          <ul className="space-y-2">
            {recent.map((event) => (
              <li
                key={event.event_id}
                className="flex items-center justify-between gap-2"
              >
                <Badge variant="secondary">{event.type}</Badge>
                <span className="font-mono text-xs text-muted-foreground tabular-nums">
                  {formatTime(event.ts)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
