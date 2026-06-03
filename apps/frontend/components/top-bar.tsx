"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { INTERVAL_OPTIONS, PERIOD_OPTIONS, type Interval, type Period } from "@/lib/time";
import { EVENT_TYPES, type EventType } from "@/lib/events";

interface TopBarProps {
  interval: Interval;
  period: Period;
  eventType: EventType;
  onIntervalChange: (v: Interval) => void;
  onPeriodChange: (v: Period) => void;
  onEventTypeChange: (v: EventType) => void;
  onRefresh: () => void;
}

export function TopBar({
  interval,
  period,
  eventType,
  onIntervalChange,
  onPeriodChange,
  onEventTypeChange,
  onRefresh,
}: TopBarProps) {
  return (
    <div className="flex items-center justify-between border-b px-6 py-3">
      <h1 className="text-sm font-semibold text-foreground">Overview</h1>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Aggregation</span>
          <Select value={interval} onValueChange={(v) => onIntervalChange(v as Interval)}>
            <SelectTrigger className="h-7 w-[80px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INTERVAL_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value} className="text-xs">
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Period</span>
          <Select value={period} onValueChange={(v) => onPeriodChange(v as Period)}>
            <SelectTrigger className="h-7 w-[120px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PERIOD_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value} className="text-xs">
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Event type</span>
          <Select value={eventType} onValueChange={(v) => onEventTypeChange(v as EventType)}>
            <SelectTrigger className="h-7 w-[110px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="text-xs">All types</SelectItem>
              {EVENT_TYPES.map((t) => (
                <SelectItem key={t} value={t} className="text-xs">
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button variant="outline" size="sm" className="h-7 gap-1.5 text-xs" onClick={onRefresh}>
          <RefreshCw className="h-3 w-3" />
          Refresh
        </Button>
      </div>
    </div>
  );
}
