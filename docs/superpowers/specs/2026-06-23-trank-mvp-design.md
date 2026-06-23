# trank — MVP Solo Design Spec

**Date :** 2026-06-23
**Statut :** Validé (section par section) → en attente de review final
**Auteur :** kamtech + ZCode
**Scope :** MVP Solo uniquement (1 site, 200 mots-clés, 1 utilisateur). Les plans Builder/Agency et les features avancées sont explicitement hors scope (voir Roadmap).

---

## 1. Vision & Positionnement

### 1.1 Problème

Les créateurs de niche sites (affiliés, niche site builders) paient Ahrefs/SEMrush $139+/mois pour n'en utiliser que 5-20%. Ils découvrent leurs chutes de trafic 3 semaines trop tard. Ils veulent une seule chose : **savoir si leurs positions ont monté ou baissé aujourd'hui**.

### 1.2 Proposition de valeur

> **trank** : tes positions Google dans ta boîte mail chaque matin. Rien d'autre.

Daily **alerts** (pas "tracking") — le mot qui convertit le plus selon la research LeadFactory. 200 mots-clés, 1 site, $29/mois.

### 1.3 Persona cible (depuis LeadFactory research)

- **Qui :** Homme 25-42 ans, anglophone (US/UK/Canada/Aus). Side hustle ou full-time.
- **Mindset :** "Builder" pas "blogueur". Pense en systèmes, valide ses niches tôt, construit des clusters thématiques.
- **Douleurs :** (1) trop d'outils, pas le temps ; (2) découvre les chutes trop tard ; (3) paie Ahrefs pour 20% des features.
- **Déclencheur d'achat :** un Google Core Update (perte 30% trafic en 48h) → réalise qu'il n'a pas de système de monitoring.
- **Gap concurrentiel :** personne à $29-59/mo ne combine multi-sites + daily alerts + rapports clients brandés.

### 1.4 Voice & tone (à respecter partout : landing, emails, dashboard)

- **Pas corporate.** Pas "solution innovante". Ton de fondateur qui parle à un pair.
- Phrases courtes. Données concrètes. Pas de jargon SEO gratuit.
- Headline de landing (verbatim de Reddit) : *"I don't need 47 SEO tools. I just need to know if my rankings went up or down today."*
- Le mot magique : **"daily alerts"**, jamais "daily tracking".

---

## 2. Décisions clés (résumé exécutif)

| Décision | Choix | Raison |
|---|---|---|
| Source SERP | DataForSEO API | 0.0006$/requête, cheapest à terme |
| Géolocalisation | 1 location par site | Simple, couvre 80% des cas |
| Alertes | Digest email quotidien | La proposition de valeur centrale |
| Auth | Supabase Auth (magic link + password) | Déjà maîtrisé, RLS native |
| Infra | VPS Hetzner + Docker via Dokploy | Coût-efficace, tu connais |
| Frontend | Next.js 14 App Router + shadcn/ui | UX riche, SSR |
| Détection URL | Domaine → meilleure URL dans le SERP | Standard industrie, simple |
| Architecture backend | Monolithe FastAPI + Celery worker | Simple, suffisant MVP |
| Admin | Protégé frontend ET backend (defense in depth) | Non-négociable sécurité |
| Rapports PDF | Basique dans MVP (@react-pdf/renderer via microservice Node) | Différenciateur vs Wincher |

---

## 3. Architecture globale

