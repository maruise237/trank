# trank — Local Dev

## Prereqs

- Docker Desktop / Compose
- A Supabase project (free tier) with migrations applied

## 1. Apply DB migrations

In Supabase Studio → SQL Editor, run in order:
- `supabase/migrations/0001_init.sql`
- `supabase/migrations/0002_rls.sql`
- `supabase/migrations/0003_constraints.sql`
- `supabase/migrations/0004_views_indexes.sql`

## 2. Configure env

```bash
cp infra/.env.example infra/.env
# fill in Supabase + DataForSEO credentials
```

## 3. Run the stack (local)

```bash
docker compose -f infra/docker-compose.yml up --build
```

- API: http://localhost:8000/health
- Redis: localhost:6379

## 4. Run tests (optional)

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
python -m pytest -v
```

## Deploy to Dokploy

See `docs/ENV_TEMPLATE.md` for all required environment variables.
Add them in Dokploy UI → Application → Environment.
