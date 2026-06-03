import type {
  EventIn,
  EventAccepted,
  MetricsResponse,
  TopResponse,
  InfoResponse,
  HealthStatus,
} from "./types";
import type { Interval } from "./time";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.error?.message ?? `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export function postEvent(event: EventIn): Promise<EventAccepted> {
  return request<EventAccepted>("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
}

export interface MetricsParams {
  type?: string; // omit for all-types aggregate
  from: string; // ISO UTC datetime
  to: string; // ISO UTC datetime
  interval: Interval;
}

export function getMetrics(params: MetricsParams): Promise<MetricsResponse> {
  const q = new URLSearchParams();
  if (params.type) q.set("type", params.type);
  q.set("from", params.from);
  q.set("to", params.to);
  q.set("interval", params.interval);
  return request<MetricsResponse>(`/api/metrics?${q}`);
}

export interface TopParams {
  from: string;
  to: string;
  limit?: number;
}

export function getTop(params: TopParams): Promise<TopResponse> {
  const q = new URLSearchParams({
    dimension: "type",
    from: params.from,
    to: params.to,
  });
  if (params.limit) q.set("limit", String(params.limit));
  return request<TopResponse>(`/api/metrics/top?${q}`);
}

export function getInfo(): Promise<InfoResponse> {
  return request<InfoResponse>("/api/info");
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/healthz");
}