```
┌─────────────────────────────────────────────────────────────┐
│                       trank (MVP Solo)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌─────────────────────────────────┐  │
│  │  Next.js 14  │────▶│      FastAPI (REST API)          │  │
│  │  (dashboard) │     │  - Auth via Supabase JWT         │  │
│  │  shadcn/ui   │     │  - CRUD sites/keywords           │  │
│  │  Supabase JS │     │  - Read positions/deltas         │  │
│  └──────────────┘     └────────────┬────────────────────┘  │
│                                    │                         │
│                       ┌────────────┴──────────────┐         │
│                       │       Redis                │        │
│                       └─────────┬─────────────────┘         │
│              ┌──────────────────┴──────────────┐           │
│              ▼                                  ▼           │
│  ┌──────────────────┐             ┌──────────────────┐    │
│  │ Celery beat      │             │  Celery worker    │    │
│  │ (cron 03h00)     │             │  - fetch SERP     │    │
│  └──────────────────┘             │  - compute deltas │    │
│                                   │  - send digest    │    │
│                                   └─────────┬────────┘    │
│                          ┌──────────────────┼────────┐    │
│                          ▼                  ▼        ▼     │
│                   ┌──────────┐    ┌────────────┐ ┌───────┐│
│                   │DataForSEO│    │ Supabase   │ │Resend ││
│                   │  (SERP)  │    │ (Postgres) │ │(email)││
│                   └──────────┘    └────────────┘ └───────┘│
└─────────────────────────────────────────────────────────────┘
       Tout déployé sur 1 VPS Hetzner via Dokploy (docker-compose)
```

### 3.1 Conteneurs (docker-compose géré par Dokploy)

- `trank-api` — FastAPI (uvicorn, port 8000) → `api.trank.tld`
- `trank-worker` — Celery worker
- `trank-beat` — Celery beat (scheduler)
- `trank-redis` — redis:7
- `trank-pdf` — microservice Node (@react-pdf/renderer), interne uniquement (pas public)
- `trank-frontend` — Next.js standalone build → `app.trank.tld`

### 3.2 Monorepo

```
trank/
├── backend/          # FastAPI + Celery
├── frontend/         # Next.js (inclut l'admin)
├── pdf-service/      # microservice Node de rendu PDF
├── supabase/         # migrations + seed
├── infra/            # docker-compose, Dockerfiles, nginx
└── docs/             # ce spec + deployment
```

### 3.3 Flow quotidien

1. **03h00** — Celery beat enfile `track_site(site_id)` pour chaque site actif
2. Le worker interroge DataForSEO (batch), match le domaine, calcule les deltas vs veille, INSERT dans `rank_snapshots`
3. **07h00** — Celery beat enfile `send_digest(user_id)` → compile les top movers → envoie via Resend
4. **Toutes les 15 min** — `health_check` ping DataForSEO/Resend/Redis/DB

---

## 4. Data Model (Supabase Postgres)

### 4.1 Schéma

```sql
-- Extension des users Supabase Auth
profiles (
  id              uuid  PK  = auth.users.id
  email           text
  plan            text  DEFAULT 'solo'       -- 'solo' (MVP) | 'builder','agency' (plus tard)
  trial_ends_at   timestamptz NULL           -- null = pas en essai
  is_active       boolean DEFAULT true       -- false = suspendu par admin
  created_at      timestamptz DEFAULT now()
)

sites (
  id              uuid  PK  default gen_random_uuid()
  user_id         uuid  FK → profiles.id     -- RLS: user_id = auth.uid()
  domain          text                       -- "monsite.com" (normalisé: lowercase, sans www/https)
  name            text                       -- libellé libre
  country_code    char(2)                    -- "FR"
  location_name   text  NULL                 -- "Paris" (optionnel)
  language_code   char(2)                    -- "fr"
  is_active       boolean DEFAULT true       -- false = pause le tracking
  last_tracked_at timestamptz NULL
  created_at      timestamptz DEFAULT now()
)

keywords (
  id              uuid  PK
  site_id         uuid  FK → sites.id  ON DELETE CASCADE
  query           text
  status          text  DEFAULT 'active'    -- 'active' | 'paused'
  created_at      timestamptz DEFAULT now()
)

rank_snapshots (
  id                bigserial PK
  keyword_id        uuid  FK → keywords.id  ON DELETE CASCADE
  checked_at        timestamptz
  position          smallint                  -- 1-100 (null si non trouvé dans top 100)
  url               text     NULL             -- URL du domaine trouvée
  search_volume     integer  NULL             -- volume mensuel (DataForSEO)
  serp_features     text[]   NULL             -- ["featured_snippet","people_also_ask"]
  delta_vs_yesterday smallint NULL            -- -3 = gagné 3 places, +5 = perdu 5
  is_new            boolean  DEFAULT false
  UNIQUE (keyword_id, checked_at)
)

admin_actions (          -- audit trail des actions admin
  id          bigserial PK
  admin_user  text
  action      text       -- 'trigger_run', 'disable_user', ...
  target      text
  metadata    jsonb
  ip          text
  user_agent  text
  created_at  timestamptz DEFAULT now()
)
```

