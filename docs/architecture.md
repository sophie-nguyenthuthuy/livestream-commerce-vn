# Architecture

## Goals

1. **Per-minute conversion analytics** at livestream cadence (writes come in waves of hundreds of events per second during peaks).
2. **Vietnamese-native AI script generation** — Northern and Southern dialects, conditioned on product/persona/intent.
3. **Statistically honest A/B testing** — never declare a winner on noise.

## Components

### Ingest
TikTok Shop pushes webhook events (orders, comments, viewers) to `POST /api/v1/streams/{id}/events`. Events are batched by the sender and aggregated server-side into per-minute buckets via `INSERT … ON CONFLICT DO UPDATE`. Concurrent viewers take MAX within a bucket; everything else takes SUM.

### Storage
- **PostgreSQL 16 + TimescaleDB**. `stream_minutes` is promoted to a hypertable with 7-day chunks. Heavy reads (last 4 hours of a live stream) hit the most recent chunk; cold reads (historical reports) hit older chunks.
- **Redis** holds live counters for the dashboard live tile and the host-facing "right now" widget. Source of truth remains Postgres.
- **MinIO** (S3-compatible) stores thumbnail variants for A/B tests.

### Services
- `script_service.py` calls Anthropic Claude (primary) or OpenAI (fallback) with a system prompt that pins the model to Vietnamese-first writing and TikTok Shop compliance rules. Dialect style guides are conservative — they encode lexical markers actually used by hosts, not academic linguistics.
- `ab_test_service.py` models each variant's CTR as Beta-Bernoulli. `prob_best` is estimated via Monte Carlo sampling (`scipy.stats` + numpy). A winner is declared only when both guardrails pass: (a) every variant has ≥ `min_impressions_per_variant`, and (b) the leader's `prob_best` ≥ `confidence_target`.
- `stream_service.py` handles event aggregation and conversion funnel math.

### Frontend
Next.js 14 App Router. Pages are server components by default; the script generator is the one interactive client component. Recharts for visualization.

## Why TimescaleDB instead of ClickHouse?

We considered both. Choosing TimescaleDB because:
- 1 database, 1 query language, 1 migration story.
- Per-minute granularity at our expected scale (≤ 100 concurrent live streams in year 1, ≤ 10k peak events/min/stream) sits comfortably inside Postgres with a hypertable.
- Continuous aggregates can replace materialized views once the data set crosses the line where minute-by-minute scans get slow.

We will revisit if a single host crosses 100k concurrent viewers regularly.

## Data flow

```
TikTok webhook ──▶ FastAPI ingest ──▶ Postgres (stream_minutes)
                                  └─▶ Redis (live counters)

Host opens dashboard ──▶ Next.js (server) ──▶ FastAPI ──▶ Postgres

Host requests AI script ──▶ Next.js (client) ──▶ FastAPI ──▶ Anthropic / OpenAI
                                                          └─▶ Postgres (saved)

Host views A/B result ──▶ Next.js (server) ──▶ FastAPI ──▶ Postgres aggregate
                                                       └─▶ scipy MC eval
```

## Out of scope (for now)

- Personalization / RAG over the host's past top-converting scripts. Stub `prompt_hash` field is there to bucket prompts for evaluation later.
- Real-time WebSocket dashboard. Polling at 10s is good enough; promote to WS when we have multi-host operator rooms.
- Multi-tenancy and SSO. Single-tenant install per agency in beta.
