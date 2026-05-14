# Livestream Commerce VN

Analytics & AI co-pilot for TikTok Shop livestream sellers in Vietnam.

TikTok Shop VN crossed **$1.3B GMV in 2024** and livestream drives the bulk of it. Existing tooling is Chinese-only (Feigua, Chanmama, Youshu). This platform is built for Vietnamese hosts and operators.

## What it does

- **Per-minute conversion analytics** — viewers, comments, click-through, orders, GMV, AOV, CVR computed in 60-second buckets and streamed to a live dashboard.
- **AI script generator** — hook, objection-handling, and closing scripts generated in Northern (Hà Nội) or Southern (Sài Gòn) Vietnamese, conditioned on product, price band, and audience profile.
- **Thumbnail A/B testing** — multi-variant tests with Bayesian winner selection and minimum-sample guardrails so hosts don't ship on noise.

## Architecture

```
┌──────────────┐    ingest    ┌──────────────┐
│ TikTok Shop  │─────────────▶│   FastAPI    │
│  webhooks    │              │   ingestor   │
└──────────────┘              └──────┬───────┘
                                     │
              ┌──────────────────────┼───────────────────────┐
              ▼                      ▼                       ▼
       ┌────────────┐         ┌────────────┐          ┌────────────┐
       │ PostgreSQL │         │   Redis    │          │   Worker   │
       │TimescaleDB │         │  counters  │          │  (arq)     │
       └─────┬──────┘         └─────┬──────┘          └─────┬──────┘
             │                      │                        │
             └──────────────────────┼────────────────────────┘
                                    ▼
                          ┌──────────────────┐
                          │  Next.js 14 App  │
                          └──────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for the full picture.

## Quickstart

```bash
cp .env.example .env
make up           # postgres + redis + minio + backend + frontend + worker
make migrate      # apply alembic migrations
make seed         # load demo stream + products
open http://localhost:3000
```

## Repo layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI service, models, AI services, A/B test math |
| `frontend/` | Next.js 14 dashboard (App Router) |
| `infra/` | Dockerfiles, k8s manifests, terraform stubs |
| `docs/` | Architecture, API reference, runbooks |
| `scripts/` | Seed data, load testing, ops utilities |

## Status

Pre-launch. Targeting closed beta with 20 mid-tier hosts in Q3 2026.

## License

Apache-2.0
