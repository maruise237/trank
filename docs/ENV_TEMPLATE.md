# trank — Environment Variables

All secrets live in Dokploy (UI → Application → Environment). Never commit `.env`.

## Backend (`trank-backend`)

| Var | Example | Purpose |
|---|---|---|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Postgres + Auth |
| `SUPABASE_ANON_KEY` | `ey...` | Client reads (RLS-enforced) |
| `SUPABASE_SERVICE_ROLE_KEY` | `ey...` | Admin/internal writes (bypass RLS) |
| `SUPABASE_JWT_SECRET` | `<random>` | Verify user JWTs |
| `DATAFORSEO_LOGIN` | `you@trank.tld` | SERP API auth |
| `DATAFORSEO_PASSWORD` | `xxx` | SERP API auth |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker/backend |
| `CELERY_TIMEZONE` | `Europe/Paris` | beat crontab TZ |
| `DIGEST_DELTA_THRESHOLD` | `5` | min abs delta to flag a move |
| `LOG_LEVEL` | `INFO` | uvicorn/celery logs |

## Generating secrets

```bash
openssl rand -hex 32   # for SUPABASE_JWT_SECRET
openssl rand -hex 32   # for ADMIN_JWT_SECRET (Plan 2)
```
