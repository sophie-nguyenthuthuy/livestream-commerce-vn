# API reference

Base URL: `/api/v1`

OpenAPI is auto-generated and browsable at `/docs` when the backend is running. The reference below covers the integration surface a host operator's tooling will need.

## Streams

### `POST /streams`
Register a livestream session.
```json
{
  "platform": "TIKTOK_SHOP",
  "platform_stream_id": "7311…",
  "host_handle": "@hostname.vn",
  "title": "Flash sale skincare",
  "started_at": "2026-05-14T12:00:00Z"
}
```

### `POST /streams/{id}/events`
Batch ingest. Each event is one sample of stream state; the server aggregates into 1-minute buckets idempotently.
```json
{
  "events": [
    {
      "occurred_at": "2026-05-14T12:01:30Z",
      "concurrent_viewers": 820,
      "new_viewers": 42,
      "comments": 33,
      "product_clicks": 19,
      "add_to_carts": 8,
      "orders": 3,
      "gmv_vnd": "549000",
      "featured_product_id": "…"
    }
  ]
}
```
Returns `202 Accepted` with `{"buckets_upserted": N, "events_received": M}`.

### `GET /streams/{id}/minutes?limit=240`
Per-minute time series, oldest first.

### `GET /streams/{id}/conversion`
Cumulative funnel (viewers → clicks → carts → orders) plus GMV and AOV.

### `POST /streams/{id}/end`
Finalize aggregates, set status to `ENDED`.

## Scripts

### `POST /scripts/generate`
Generate N script variants in a Vietnamese dialect.
```json
{
  "dialect": "SOUTH",
  "intent": "HOOK",
  "product_name": "Serum Vitamin C 30ml",
  "product_category": "skincare",
  "price_band": "under-200k",
  "audience_persona": "Nữ 25-35, da dầu",
  "target_duration_sec": 30,
  "n_variants": 3
}
```
Response includes the model used and the parsed variant array.

### `POST /scripts`
Persist a generated (or hand-written) variant for reuse.

### `GET /scripts?dialect=SOUTH&intent=HOOK`
List saved templates, ordered by upvotes then recency.

### `POST /scripts/{id}/upvote`
Increment the upvote counter — used to rank templates over time.

## A/B tests

### `POST /ab-tests`
Create with 2–6 variants. Variant weights must sum to 100.

### `POST /ab-tests/{id}/start`
Move from `DRAFT` to `RUNNING`. Sets `started_at` if first time.

### `POST /ab-tests/{id}/events`
Bulk record `IMPRESSION` or `CLICK` events with a `session_hash` for dedup.

### `GET /ab-tests/{id}/results`
Compute current results. Returns per-variant CTR, 95% credible interval, and `prob_best` (Bayesian probability the variant has the highest true CTR). If guardrails pass, the test is auto-promoted to `DECIDED` and `winner_variant_id` is set.

## Auth

Webhook endpoints validate HMAC-SHA256 against `TIKTOK_WEBHOOK_SECRET`. Dashboard endpoints assume a trusted internal network in beta; bearer tokens land in milestone 2.
