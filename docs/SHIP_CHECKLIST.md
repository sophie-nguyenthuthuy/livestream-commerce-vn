# Ship checklist — livestream-commerce-vn

## 1. TikTok Shop integration

- [ ] **Apply for TikTok Shop API access** at <https://partner.tiktokshop.com>.
  - Required: registered seller account in VN with at least 30 days of
    trading history (TikTok's anti-fraud gate).
  - Get `TIKTOK_SHOP_APP_KEY` + `TIKTOK_SHOP_APP_SECRET` from the dev
    portal once approved.
- [ ] **Webhook secret**: configure in TikTok Shop developer console; copy
      into `.env` as `TIKTOK_WEBHOOK_SECRET`.
- [ ] **OAuth redirect URI** registered (must be HTTPS, no localhost in prod).

## 2. AI model

- [ ] **LLM tier**
  - Dev/laptop: `LLM_MODEL=qwen2.5:7b-instruct` (~4 GB) is the default.
  - Production: `qwen2.5:32b-instruct` produces noticeably better
    Vietnamese sales-pitch copy + dialect templating.

## 3. Object storage

- [ ] **MinIO bucket** `thumbnails` with public-read on `/public/*` prefix.
- [ ] **CDN** in front (free Cloudflare tier is enough — daily thumbnail
      churn is low).

## 4. Bayesian A/B harness

- [ ] **Per-tenant priors**: the thumbnail A/B service ships with a
      conservative prior. Tune per category after ~200 livestreams of data.
- [ ] **Auto-stop threshold**: default p > 0.95 — defendable but conservative.

## 5. Smoke before release

```
make smoke PROJECT=livestream-commerce-vn
cd backend && .venv/bin/pytest -q
```
