import type { TimeRange } from "./time";

export const EVENT_TYPES = ["signup", "click", "purchase"] as const;
export type EventType = (typeof EVENT_TYPES)[number] | "all";

const WEIGHTS: Record<string, number> = { signup: 1, click: 4, purchase: 2 };

export function weightedRandomType(): string {
  const total = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (const [type, w] of Object.entries(WEIGHTS)) {
    r -= w;
    if (r <= 0) return type;
  }
  return "signup";
}

export function makeEvent(type: string): {
  event_id: string;
  type: string;
  ts: string;
} {
  return {
    event_id: crypto.randomUUID(),
    type,
    ts: new Date().toISOString(),
  };
}

export function seedEvents(
  range: TimeRange,
  count = 200
): Array<{ event_id: string; type: string; ts: string }> {
  const fromMs = new Date(range.from).getTime();
  const toMs = new Date(range.to).getTime();
  const span = toMs - fromMs;
  return Array.from({ length: count }, () => {
    const ts = new Date(fromMs + Math.random() * span).toISOString();
    return { event_id: crypto.randomUUID(), type: weightedRandomType(), ts };
  });
}

export async function throttledFire(
  events: Array<{ event_id: string; type: string; ts: string }>,
  fireFn: (event: { event_id: string; type: string; ts: string }) => Promise<unknown>,
  chunkSize = 10,
  delayMs = 150,
): Promise<void> {
  for (let i = 0; i < events.length; i += chunkSize) {
    const chunk = events.slice(i, i + chunkSize);
    await Promise.all(chunk.map(fireFn));
    if (i + chunkSize < events.length) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
}