### 4.2 Contraintes MVP (via triggers)

- `count(sites) <= 1` par user sur plan='solo'
- `count(keywords WHERE status='active') <= 200` par user
- Enforce en DB → un user malveillant ne peut pas bypasser l'API.

### 4.3 Index

- `rank_snapshots (keyword_id, checked_at DESC)` — récupérer les N dernières positions
- View `latest_snapshots` : la dernière position par keyword (évite les sous-requêtes)

### 4.4 RLS (Row Level Security)

- `sites`, `keywords`, `rank_snapshots` : user ne voit/écrit QUE ses propres lignes (`user_id = auth.uid()`)
- `admin_actions`, `profiles` : lecture/écriture uniquement via service role (admin)
- Test automatisé : User A ne peut pas lire les sites de User B.

### 4.5 Volumétrie estimée

10 users × 200 KW × 1 snapshot/jour × 365j = **730k lignes/an**. Trivial pour Postgres. Aucune optimisation à anticiper.

---

## 5. Backend FastAPI + Celery

### 5.1 Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app + routers
│   ├── config.py                # pydantic-settings (lit .env)
│   ├── deps.py                  # get_supabase, require_user, require_admin
│   ├── routers/
│   │   ├── auth.py              # /auth/*
│   │   ├── sites.py             # /sites CRUD
│   │   ├── keywords.py          # /sites/{id}/keywords
│   │   ├── snapshots.py         # /sites/{id}/positions, /trends
│   │   ├── reports.py           # /sites/{id}/report.pdf
│   │   └── admin.py             # /admin/* (PROTÉGÉ)
│   ├── services/
│   │   ├── dataforseo.py        # client SERP batch
│   │   ├── positions.py         # match domain, compute delta, build_report_payload
│   │   ├── digest.py            # compile digest
│   │   ├── resend.py            # envoi email
│   │   └── pdf.py               # client HTTP vers trank-pdf
│   └── admin/
│       ├── auth.py              # login admin → admin JWT
│       └── actions.py           # actions admin + audit
├── worker/
│   ├── celery_app.py
│   ├── tasks/
│   │   ├── track_site.py
│   │   ├── send_digest.py
│   │   └── health_check.py
│   └── beat_schedule.py         # crontab 03h00 / 07h00 / 15min
├── tests/
├── Dockerfile
└── requirements.txt
```

### 5.2 Dépendances FastAPI (cœur de la sécurité)

```python
async def require_user(token = Depends(oauth2)) -> dict:
    """Vérifie JWT Supabase user. RLS appliquée côté Supabase."""
    payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
    return {"user_id": payload["sub"], "role": "user"}

async def require_admin(authorization = Depends(oauth2)) -> dict:
    """
    Vérifie un JWT ADMIN (secret DIFFÉRENT du JWT user).
    Indépendant du frontend : un user connecté ne passe pas.
    """
    payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=["HS256"])
    if payload.get("role") != "admin": raise HTTPException(403)
    if payload["exp"] < time.time(): raise HTTPException(401)
    return {"admin_user": payload["sub"], "role": "admin"}
