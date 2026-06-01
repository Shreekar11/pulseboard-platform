# @pulseboard/frontend

Placeholder for the PulseBoard dashboard (Part 1 / Phase 2).

Planned stack: **React + Recharts** — fires a few sample events at `POST /api/events`
and renders a time-series chart from `GET /api/metrics`. Kept intentionally minimal;
the depth of this project is in the backend and the platform.

API contract consumed (stable — see backend):

- `GET /api/metrics` → `{ series: [{ bucket, count }] }`
- `GET /api/metrics/top` → `{ items: [{ type, count }] }`

> Not scaffolded yet. This directory exists so the Turborepo workspace and
> `docker-compose` topology are in place from the start.
