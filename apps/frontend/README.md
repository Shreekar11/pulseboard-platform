# PulseBoard Frontend

Event analytics dashboard. Built with Next.js 16, shadcn/ui, Recharts.

## Local Development

**Prerequisites:** Docker, Node.js 20+, pnpm

**1. Start the backend stack:**
```bash
# From repo root
docker compose up -d
```

This starts Postgres, Redis, the FastAPI backend, and the rollup worker.

**2. Install frontend dependencies:**
```bash
cd apps/frontend
pnpm install
```

**3. Generate TypeScript types from the OpenAPI spec:**
```bash
make generate
```

**4. Start the dev server:**
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## API Configuration

The frontend calls the backend at `NEXT_PUBLIC_API_BASE_URL` (set in `.env.local`).

| Environment | Value |
|---|---|
| Local dev | `http://localhost:8000` |
| Production | (empty — uses relative `/api` via ingress) |

## Project Structure

```
app/           Next.js App Router pages and layouts
components/    Shared React components
  ui/          shadcn/ui component library
lib/           Utilities and API layer
  api.ts       Typed fetch wrapper
  types.ts     Re-exported generated types
  events.ts    Event helpers (seed, fire)
  time.ts      Period presets and formatters
  generated/   Generated from OpenAPI spec (do not edit)
openapi/       Synced OpenAPI spec (do not edit)
```