```

### 5.3 API REST — endpoints users (tous `Depends(require_user)`)

| Méthode | Route | Description | Limite |
|---|---|---|---|
| POST | `/auth/sync-profile` | Crée/maj profile après login | — |
| GET | `/sites` | Liste sites du user | max 1 (solo) |
| POST | `/sites` | Crée un site (domain + geo) | refuse si déjà 1 |
| PATCH | `/sites/{id}` | Édite name/geo/is_active | — |
| DELETE | `/sites/{id}` | Supprime (cascade) | — |
| GET | `/sites/{id}/keywords` | Liste paginée KW | — |
| POST | `/sites/{id}/keywords` | Ajoute 1 KW | refuse si > 200 |
| POST | `/sites/{id}/keywords/bulk` | Import CSV | refuse si > 200 |
| DELETE | `/keywords/{id}` | Supprime un KW | — |
| GET | `/sites/{id}/positions` | Dernière position + delta | pagination 50 |
| GET | `/sites/{id}/trends?days=30` | Série temporelle | 7/30/90 |
| GET | `/sites/{id}/overview` | KPIs + top movers | — |
| GET | `/sites/{id}/report.pdf?period=30` | Export PDF | — |
| PATCH | `/me/notification-settings` | Active/désactive digest | — |

### 5.4 API REST — endpoints admin (tous `Depends(require_admin)` sauf login)

| Méthode | Route | Description |
|---|---|---|
| POST | `/admin/login` | Vérifie password hash → admin JWT 15min. **Pas de require_admin.** |
| GET | `/admin/me` | Valide le token admin (utilisé par le layout admin) |
| GET | `/admin/users` | Liste paginée |
| GET | `/admin/users/{id}` | Détail user + sites |
| PATCH | `/admin/users/{id}` | Suspendre/réactiver |
| GET | `/admin/sites` | Tous les sites |
| POST | `/admin/runs/trigger?site_id=` | Lance un run immédiat |
| GET | `/admin/runs` | Historique runs 24h |
| GET | `/admin/health` | Status DataForSEO/Resend/Redis/DB |

Chaque action admin → ligne dans `admin_actions` (IP + user-agent).

### 5.5 Job Celery `track_site` — flow

1. Beat (cron 03h00) → `track_all_sites` dispatcher → `track_site.delay(site_id)` par site actif
2. Worker charge les KW actifs + dernières positions connues
3. Batch DataForSEO `/v3/serp/google/organic/live/advanced` (100 KW/requête → 2 batches pour 200 KW = ~0,24$/site/jour)
4. Pour chaque résultat : parcourir organic results top 100, trouver la 1re URL qui match `site.domain`, extraire position/url/volume/serp_features. Si rien → position=null.
5. Compute `delta_vs_yesterday` = position_today - position_yesterday (null si pas d'historique → is_new=true)
6. INSERT bulk dans `rank_snapshots` (1 transaction, `ON CONFLICT DO NOTHING` pour idempotence)
7. Marquer `site.last_tracked_at = now()`

### 5.6 Gestion des erreurs (job nocturne non supervisé)

| Cas | Action |
|---|---|
| DataForSEO 429 (rate limit) | Retry exponentiel 60s/5min/15min (`autoretry_for`) |
| DataForSEO 5xx | Retry x3 puis run marqué en erreur (visible admin) |
| Timeout/réseau | Retry x2 |
| Quota DataForSEO épuisé | Alert email à kamtech, pas de retry |
| Site sans KW actifs | Skip proprement |
| Échec définitif | Snapshot non créé → digest saute ce jour (pas de fausse donnée) |

**Idempotence** : contrainte `UNIQUE (keyword_id, checked_at)` + `ON CONFLICT DO NOTHING`.

### 5.7 Job `send_digest` (07h00)

Pour chaque user avec `notification_enabled=true` :
1. Charger `latest_snapshots` pour ses KW
2. Calculer : position moyenne, top 5 gains, top 5 pertes, nouveaux KW classés, KW sortis du top 100
3. Render template React Email (.tsx → HTML + texte)
4. Envoyer via Resend

**Définition d'un mouvement "notable"** : `abs(delta_vs_yesterday) >= 5`. En dessous de 5 positions, le keyword est considéré stable. Ce seuil est configurable via env `DIGEST_DELTA_THRESHOLD` (défaut 5).

Sujet type : `☀️ trank — ton site a gagné 3 positions ce matin`. Si aucun mouvement notable (tous les deltas < seuil) → version courte "position stable à X".

### 5.8 Beat schedule

**Fuseau horaire** : `timezone='Europe/Paris'` configuré dans `celery_app.py` (CELERY_TIMEZONE). Les crontabs 03h00/07h00 sont en heure de Paris, été comme hiver.

```python
beat_schedule = {
    "track-all-sites":  crontab(hour=3, minute=0),
    "send-all-digests": crontab(hour=7, minute=0),
    "health-check":     crontab(minute="*/15"),
}
```

> Note : à terme (plan Builder), l'heure du digest deviendra personnalisable par user. Pour le MVP, heure fixe 07h00 Paris pour tous.

---

## 6. Rapports PDF

### 6.1 Niveaux (calés sur les plans)

| Niveau | Plan | Contenu | Statut |
|---|---|---|---|
| Basique | Solo ($29) | Branding trank, période au choix, export manuel | **MVP** |
| Brandé | Builder ($59) | Logo + nom client custom, page de garde, envoi auto hebdo | Roadmap v1.1 |
| White-label | Agency ($149) | Multi-sites par rapport, sans mention trank | Roadmap v1.2 |

### 6.2 Stack

`@react-pdf/renderer` (composants React `<Document>`/`<Page>`/`<View>`/`<Text>`). Rendu côté **backend FastAPI** (pas frontend) via un microservice Node dédié `trank-pdf` (stateless, interne Docker uniquement, jamais public).

Pourquoi pas Puppeteer/ReportLab/WeasyPrint : lourds, fragiles, dépendances système. Voir section discussion.

### 6.3 Endpoint

```python
@router.get("/sites/{site_id}/report.pdf")
async def download_report(site_id, period: int = 30, user = Depends(require_user)):
    site = await sites.get(site_id, user["user_id"])
    if not site: raise HTTPException(404)
    data = await positions.build_report_payload(site_id, period)
    pdf_bytes = await pdf_service.render(template="standard", data=data,
                                         branding={"logo_url": TRANK_LOGO_URL})
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="trank-{site.domain}-{today}.pdf"'})
```

### 6.4 Contenu du PDF

Header brandé → Synthèse KPIs (position moyenne, KW classés, visibilité top 10, évolution période) → Graphique tendance → Top 5 gains / Top 5 pertes → Table détaillée paginée de tous les KW classés → Footer (date + branding trank).

### 6.5 Conteneur docker-compose

```yaml
trank-pdf:
  build: ./pdf-service
  expose: ["3000"]        # interne seulement
  restart: unless-stopped
