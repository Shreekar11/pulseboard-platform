"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { postEvent } from "@/lib/api";
import { EVENT_TYPES, makeEvent, seedEvents, throttledFire, type EventType } from "@/lib/events";
import type { TimeRange } from "@/lib/time";

interface FireEventsProps {
  range: TimeRange;
  onFired: (count: number) => void;
}

export function FireEvents({ range, onFired }: FireEventsProps) {
  const [seeding, setSeeding] = useState(false);
  const [dupId, setDupId] = useState<string | null>(null);

  async function fireOne(type: string) {
    const ev = makeEvent(type);
    await postEvent(ev);
    onFired(1);
  }

  async function handleSeed() {
    setSeeding(true);
    try {
      const events = seedEvents(range, 200);
      await throttledFire(events, postEvent);
      onFired(events.length);
    } finally {
      setSeeding(false);
    }
  }

  async function handleDuplicate() {
    // Fires the same event_id twice; backend deduplication means count rises by 1.
    const ev = dupId ? { event_id: dupId, type: "click", ts: new Date().toISOString() } : makeEvent("click");
    const id = ev.event_id;
    setDupId(id);
    await postEvent(ev);
    await postEvent({ ...ev, event_id: id }); // second send — same id
    onFired(1); // backend stores only one
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-2">
        Fire Events
      </p>
      <div className="space-y-1">
        {EVENT_TYPES.map((type) => (
          <Button
            key={type}
            variant="ghost"
            size="sm"
            className="w-full justify-start text-xs h-7"
            onClick={() => fireOne(type)}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Button>
        ))}
      </div>
      <Separator />
      <div className="space-y-1">
        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs h-7"
          onClick={handleSeed}
          disabled={seeding}
        >
          {seeding ? "Seeding…" : "Seed sample data"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs h-7"
          onClick={handleDuplicate}
        >
          Fire duplicate
        </Button>
      </div>
    </div>
  );
}
