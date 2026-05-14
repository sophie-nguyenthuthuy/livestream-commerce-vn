# Deployment

## Local

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY or OPENAI_API_KEY (at least one) for /scripts/generate to work.
make up
make migrate
make seed
```

App: http://localhost:3000 · API: http://localhost:8000/docs · MinIO console: http://localhost:9001

## Production checklist

1. Set `APP_ENV=production`, generate a 32-byte `APP_SECRET_KEY`.
2. Point `DATABASE_URL` at managed Postgres with TimescaleDB enabled.
   - On RDS, use the [Timescale Cloud](https://www.timescale.com/) addon or self-host on EKS.
3. Lock `CORS_ORIGINS` to your frontend domain.
4. Build images:
   ```bash
   docker build -t ghcr.io/.../backend:$(git rev-parse --short HEAD) backend
   docker build -t ghcr.io/.../frontend:$(git rev-parse --short HEAD) frontend
   ```
5. Apply k8s manifests:
   ```bash
   kubectl apply -f infra/k8s/namespace.yaml
   kubectl create secret generic backend-env --from-env-file=.env.prod -n livestream-vn
   kubectl create configmap frontend-config --from-literal=api_base_url=https://api.livestream-vn.example/api/v1 -n livestream-vn
   kubectl apply -f infra/k8s/
   ```
6. Run migration as a one-shot Job (don't bake it into the entrypoint in prod):
   ```bash
   kubectl run alembic-upgrade --rm -it --image=ghcr.io/.../backend:TAG \
     --env-from=secret/backend-env -n livestream-vn -- alembic upgrade head
   ```

## Observability

- `/metrics` exposes Prometheus counters + latency histograms (`http_requests_total`, `http_request_duration_seconds`).
- Structured logs use `structlog`. In production they emit JSON to stdout — ship with your usual stack (Loki, CloudWatch, Datadog).
- Set `SENTRY_DSN` to capture unhandled exceptions.

## Backups

Stream minutes are the only data class that grows fast. TimescaleDB compression after 7 days is configured by adding the policy once after migration:

```sql
SELECT add_compression_policy('stream_minutes', INTERVAL '7 days');
SELECT add_retention_policy('stream_minutes', INTERVAL '18 months');
```

Run nightly `pg_dump --format=custom` to S3 for everything else.