```

### 6.6 Frontend

Bouton "Export PDF" dans la topbar de la page Trends → `GET /sites/{id}/report.pdf?period=30` → téléchargement navigateur direct (pas de preview en MVP).

---

## 7. Frontend Next.js

### 7.1 Structure

```
frontend/
├── app/
│   ├── (marketing)/         page.tsx, pricing/        # landing publique
│   ├── (auth)/              login/, signup/
│   ├── (app)/               dashboard/, keywords/, trends/, settings/
│   └── (admin)/             admin-{SALT}/dashboard/, users/, sites/, runs/, health/
├── components/
│   ├── ui/                  shadcn/ui
│   ├── charts/              wrapper Recharts
│   ├── keywords/, dashboard/, admin/
├── lib/
│   ├── supabase/            client.ts, server.ts, admin.ts
│   └── api.ts               fetcher typé FastAPI
├── middleware.ts            auth guard + admin guard
└── emails/                  templates React Email (digest)
```

### 7.2 Stack

Next.js 14 App Router + Server Components, shadcn/ui + Tailwind, Supabase JS (auth + reads directs RLS), Recharts, React Email, TanStack Query (mutations keywords).

### 7.3 Design system

- Primaire : bleu profond `#1e3a8a` (confiance, data)
- Accent : vert `#10b981` (gains), rouge `#ef4444` (pertes)
- Police : Inter
- Delta badge : `↑+12` vert / `↓-8` rouge / `—` neutre
- Principe : beaucoup de data, peu de chrome

### 7.4 Pages user

- **Dashboard** : KPIs (position moyenne, KW classés, visibilité top 10, évolution 7j), graphique tendance 30j, top gains/pertes
- **Keywords** : tableau paginé (query/position/delta/volume/sparkline/serp features), filtre classés/non classés/tous, tri, ajout manuel, import CSV (preview + vérif limite 200), pause/supprimer
- **Trends** : sélecteur 7/30/90j, position moyenne du site, nb KW top 10/top 100, comparaison multi-KW, **bouton Export PDF**
- **Settings** : édition site, toggle is_active, préférences digest (activé, heure), danger zone (supprimer)

---

## 8. Admin Panel — Sécurité (Defense in Depth)

### 8.1 Principe

L'admin est protégé côté frontend **ET** backend, de façon indépendante. Même si un attaquant bypass le frontend (appelle directement `api.trank.tld/admin/*`), le backend rejette. Et inversement. Trois portes indépendantes.

### 8.2 Couche 1 — Frontend (middleware.ts)

- Routes admin montées sur `/admin-{ADMIN_PATH_SALT}` (URL masquée, mais ce n'est PAS la sécurité principale)
- `middleware.ts` vérifie Basic Auth : compare `ADMIN_USERNAME` + `bcrypt.compare(pass, ADMIN_PASSWORD_HASH)` lus depuis env serveur
- Sans creds valides → 401 immédiat, la page n'est jamais rendue

### 8.3 Couche 2 — Layout admin (Next.js)

- Exige un admin JWT valide (cookie `trank_admin_jwt`) obtenu via `POST /admin/login`
- À chaque render, `GET /admin/me` valide le token côté backend (token 15min, expired = kick)

### 8.4 Couche 3 — Backend FastAPI

- `Depends(require_admin)` sur **toutes** les routes `/admin/*`
- Vérifie JWT signé par `ADMIN_JWT_SECRET` (≠ `SUPABASE_JWT_SECRET`), claim `role=admin`, non expiré
- Un JWT user valide ne passe pas (claim role différent)
- Utilise `SUPABASE_SERVICE_ROLE_KEY` (bypass RLS) — accès admin uniquement

### 8.5 Règles strictes

- Deux secrets séparés : `SUPABASE_JWT_SECRET` ≠ `ADMIN_JWT_SECRET`
- Aucune route admin déguisée : toutes les actions admin commencent par `/admin/*`
- Statut admin vient de l'env (possession du password), PAS de la DB
- Admin JWT court (15 min), refresh silencieux
- CORS admin séparé : n'accepte que depuis `app.trank.tld`
- Audit trail obligatoire (`admin_actions` : IP + user-agent)
- Aucune cred admin en clair (jamais repo, jamais DB) — uniquement hash bcrypt dans env Dokploy

### 8.6 Variables d'environnement (gérées dans Dokploy)

```env
# Frontend (Next.js)
ADMIN_USERNAME=kamtech
ADMIN_PASSWORD_HASH=$2b$12$...        # bcrypt
ADMIN_PATH_SALT=9f3a2b                # → /admin-9f3a2b
BACKEND_ADMIN_LOGIN_URL=https://api.trank.tld/admin/login

# Backend (FastAPI)
ADMIN_JWT_SECRET=<64-char-random>     # DIFFÉRENT du secret user
ADMIN_USERNAME=kamtech
ADMIN_PASSWORD_HASH=$2b$12$...
SUPABASE_SERVICE_ROLE_KEY=eyJ...      # bypass RLS pour ops admin
CORS_ADMIN_ORIGIN=https://app.trank.tld
```

### 8.7 Pages admin

- **Dashboard** : stats users/sites/runs, quota DataForSEO, derniers runs 24h (avec bouton trigger)
- **Users** : liste (email/plan/trial/usage/active), suspendre/réactiver, détail
- **Sites** : tous les sites tous users
- **Runs** : historique 7j Celery, trigger run manuel
- **Health** : status temps réel DataForSEO/Resend/Redis/Supabase

---

## 9. Validation & Go-to-Market

### 9.1 Phase de validation (avant de coder — mais post-spec)

```
Jour 0 : 3 supports préparés (post Reddit long, tweet thread, msg Facebook groups)
Jour 1-2 : poster + répondre en temps réel
  - Succès : 10 personnes "I want in" en 48h → on code
  - Échec : 0 réponse en 72h → on pivote avant d'investir 2 semaines
Jour 3 : si ≥10 réponses → build MVP
```

Message de validation (tone research) :
> *"I got tired of paying Ahrefs $139/mo to use 5% of it. So I'm building trank — daily rank alerts in your inbox, nothing else. 200 keywords, 1 site, $29/mo when it launches. First 10 people get 1 month free. Who's in?"*

Canaux : r/juststart, r/SEO, r/blogging ; Facebook groups (Niche Pursuits, Authority Hacker) ; Twitter/X (répondre aux threads qui se plaignent d'Ahrefs/SEMrush).

### 9.2 Inputs marketing (depuis LeadFactory)

Référencer dans `docs/` les 7 fichiers produits : creative-brief, strategy, master-research.csv, 02-competitor-research, 03-psychographic, etc. Serviront pour la landing page et les messages Reddit.

---

## 10. Tests

| Type | Couverture | Outil |
|---|---|---|
| Unit backend | `services/positions.py` (match domain, compute delta), `services/digest.py` | pytest |
| Integration | `track_site` end-to-end avec mock DataForSEO (cassettes VCR) | pytest + vcrpy |
| API contract | Tous endpoints users + admin | pytest + fastapi.testclient |
| Sécurité admin | `require_admin` rejette JWT user, JWT expiré, sans token | pytest `tests/test_admin_security.py` |
| RLS | User A ne lit pas les sites de User B (via Supabase direct) | script SQL |
| E2E frontend | Login → add site → import CSV → voir positions → export PDF | Playwright |

Non-négociable : tests sécurité admin + tests RLS.

---

## 11. Sécurité — checklist finale

- [ ] Aucune cred admin en clair dans le code ou la DB
- [ ] `ADMIN_JWT_SECRET` ≠ `SUPABASE_JWT_SECRET`
- [ ] `require_admin` sur toutes les routes `/admin/*` (vérifié par test)
- [ ] RLS active sur `sites`, `keywords`, `rank_snapshots`
- [ ] Service role key jamais exposée au frontend
- [ ] HTTPS partout (Traefik/Let's Encrypt via Dokploy)
- [ ] Rate limit sur `/auth/*` et `/admin/login`
- [ ] Backups Supabase quotidiens
- [ ] Secrets tournés si un admin quitte

---

## 12. Livrables

```
trank/
├── backend/                      # FastAPI + Celery + services
├── frontend/                     # Next.js (inclut admin)
├── pdf-service/                  # microservice Node @react-pdf/renderer
├── infra/
│   ├── docker-compose.yml        # utilisé par Dokploy
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.pdf
│   └── nginx
├── supabase/
│   ├── migrations/               # schema + RLS + triggers
│   └── seed.sql
├── docs/
│   ├── README.md                 # setup dev 5 min
│   ├── DEPLOYMENT.md             # Dokploy pas à pas
│   ├── ENV_TEMPLATE.md           # toutes les variables + génération
│   └── superpowers/specs/2026-06-23-trank-mvp-design.md  (ce fichier)
└── .env.example
```

---

## 13. Coûts (10 users MVP)

| Item | Coût/mois |
|---|---|
| Hetzner VPS CX22 (4GB) | ~4,5 € |
| Supabase Free tier | 0 € |
| DataForSEO (10 × 200 KW × 30j × 0,0006$) | ~36 $ |
| Resend (3k emails/mo, free tier) | 0 $ |
| Domaine trank.tld | ~1 $ |
| **Total** | **~42 $/mois** |

Break-even à 2 users payants à $29.

---

## 14. Roadmap post-MVP (explicitement hors scope)

| Phase | Features |
|---|---|
| v1.1 | Plan Builder ($59) : multi-sites, 1000 KW, rapports hebdo, branding client custom, table `generated_reports` |
| v1.2 | Plan Agency ($149) : sites illimités, API publique, white-label total |
| v1.3 | **Détection Core Update** (chute massive simultanée → alerte urgence) — le déclencheur d'achat n°1 de la research |
| v2.0 | Détection cannibalization, app mobile |

---

## 15. Ce qui n'est PAS dans le MVP (YAGNI)

- Billing Stripe complexe (free 1 mois pour les 10 testeurs, paiement manuel ensuite)
- Multi-sites par user
- Rapports PDF brandés (seulement basique trank)
- API publique
- Détection cannibalization / Core Update
- App mobile
- Preview PDF dans le navigateur
