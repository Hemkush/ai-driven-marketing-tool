# Developer Handoff — AI-Driven Marketing Tool (MarketPilot)

> Last updated: April 2026  
> Stack: React + Vite · FastAPI · PostgreSQL (Supabase) · OpenAI · Google Places API · Resend · Cloud Run · Firebase Hosting

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Backend Deep Dive](#5-backend-deep-dive)
6. [Frontend Deep Dive](#6-frontend-deep-dive)
7. [Database Schema](#7-database-schema)
8. [Authentication System](#8-authentication-system)
9. [Email Verification Flow](#9-email-verification-flow)
10. [AI Integration](#10-ai-integration)
11. [Deployment](#11-deployment)
12. [Environment Variables](#12-environment-variables)
13. [Special Cases & Gotchas](#13-special-cases--gotchas)
14. [Observability, Evaluation & Optimization](#14-observability-evaluation--optimization)
15. [Interview Q&A](#15-interview-qa)

---

## 1. Product Overview

MarketPilot is an AI-powered marketing tool for small businesses. It lets users:

- **Onboard** via a conversational AI questionnaire that learns their business
- **Generate** marketing campaign briefs, channel assets, personas, and roadmaps
- **Research** competitors using Google Places API + AI enrichment (SWOT, pricing, hours gaps)
- **Create content** — social posts, email newsletters, ad copy, blog intros, logo concepts, posters, and more — with tone and audience controls
- **Benchmark** against local competitors with a price-quality map, SWOT analysis, and opportunity gap analysis

Each user can have multiple **Projects** (business profiles) and all generated content is stored per-project.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
│              React SPA (Firebase Hosting)                   │
│         https://ai-marketing-prod.web.app                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS (REST + JSON)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (Cloud Run)                       │
│              FastAPI · Python 3.12 · uvicorn                │
│         https://backend-[hash]-uc.a.run.app                 │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │  routes  │  │  mvp/    │  │  services/               │  │
│  │ (auth,   │  │ (quest-  │  │ generator, content_studio│  │
│  │  projects│  │  ionnaire│  │ competitive_benchmarker  │  │
│  │  generate│  │  analysis│  │ persona_builder, etc.    │  │
│  │  )       │  │  content │  │                          │  │
│  └──────────┘  └──────────┘  └──────────────────────────┘  │
└──────┬────────────────────────────┬────────────────────────┘
       │                            │
       ▼                            ▼
┌─────────────┐            ┌─────────────────┐
│  Supabase   │            │   OpenAI API    │
│  PostgreSQL │            │  gpt-4o-mini    │
│  + pgvector │            │  text-embedding │
└─────────────┘            └─────────────────┘
                                    │
                           ┌─────────────────┐
                           │ Google Places   │
                           │     API         │
                           └─────────────────┘
```

**Data flow:** Browser → Cloud Run (FastAPI) → Supabase (persistence) + OpenAI (generation) + Google Places (competitor data)

---

## 3. Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Language |
| FastAPI | Latest | Web framework |
| uvicorn | Latest | ASGI server (1 worker on Cloud Run) |
| SQLAlchemy | 2.x | ORM with mapped columns |
| Alembic | Latest | Database migrations |
| psycopg (v3) | Latest | PostgreSQL driver (`psycopg`, not `psycopg2`) |
| pgvector | Latest | Vector embeddings for memory store |
| OpenAI SDK | Latest | LLM + embeddings |
| slowapi | Latest | Rate limiting (10 req/min on generate endpoints) |
| prometheus-fastapi-instrumentator | Latest | `/metrics` endpoint for monitoring |
| sentry-sdk[fastapi] | 2.29.1 | Error tracking + alerting |
| numpy | ≥1.26.0 | Cosine similarity for embedding ranking |
| Resend API | REST | Transactional email (verification emails) |
| python-dotenv | Latest | `.env` loading |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | Latest | Build tool + dev server |
| Custom hook | — | State management via `useMvpWorkflow.js` |
| React Router | Latest | Client-side routing |
| Tailwind CSS | Latest | Styling |
| Lucide React | Latest | Icon library |
| Axios | Latest | HTTP client with interceptors |

### Infrastructure
| Service | Purpose |
|---|---|
| Google Cloud Run | Backend hosting (serverless containers, scales to zero) |
| Firebase Hosting | Frontend static file hosting (CDN) |
| Supabase | Managed PostgreSQL + pgvector extension |
| Google Container Registry (GCR) | Docker image storage |
| Google Cloud Build | CI build for Docker images |
| Resend | Email delivery (verification emails) |
| Google Places API | Competitor discovery and data |

---

## 4. Project Structure

```
ai-driven-marketing-tool/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── routes.py          # Auth, projects, campaign generation
│   │   │   │   └── mvp/               # MVP workflow endpoints
│   │   │   │       ├── questionnaire.py
│   │   │   │       ├── analysis.py
│   │   │   │       ├── positioning.py
│   │   │   │       ├── research.py
│   │   │   │       ├── personas.py
│   │   │   │       ├── strategy.py
│   │   │   │       ├── content.py
│   │   │   │       ├── system.py
│   │   │   │       └── deps.py        # Shared dependencies
│   │   │   ├── core/
│   │   │   │   ├── auth.py            # JWT (custom HMAC-SHA256), password hashing
│   │   │   │   ├── config.py          # Settings from env vars
│   │   │   │   ├── rate_limit.py      # slowapi limiter
│   │   │   │   ├── security.py        # Internal API key check
│   │   │   │   ├── logging_config.py  # JSON formatter for Cloud Run
│   │   │   │   ├── llm_tracker.py     # Token/cost/latency tracking wrapper
│   │   │   │   ├── quality_scorer.py  # LLM output quality scoring
│   │   │   │   ├── response_cache.py  # DB-backed response caching
│   │   │   │   ├── metrics.py         # Custom Prometheus metrics
│   │   │   │   ├── pipeline_tracer.py # Agent invocation tracing
│   │   │   │   └── token_budget.py    # Prompt token budget enforcement
│   │   │   ├── services/
│   │   │   │   ├── generator.py            # Campaign brief + channel assets
│   │   │   │   ├── content_studio.py       # Content generation (all asset types)
│   │   │   │   ├── competitive_benchmarker.py  # Google Places + AI enrichment
│   │   │   │   ├── onboarding_interviewer.py   # Conversational questionnaire
│   │   │   │   ├── persona_builder.py          # AI persona generation
│   │   │   │   ├── market_researcher.py        # Market research reports
│   │   │   │   ├── segment_analyst.py          # Audience segment analysis
│   │   │   │   ├── positioning_copilot.py      # Positioning statement generation
│   │   │   │   ├── channel_strategy_planner.py # Channel strategy
│   │   │   │   ├── roadmap_planner.py          # Marketing roadmap
│   │   │   │   ├── memory_store.py             # pgvector semantic memory
│   │   │   │   ├── email_sender.py             # Resend + SMTP fallback
│   │   │   │   └── storage.py                  # Generation persistence
│   │   │   ├── db.py                  # SQLAlchemy engine + session
│   │   │   ├── models.py              # All ORM models
│   │   │   └── main.py                # App factory, middleware, CORS
│   │   ├── alembic/
│   │   │   ├── env.py                 # Migration runner (reads DATABASE_URL)
│   │   │   └── versions/              # Migration scripts
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env                       # Local dev only (never in prod)
│   └── frontend/
│       ├── src/
│       │   ├── pages/                 # Route-level components
│       │   ├── components/            # Reusable UI components
│       │   ├── state/
│       │   │   └── useMvpWorkflow.js  # Central state store
│       │   ├── lib/
│       │   │   ├── api.js             # Axios instance + interceptors
│       │   │   └── mvpClient.js       # API client functions
│       │   ├── App.jsx                # Router + auth guard
│       │   └── index.css              # Global styles + Tailwind
│       ├── .env                       # Dev env (VITE_API_BASE_URL)
│       ├── .env.production            # Prod env
│       └── nginx.conf                 # Nginx config (used in Docker)
├── firebase.json                      # Firebase Hosting config
├── .firebaserc                        # Firebase project alias
├── DEPLOYMENT.md                      # Step-by-step deploy guide
└── Developer_Handoff.md               # This file
```

---

## 5. Backend Deep Dive

### FastAPI App (`main.py`)
- CORS configured via `CORS_ORIGINS` env var (comma-separated list)
- Falls back to `FRONTEND_URL` + localhost for local dev
- Prometheus metrics exposed at `/metrics`
- Rate limiter attached to app state (slowapi)
- Custom request logging middleware (method + path + status + duration ms)
- Health check at `/health` → `{"status": "ok"}`
- Global exception handler returns `{"detail": "Internal server error"}` for unhandled exceptions (no stack traces leaked to clients)

### Router Structure

**`/api` prefix — `routes.py`:**
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | None | Creates PendingRegistration, sends verification email |
| POST | `/api/auth/login` | None | Validates credentials, returns JWT |
| GET | `/api/auth/verify-email` | None | Promotes pending → real User |
| POST | `/api/auth/resend-verification` | None | Resends verification email |
| GET | `/api/auth/me` | JWT | Returns current user info |
| POST | `/api/projects` | JWT | Creates a project |
| GET | `/api/projects` | JWT | Lists user's projects |
| GET | `/api/projects/{id}` | JWT | Gets single project |
| PATCH | `/api/projects/{id}` | JWT | Updates project |
| DELETE | `/api/projects/{id}` | JWT | Deletes project + nullifies generations |
| POST | `/api/generate` | JWT | Campaign brief (rate limited 10/min) |
| POST | `/api/generate-assets` | JWT | Channel assets (rate limited 10/min) |
| GET | `/api/generations` | Internal API Key | Admin: list all generations |

> Note: All `/api/projects/*` endpoints are also aliased as `/api/business-profiles/*`

**`/api/mvp` prefix — `mvp/` folder:**
- Questionnaire, analysis, positioning, research, personas, channel strategy, content generation

### Rate Limiting
- `slowapi` wraps `/generate` and `/generate-assets`
- Limit: **10 requests/minute per IP**
- Returns HTTP 429 with `Retry-After` header on breach

### Custom JWT (`core/auth.py`)
- **No external JWT library** (no PyJWT) — implemented using stdlib `hmac` + `hashlib` + `base64`
- Token format: `base64url(json_payload).hmac_sha256_hex_signature`
- Payload: `{ "sub": "<user_id>", "iat": <timestamp>, "exp": <timestamp> }`
- Token expiry: **24 hours**
- Secret: `JWT_SECRET_KEY` env var (required in production; falls back to insecure dev value if `APP_ENV != prod`)

### Password Hashing (`core/auth.py`)
- Algorithm: **PBKDF2-SHA256** with 310,000 iterations
- Salt: 16-byte random hex per user (via `secrets.token_hex(16)`)
- Stored format: `pbkdf2_sha256$310000$<salt>$<hex_digest>`
- Comparison: `hmac.compare_digest` for constant-time, timing-attack-safe verification

---

## 6. Frontend Deep Dive

### State Management (`state/useMvpWorkflow.js`)
All application state lives in a single custom React hook. Key state:

| State Key | Description |
|---|---|
| `user` | Authenticated user object |
| `token` | JWT stored in `localStorage` |
| `sessionId` | Current workflow session ID |
| `projects` | List of user's business profiles |
| `currentProject` | Selected project |
| `pendingVerificationEmail` | Set when signup awaiting email verification |
| `contentAssets` | Generated content items |
| `competitors` / `benchmarkData` | Competitive analysis results |
| `roadmap`, `personas`, `channelStrategy` | Generated marketing artifacts |

**Key actions:**
- `resetForNewSession()` — clears all session/artifact state before starting a new workflow
- `register()` / `login()` / `logout()`
- `resendVerification()` — resends verification email to `pendingVerificationEmail`

### API Client (`lib/api.js`)
- Axios instance with `baseURL` from `VITE_API_BASE_URL` env var
- Request interceptor: attaches `Authorization: Bearer <token>` from localStorage
- Response interceptor: redirects to `/login` on 401

### Routing (`App.jsx`)
- Public paths: `/login`, `/register`, `/verify-email`
- All other paths require authentication (redirect to `/login` if no token)

### Email Verification Page (`pages/VerifyEmailPage.jsx`)
- Reads `token` query param from URL on mount
- Calls `authClient.verifyEmail(token)`
- Shows verifying / success / error states with appropriate UI

### Auth Panel (`components/AuthPanel.jsx`)
- Client-side email validation with regex before making API calls
- Shows `PendingVerificationScreen` when `pendingVerificationEmail` is set
- Handles `EMAIL_NOT_VERIFIED` (403) from login — shows inline message with resend link
- Enter key submits forms

---

## 7. Database Schema

### Tables

#### `users`
| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| email | varchar(255) | unique, indexed |
| password_hash | varchar(255) | PBKDF2-SHA256 format |
| full_name | varchar(255) | nullable |
| created_at | timestamptz | server default `now()` |

#### `pending_registrations`
| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| email | varchar(255) | unique, indexed |
| password_hash | varchar(255) | hashed at signup time |
| full_name | varchar(255) | nullable |
| token | varchar(128) | unique, indexed — sent in verification email |
| expires_at | timestamptz | 24h from registration |
| created_at | timestamptz | server default |

> Row is **deleted** when user verifies email (promotes to `users`) or when token expires and user re-registers.

#### `projects`
| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| name | varchar(200) | |
| description | text | nullable |
| business_address | varchar(500) | nullable — used for Google Places competitor search |
| owner_id | integer FK | → users.id |
| created_at | timestamptz | |

#### `generations`
Stores all campaign brief / asset generation inputs and outputs as JSON text blobs.

#### `questionnaire_sessions` / `questionnaire_responses`
Tracks the conversational onboarding interview per project. Sessions have a `status` (`in_progress`, `complete`). Responses store question + answer + sequence number.

#### `memory_chunks`
Stores semantic memory from questionnaire responses. Uses pgvector `Vector(1536)` column for embeddings from `text-embedding-3-small`. Content hash prevents duplicates.

#### Other tables
`analysis_reports`, `positioning_statements`, `research_reports`, `persona_profiles`, `channel_strategies`, `roadmap_plans`, `media_assets` — all linked to `project_id`.

### Migrations
Managed with **Alembic**. Migration files in `apps/backend/alembic/versions/`.

**Run migrations (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require"; alembic upgrade head
```

**Key note in `alembic/env.py`:** The `DATABASE_URL` is escaped before being passed to configparser:
```python
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
```
This prevents a crash when the URL contains `%` from URL-encoded characters in passwords.

---

## 8. Authentication System

### Flow

```
REGISTER
  └─► POST /api/auth/register
        └─► Create PendingRegistration (hashed password + random token)
        └─► Send verification email → {FRONTEND_URL}/verify-email?token=...
        └─► Return { email, email_sent }

EMAIL VERIFICATION
  └─► GET /api/auth/verify-email?token=...
        └─► Find PendingRegistration by token
        └─► Check not expired
        └─► Create real User record
        └─► Delete PendingRegistration
        └─► Return { message: "Email verified successfully" }

LOGIN
  └─► POST /api/auth/login
        └─► Find User by email → verify PBKDF2 password hash
        └─► If not in users but in pending_registrations → return 403 EMAIL_NOT_VERIFIED
        └─► Return { access_token, token_type: "bearer" }
```

### Design Decision: Why `PendingRegistration` Table?
Instead of an `is_verified` flag on `User`, unverified registrations live in a separate table:
- `users` table only ever contains verified, active accounts
- No accidental querying of unverified users in business logic
- Expired rows can be pruned without touching real users
- Clean upsert on retry — re-registration updates the token instead of creating a duplicate row

---

## 9. Email Verification Flow

### Provider Priority in `services/email_sender.py`
1. **Resend API** (if `RESEND_API_KEY` set) — production provider
2. **SMTP** (if `SMTP_HOST` + `SMTP_USER` + `SMTP_PASSWORD` set) — fallback
3. **Log to terminal** (if neither configured) — local dev convenience

### Resend Configuration
- API endpoint: `https://api.resend.com/emails`
- From address: `onboarding@resend.dev` (Resend's shared test domain, no domain verification needed)
- For production with custom domain: update `FROM_EMAIL=noreply@yourdomain.com` and verify domain in Resend dashboard

### Verification Email Link
```
{FRONTEND_URL}/verify-email?token={64-char-urlsafe-token}
```

Local dev: `http://localhost:5173/verify-email?token=...`  
Production: `https://ai-marketing-prod.web.app/verify-email?token=...`

### Token Details
- Generated with: `secrets.token_urlsafe(48)` → 64 characters
- Stored in `pending_registrations.token` (unique, indexed)
- Expires: 24 hours from registration
- Resend endpoint refreshes the token and extends expiry

---

## 10. AI Integration

### OpenAI Usage

| Feature | Model | Output |
|---|---|---|
| Campaign brief generation | gpt-4o-mini | JSON (json_object mode) |
| Channel asset generation | gpt-4o-mini | JSON |
| Competitive benchmarking enrichment | gpt-4o-mini | JSON |
| Content Studio (all asset types) | gpt-4o-mini | JSON |
| Onboarding questionnaire | gpt-4o-mini | JSON |
| Semantic memory embeddings | text-embedding-3-small | 1536-dim vector |

### Token-Saving Strategy — Embedding-Based Competitor Ranking

The competitive benchmarking pipeline fetches up to 20 competitors from Google Places. Naively sending all of them to `gpt-4o-mini` with full details creates a huge prompt (~8k+ tokens) that causes timeouts and high cost.

**Solution: RAG-style pre-filtering with embeddings before the LLM call**

```
Before:  20 raw places → fetch Place Details for 10 → 10 competitors in LLM prompt (~8k tokens, ~100s)
After:   20 raw places → embed + rank → top 5 → fetch Place Details for 5 → 5 in LLM prompt (~2k tokens, ~15s)
```

**How it works (`_rank_by_relevance` in `competitive_benchmarker.py`):**

1. **Embed each candidate cheaply** — convert basic place data (name + types + vicinity) into a short text string, then embed all 20 using `text-embedding-3-small`. This costs ~$0.00003 per benchmarking run — essentially free.
2. **Embed the business context** — combine the business keyword + address + first 400 chars of interview context into one query vector.
3. **Cosine similarity ranking** — score each competitor against the business context vector. The top 5 most semantically relevant competitors win.
4. **Only then fetch Place Details** — API calls with full reviews/hours/etc. go to just those 5 competitors (saves Google Places quota too).
5. **Send 5 enriched competitors to LLM** — prompt is 4x smaller, response is 4x faster, no more timeouts.

**Why cosine similarity works here:** A "hair salon" business context vector will score high similarity against other hair salons and low against restaurants or plumbers — even though all of them might be geographically nearby. The embedding naturally filters for business-type relevance before the expensive LLM call.

**Cost comparison per benchmarking run:**

| Step | Before | After |
|---|---|---|
| Google Places Detail API calls | 10 | 5 |
| LLM tokens (approx) | ~8,000 | ~2,000 |
| Embedding tokens | 0 | ~500 |
| Total OpenAI cost | ~$0.0012 | ~$0.0004 |
| Response time | ~100s (timeout) | ~15s |

---

### Why `chat.completions.create` with `json_object` Mode?
Earlier versions used `client.responses.create` (OpenAI Responses API). This returned unstructured text that was inconsistently parsed — competitive benchmarking sections (SWOT, hours gap, opportunity gaps) silently returned empty because the text parser failed to extract structured data.

**Fix:** Switched to `client.chat.completions.create` with `response_format={"type": "json_object"}`. This guarantees valid JSON output every time. The model is instructed in the prompt to return a JSON object with specific keys.

```python
resp = client.chat.completions.create(
    model=settings.openai_model,
    response_format={"type": "json_object"},
    messages=[{"role": "user", "content": prompt}],
)
raw = resp.choices[0].message.content or ""
result = json.loads(raw)
```

### Google Places API (Competitive Benchmarking)
1. Geocode the business address to lat/lng
2. Search nearby businesses by type within `BENCHMARKING_RADIUS_METERS` (default 5000m)
3. Fetch place details: hours, rating, price level, total ratings, reviews
4. Pass competitor data as context to OpenAI prompt
5. AI returns: SWOT analysis, pricing comparison, hours gap analysis, opportunity gaps

---

## 11. Deployment

### Live Infrastructure

| Component | Service | Notes |
|---|---|---|
| Frontend | Firebase Hosting `ai-marketing-prod` | `https://ai-marketing-prod.web.app` |
| Backend | Google Cloud Run `backend` | Region: `us-central1` |
| Database | Supabase `swrixeaymsplobheqnaw` | Region: `us-west-2` (Oregon) |

### Backend Deployment (Cloud Run)

```bash
# 1. Build Docker image
cd apps/backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/backend

# 2. Deploy / update
gcloud run deploy backend --image gcr.io/YOUR_PROJECT_ID/backend --region us-central1

# 3. Update a single env var
gcloud run services update backend --region us-central1 --update-env-vars KEY=value
```

**Dockerfile notes:**
- Base: `python:3.12-slim`
- Port: **8080** (Cloud Run requirement — not the FastAPI default of 8000)
- Workers: 1 (Cloud Run scales by instances, not workers)
- `--timeout-keep-alive 75` matches Cloud Run's ~80s idle timeout
- `RUN rm -f .env` — removes any local `.env` from the image; secrets come from Cloud Run env vars

### Frontend Deployment (Firebase Hosting)

```bash
# 1. Set backend URL
# Edit apps/frontend/.env.production:
# VITE_API_BASE_URL=https://backend-[hash]-uc.a.run.app/api

# 2. Build
cd apps/frontend
npm run build  # outputs to apps/frontend/dist/

# 3. Deploy
cd ../..
firebase deploy --only hosting
```

**`firebase.json` key settings:**
- `"site": "ai-marketing-prod"` — required for named sites (without this: `Assertion failed: resolving hosting target`)
- SPA rewrite: all routes → `/index.html`
- JS/CSS: `Cache-Control: max-age=31536000, immutable` (safe because Vite adds content hashes to filenames)
- `index.html`: `Cache-Control: no-cache` (always fetches fresh entry point)

### Database Migrations (Supabase)

```powershell
# PowerShell — run from apps/backend/
$env:DATABASE_URL="postgresql+psycopg://postgres.[ref]:[password]@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"; alembic upgrade head
```

**Before first migration, enable pgvector in Supabase SQL Editor:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 12. Environment Variables

### Backend

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Supabase pooler connection string |
| `JWT_SECRET_KEY` | Prod only | `dev-insecure-secret` | JWT signing secret — generate with `secrets.token_hex(32)` |
| `INTERNAL_API_KEY` | Prod only | — | Protects `/api/generations` admin endpoint |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `OPENAI_BASE_URL` | No | `https://us.api.openai.com/v1` | OpenAI endpoint |
| `OPENAI_TIMEOUT_SECONDS` | No | `45` | Request timeout |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Embedding model |
| `GOOGLE_PLACES_API_KEY` | Yes | — | For competitive benchmarking |
| `BENCHMARKING_RADIUS_METERS` | No | `5000` | Competitor search radius |
| `RESEND_API_KEY` | Yes (prod) | — | Resend email API key |
| `FROM_EMAIL` | No | `onboarding@resend.dev` | Sender address |
| `APP_NAME` | No | `MarketPilot` | Used in email templates |
| `CORS_ORIGINS` | Prod only | localhost fallback | Comma-separated allowed origins |
| `FRONTEND_URL` | No | `http://localhost:5173` | Used in verification email links |
| `APP_ENV` | No | `dev` | `dev` or `production` |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN (no-op if unset) |
| `SENTRY_ENVIRONMENT` | No | `production` | Sentry environment tag |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Frontend

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend Cloud Run URL + `/api` suffix |

---

## 13. Special Cases & Gotchas

### 1. `%` in DATABASE_URL Breaks Alembic

Alembic uses Python's `configparser` internally. configparser treats `%` as the start of an interpolation sequence. A URL-encoded password like `Maryland%40123` (where `%40` = `@`) causes:
```
ValueError: invalid interpolation syntax at position 59
```

**Fix in `alembic/env.py`:**
```python
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
```
configparser sees `%%` → unescapes to `%` → SQLAlchemy gets the correct URL.

**Simpler long-term fix:** Use passwords without special characters (letters and numbers only) to avoid URL encoding entirely.

---

### 2. Cloud Run Port Must Be 8080

Cloud Run health probes port **8080**. FastAPI/uvicorn defaults to 8000. Container fails startup if port doesn't match.

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### 3. Firebase Hosting `site` Field Required

For projects with multiple named hosting sites, `firebase.json` must declare `"site"`:
```json
{ "hosting": { "site": "ai-marketing-prod", ... } }
```
Without it: `Error: Assertion failed: resolving hosting target`

---

### 4. New Session Showing Previous Session Data

When navigating to the Marketing Discovery page, the old `sessionId` (persisted from the previous session) was still in state, causing stale live analysis and chat data to appear.

**Fix:** Call `actions.resetForNewSession()` before navigating. This explicitly clears `sessionId`, `liveAnalysis`, `chatMessages`, and all artifact state while preserving auth and project selection.

---

### 5. Competitive Benchmarking Missing SWOT/Hours/Opportunity Sections

The AI enrichment was using `client.responses.create` (OpenAI Responses API) which returned unstructured plain text. The text parser silently dropped sections it couldn't match.

**Fix:** Switched to `client.chat.completions.create` with `response_format={"type": "json_object"}`. This forces the model to return structured JSON with all required keys. Logging was added for the raw response and returned keys to aid debugging.

---

### 6. Supabase Direct Connection DNS Failure

`db.PROJECT_REF.supabase.co:5432` (direct connection host) may fail DNS resolution when accessed from outside Supabase's infrastructure.

**Fix:** Use the **connection pooler** URL instead:
```
aws-0-REGION.pooler.supabase.com:5432
```
Username for pooler format: `postgres.PROJECT_REF` (not just `postgres`).

---

### 7. Resend 403 on Unverified Sender Domain

Using a custom `FROM_EMAIL` domain that isn't verified in Resend returns `403 Forbidden`.

**Fix:** Use `onboarding@resend.dev` (Resend's shared test domain — no verification needed) until your own domain is verified in the Resend dashboard.

---

### 8. PowerShell Doesn't Support `\` Line Continuation

`\` for multi-line commands is bash syntax. In PowerShell, all gcloud commands must be written on one line:

```powershell
# Wrong (bash)
gcloud run deploy backend \
  --image gcr.io/project/backend \
  --region us-central1

# Correct (PowerShell)
gcloud run deploy backend --image gcr.io/project/backend --region us-central1
```

---

### 9. Custom JWT Is Not Standard JWT

The project implements JWT manually using Python stdlib (`hmac`, `hashlib`, `base64`). The token format is `base64url(json_payload).hmac_sha256_hex_signature` — it has no header segment. This means:
- Standard JWT libraries (PyJWT, jsonwebtoken) **cannot verify these tokens**
- The tokens work correctly within this self-contained system
- If you add a third-party service that needs to verify tokens, you'll need to switch to standard JWT

---

### 10. `psycopg` v3 vs `psycopg2`

The project uses **psycopg v3** (package name: `psycopg`), not the older `psycopg2`. SQLAlchemy connection strings use:
```
postgresql+psycopg://...   ← psycopg v3
postgresql+psycopg2://...  ← psycopg v2 (NOT used here)
```
These are different packages. Installing `psycopg2` instead of `psycopg` will cause connection errors.

---

### 11. Competitive Benchmarking OpenAI Timeout

The benchmarking AI call timed out (101 seconds) because Google Places returns up to 20 competitors and sending all of them with full reviews to `gpt-4o-mini` created an 8k+ token prompt.

**Fix — two-part:**
1. Added embedding-based pre-filtering (`_rank_by_relevance`) to select only the 5 most relevant competitors before the LLM call (see Section 10 for full strategy)
2. Set a dedicated 120s timeout on the enrichment call instead of the global 45s default — because this is inherently a larger prompt than other calls

The root cause pattern: **never let unbounded external data (Google Places results) flow directly into an LLM prompt**. Always filter/rank first.

---

### 12. Supabase Pooler Username Format

When using Supabase's connection pooler, the username must include the project reference:
```
postgresql+psycopg://postgres.swrixeaymsplobheqnaw:PASSWORD@aws-0-us-west-2.pooler.supabase.com:5432/postgres
```
Using just `postgres` as the username with the pooler URL → `password authentication failed for user "postgres"`.

---

### 13. pgvector Type Registration Required for psycopg v3

Without calling `register_vector(connection)` on every new psycopg v3 connection, Python `list[float]` values cannot be serialized to PostgreSQL `vector` type. The insert silently succeeds but stores NULL. Fixed by adding a SQLAlchemy `connect` event listener in `db.py`:

```python
@event.listens_for(engine, "connect")
def _register_vector(dbapi_conn, _):
    register_vector(dbapi_conn)
```

This is a psycopg v3-specific requirement — psycopg2 handled type registration differently.

---

### 14. OpenAI Regional API Keys

API keys provisioned on the US region only work with `us.api.openai.com/v1`, not `api.openai.com/v1`. Using the global endpoint returns HTTP 401 with `incorrect_hostname` error. Set `OPENAI_BASE_URL=https://us.api.openai.com/v1` in Cloud Run environment variables.

---

## 14. Observability, Evaluation & Optimization

### Overview

The platform has a full observability stack built on top of the core application:

| Layer | Tool | What it captures |
|---|---|---|
| Structured Logging | Python `logging` + JSON formatter | Every request, LLM call, cache op, quality score |
| Error Tracking | Sentry (sentry-sdk[fastapi]) | All unhandled exceptions + ERROR logs |
| LLM Tracking | `core/llm_tracker.py` | Tokens, cost, latency per agent per call |
| Quality Scoring | `core/quality_scorer.py` | Schema completeness score (0–1) per output |
| Prometheus Metrics | `core/metrics.py` | 7 custom AI metrics at `/metrics` |
| Pipeline Tracing | `core/pipeline_tracer.py` | Per-agent DB trace with duration + status |
| Response Caching | `core/response_cache.py` | DB-backed LLM result cache |
| Token Budgets | `core/token_budget.py` | Per-agent prompt size limits |
| Retrieval Eval | `memory_store.py` | Cosine similarity scores on retrieved chunks |

---

### Structured JSON Logging (`core/logging_config.py`)

All logs are emitted as single-line JSON to stdout, which Cloud Run ingests into Google Cloud Logging automatically. Every log line includes `severity`, `message`, `logger`, and `time` fields. Extra fields passed via `extra={}` are indexed as `jsonPayload` fields — searchable in Cloud Log Explorer.

```python
logger.info("llm_call", extra={
    "agent": "competitive_benchmarker",
    "model": "gpt-4o-mini",
    "total_tokens": 1152,
    "estimated_cost_usd": 0.000312,
    "latency_ms": 3420,
})
```

HTTP request logs include `http_method`, `http_path`, `http_status`, `duration_ms`. 5xx responses log at WARNING level for easy filtering.

**Cloud Logging queries:**
```
jsonPayload.message="llm_call" AND jsonPayload.agent="competitive_benchmarker"
jsonPayload.message="llm_quality" AND severity="WARNING"
jsonPayload.http_status>=500
```

---

### LLM Call Tracking (`core/llm_tracker.py`)

Four wrapper functions replace direct OpenAI SDK calls across all 10 agents:

- `tracked_responses(client, agent, **kwargs)` — wraps `client.responses.create()`
- `tracked_chat(client, agent, **kwargs)` — wraps `client.chat.completions.create()`
- `tracked_embeddings(client, agent, **kwargs)` — wraps `client.embeddings.create()`
- `tracked_image(client, agent, **kwargs)` — wraps `client.images.generate()`

Each wrapper times the call, reads `usage` from the response, computes estimated cost using a built-in price table, and emits a `llm_call` structured log + Prometheus metrics.

**Cost table (USD per token, as of 2025):**
- gpt-4o-mini: $0.15/1M input, $0.60/1M output
- text-embedding-3-small: $0.02/1M tokens
- dall-e-3: $0.04/image

---

### LLM Output Quality Scoring (`core/quality_scorer.py`)

Every LLM output is scored 0.0–1.0 before being returned to the caller. Scores below 0.7 log at WARNING level. The scorer runs 5 check types:

1. **Required keys** — are all expected top-level fields present and non-null?
2. **Non-empty lists** — are array fields populated?
3. **Nested key paths** — do deep fields like `unit_economics.estimated_cac` exist?
4. **Numeric range** — are score fields in the expected range (e.g., 1–10)?
5. **Minimum length** — is the output at least N characters (truncation detection)?

Per-agent convenience wrappers (`score_segment_analysis`, `score_competitive_benchmarking`, `score_positioning`, etc.) encode each agent's expected schema.

---

### Custom Prometheus Metrics (`core/metrics.py`)

7 AI-specific metrics exposed at `GET /metrics`:

| Metric | Type | Labels |
|---|---|---|
| `llm_calls_total` | Counter | agent, model, call_type, status |
| `llm_latency_seconds` | Histogram | agent, call_type |
| `llm_tokens_total` | Counter | agent, token_type (prompt/completion) |
| `llm_cost_usd_total` | Counter | agent |
| `llm_quality_score` | Histogram | agent |
| `pipeline_step_duration_seconds` | Histogram | step, status |
| `cache_operations_total` | Counter | operation (hit/miss/set/expired), agent |

---

### Pipeline Tracing (`core/pipeline_tracer.py`)

Every agent invocation in the 6 main pipeline endpoints is wrapped in `trace_step()`:

```python
with trace_step(db, step="competitive_benchmarker", project_id=project.id):
    result = run_competitive_benchmarking(...)
```

This records a row in `pipeline_runs` table with: `step`, `project_id`, `status`, `started_at`, `completed_at`, `duration_ms`, `error_msg`. Cached results are logged with `status="cached"` instead of running the agent.

**Query to find slowest steps:**
```sql
SELECT step, AVG(duration_ms), COUNT(*) FROM pipeline_runs
WHERE status = 'success' GROUP BY step ORDER BY AVG(duration_ms) DESC;
```

---

### DB-Backed Response Caching (`core/response_cache.py`)

LLM results are cached in the `llm_cache` table keyed by SHA-256 of `agent + inputs`. On cache hit, the entire LLM + Google Places pipeline is skipped.

| Endpoint | Agent cached | TTL |
|---|---|---|
| POST /analysis/run | competitive_benchmarker | 24h |
| POST /positioning/generate | positioning_copilot | 6h |
| POST /personas/generate | persona_builder | 6h |
| POST /strategy/generate | channel_strategy_planner | 12h |
| POST /roadmap/generate | roadmap_planner | 12h |

Cache key is computed from inputs that affect the output (e.g., `analysis_report_id`, `persona_ids`) — not from the full payload — so trivial field changes don't invalidate the cache.

---

### Token Budget Enforcement (`core/token_budget.py`)

Per-agent token budgets prevent unbounded prompt growth as projects accumulate data:

| Agent | Budget (tokens) |
|---|---|
| segment_analyst | 3000 |
| segment_analyst_chat | 2000 |
| competitive_benchmarker | 3500 |
| memory_context | 600 |
| chat_history | 400 |

`trim_str(text, max_tokens, label)` and `trim_list(items, max_tokens, label)` truncate inputs and log `token_budget_exceeded` warnings when truncation occurs.

---

### Embedding Retrieval Evaluation (`services/memory_store.py`)

After semantic search, `retrieve_relevant_memory()` computes cosine similarity scores for every returned chunk and logs:
- `avg_similarity` — average similarity across returned chunks
- `min_similarity` — lowest similarity (potential noise)
- `low_relevance=True` when min_similarity < 0.75

This lets you detect when the RAG system is returning weakly-relevant context and tune the similarity threshold accordingly.

---

## 15. Interview Q&A

### System Design

**Q: Walk me through the architecture of this project.**

React SPA hosted on Firebase Hosting talks to a FastAPI backend on Cloud Run via HTTPS REST/JSON. The backend uses Supabase (managed PostgreSQL + pgvector) for persistence, OpenAI for all AI generation, and Google Places API for competitor data. Firebase Hosting serves static files over a CDN globally. Cloud Run handles API requests serverlessly — scales to zero when idle, scales out via new container instances under load. No custom infra to manage.

---

**Q: Why Cloud Run instead of a traditional server or EC2?**

Cloud Run fits a marketing tool perfectly — usage is bursty (users generate content in sessions, then go idle for hours). With scale-to-zero we pay essentially nothing during idle periods. It's fully managed — no server patching, OS updates, or load balancer config. The main trade-off is cold starts (~5 seconds after idle), which we accept for the cost savings at this scale. For high-traffic production we'd set `--min-instances 1` to keep it warm at ~$5/mo.

---

**Q: Why Supabase instead of self-managed PostgreSQL?**

Supabase provides managed PostgreSQL with the pgvector extension pre-available — both critical for this project. It handles backups, SSL, connection pooling, and the dashboard makes data inspection easy. For a startup-phase project it's the right trade-off between control and operational overhead. The connection pooler handles connection limits gracefully, which matters for a serverless backend that creates many short-lived connections.

---

**Q: How does the content generation pipeline work end-to-end?**

User selects a content type (e.g., "Email Newsletter"), sets tone and adds context → frontend calls `POST /api/mvp/content/generate` → backend loads the project's business profile context → constructs a prompt with asset type, tone, audience, and any semantic memory from the user's questionnaire responses → calls `gpt-4o-mini` with `json_object` response format → returns structured JSON with headline, body, CTA, etc. → frontend renders in a card UI.

---

### Authentication

**Q: How does your authentication work?**

Email + password auth with a custom JWT. On registration, credentials are stored in `pending_registrations` and a verification email is sent. Once the user clicks the link, a real `User` record is created. On login, we validate credentials against a PBKDF2-SHA256 hash (310,000 iterations) and issue a token signed with HMAC-SHA256. The token carries a user ID and 24-hour expiry. The frontend stores it in localStorage and sends it as `Authorization: Bearer <token>` on every request.

---

**Q: Why implement JWT manually instead of using PyJWT?**

To reduce dependencies in the security-critical auth layer and to understand the mechanism fully. Using stdlib `hmac`, `hashlib`, and `base64` — there's nothing opaque happening. The trade-off: these tokens aren't interoperable with standard JWT tooling. If a third-party service ever needs to verify tokens (e.g., an edge function), we'd switch to standard JWT.

---

**Q: Explain the email verification flow and why you designed it this way.**

When a user registers, we don't create a `User` record. Instead we create a `PendingRegistration` row with hashed credentials and a secure random token, then email a link. When they click it, the token is validated, expiry checked, a real `User` is created, and the pending row is deleted.

This is cleaner than an `is_verified` flag because: the `users` table only ever contains verified accounts, there's no risk of business logic accidentally including unverified users in queries, and expired signups can be cleaned up without touching real user records. The table separation makes the invariant explicit.

---

**Q: How do you prevent brute force on login?**

Rate limiting via `slowapi` on the generate endpoints. Login itself isn't rate limited in the current implementation — that's a known gap. The password hashing uses 310,000 PBKDF2 iterations which makes offline brute force slow. For production hardening we'd add per-IP rate limiting on auth endpoints.

---

### Database

**Q: Why store AI output as `Text` JSON rather than PostgreSQL `jsonb`?**

The AI output structure varies per generation type and evolves as we update prompts. Using `Text` keeps migrations simple — when the JSON schema changes, no ALTER TABLE needed. We don't do SQL queries inside the JSON (no `->` operators), so `jsonb` indexing provides no benefit. The data is read and written as blobs. If we needed to filter generations by output fields, we'd migrate those columns to `jsonb`.

---

**Q: What is pgvector and why do you need it?**

pgvector is a PostgreSQL extension that adds a native `vector` column type and approximate nearest-neighbor search (via IVFFlat/HNSW indexes). We use it to store 1536-dimension embeddings of questionnaire responses in `memory_chunks`. When generating content, we semantically search for the most relevant context from the user's prior answers, giving the AI grounding in their specific business. This avoids stuffing the entire conversation history into every prompt.

---

**Q: How do you handle schema migrations in production?**

Alembic manages migrations. Migration files are version-controlled in `alembic/versions/`. We run `alembic upgrade head` manually before each deployment. The `env.py` reads `DATABASE_URL` from the environment, overriding the static value in `alembic.ini`, so we never hardcode connection strings. One gotcha: `%` characters in the URL must be escaped to `%%` before passing to `config.set_main_option` due to configparser's interpolation syntax.

---

### API Design

**Q: Why are `/api/projects` and `/api/business-profiles` the same endpoints?**

The underlying model is called `Project` but the domain concept is "business profile." Both route aliases exist to support a naming refactor without breaking existing frontend code. They share identical handler functions via FastAPI's route decorator — `@router.get("/projects")` and `@router.get("/business-profiles")` both point to `get_projects`.

---

**Q: How does rate limiting work?**

`slowapi` (a Starlette wrapper around Flask-Limiter) decorates individual endpoints with `@limiter.limit("10/minute")`. The limiter uses client IP as the key. On breach it returns HTTP 429 with `X-RateLimit-*` and `Retry-After` headers. The limiter is attached to `app.state` in `main.py`. This protects OpenAI API costs — each generate call costs money.

---

**Q: How do you protect admin-only endpoints?**

The `/api/generations` endpoint uses a `require_internal_api_key` FastAPI dependency. The caller must include a header with the value of `INTERNAL_API_KEY`. This is separate from user JWT auth — it's for server-to-server or admin tooling use. The key is set as a Cloud Run environment variable and never exposed to frontend clients.

---

### Frontend

**Q: How do you manage state across a multi-step marketing workflow?**

All state lives in `useMvpWorkflow.js`, a single custom React hook. It exposes `state`, `set`, and `actions`. Each page component receives the `workflow` object as a prop and reads/writes to this central store. The workflow progresses linearly (questionnaire → analysis → personas → content). When starting a new session, `resetForNewSession()` clears all session-specific state (sessionId, artifacts, chat history) while preserving auth and project selection.

---

**Q: Why store the JWT in localStorage instead of an HTTP-only cookie?**

Simpler setup for a SPA calling a cross-origin API (Firebase domain → Cloud Run domain). HTTP-only cookies with cross-origin require `SameSite=None; Secure` plus specific CORS `allow_credentials` configuration. The trade-off: localStorage is accessible to JavaScript, making it vulnerable to XSS attacks. For a higher-security implementation, HTTP-only cookies are preferable. Current implementation prioritizes simplicity at the cost of XSS token theft risk.

---

### Infrastructure

**Q: Why does Cloud Run use 1 uvicorn worker?**

Cloud Run scales horizontally — it creates new container instances under load, not new processes within a container. FastAPI with uvicorn is async (handles concurrent requests on a single event loop via Python asyncio). Adding multiple workers would compete for memory within the same instance without increasing throughput meaningfully in this model. The Dockerfile comment explains this explicitly.

---

**Q: How do you handle CORS for a cross-origin deployment?**

`CORS_ORIGINS` env var on Cloud Run holds a comma-separated list of allowed origins (e.g., `https://ai-marketing-prod.web.app`). This is parsed in `config.py` and passed to FastAPI's `CORSMiddleware`. For local dev, it falls back to localhost:5173 and localhost:5174. The critical production requirement: the Firebase Hosting URL must exactly match — no trailing slash.

---

**Q: Explain the Firebase Hosting caching strategy.**

Vite generates JS/CSS bundle filenames with content hashes (e.g., `main.a3f2b1.js`). Since filenames change on every build, these can be cached forever: `Cache-Control: max-age=31536000, immutable`. The `index.html` entry point gets `Cache-Control: no-cache` so the browser always fetches the latest version, which then loads the correctly-hashed (and correctly-cached) assets. This gives best-of-both-worlds: aggressive caching for assets + always-fresh entry point.

---

### Tricky Bugs

**Q: How did you optimize LLM token usage and reduce costs?**

The competitive benchmarking pipeline fetches up to 20 competitors from Google Places. The naive approach — sending all 20 with full reviews and hours to the LLM — created an 8k+ token prompt that took over 100 seconds and timed out.

The fix was a RAG-style pre-filtering step using vector embeddings **before** the LLM call:

1. Convert each competitor's basic data (name, types, vicinity) into a short text string
2. Embed all 20 candidates using `text-embedding-3-small` alongside the user's business context
3. Rank by cosine similarity — the 5 competitors most semantically similar to the user's business type bubble up
4. Only then fetch full Place Details (reviews, hours) for those 5
5. Send just 5 enriched competitors to the LLM

This reduced the LLM prompt from ~8k to ~2k tokens, response time from 100s to ~15s, and Google Places API calls from 10 to 5. The embedding step itself costs ~$0.00003 — negligible compared to the savings on the LLM call.

The key insight: **embeddings are cheap ($0.02/1M tokens) and fast (~200ms). Use them to filter before the expensive LLM call, not after.** This is the same principle as RAG in document Q&A — retrieve relevant chunks first, then generate.

---

**Q: Describe the hardest bug you fixed in this project.**

The competitive benchmarking page was showing the price-quality chart but silently omitting SWOT analysis, hours gap, and opportunity gap sections. No errors, no logs — just empty sections. Root cause: the AI service was using `client.responses.create` (OpenAI Responses API) which returns plain text. The text parser used regex to extract JSON-like sections, but the model's formatting was inconsistent and the regex silently failed to match.

Fix: switched to `client.chat.completions.create` with `response_format={"type": "json_object"}`. This forces the model to return valid JSON with all required keys. Added logging for the raw response and the keys returned so future issues would be immediately visible. After the fix all sections appeared reliably.

---

**Q: What was the `%` configparser bug and how did you fix it?**

When running Alembic migrations against Supabase with a password containing `@` (which URL-encodes to `%40`), Python raised:
```
ValueError: invalid interpolation syntax at position 59
```
Alembic passes the `DATABASE_URL` to `config.set_main_option()`, which internally uses Python's `configparser`. configparser treats `%` as the start of a `%(variable)s` interpolation sequence. The `%40` in the URL was interpreted as a malformed interpolation.

Fix: escape `%` to `%%` before passing to configparser:
```python
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
```
configparser reads `%%` and unescapes it to `%`, giving SQLAlchemy the correct URL. The simpler production fix: use passwords with no special characters to avoid URL encoding entirely.

---

### Observability & Cost

**Q: How do you monitor LLM costs and prevent budget overruns?**

Every OpenAI API call goes through a tracking wrapper (`llm_tracker.py`) that reads the `usage` field from the response and computes estimated cost using a built-in price table. Costs are logged as structured JSON (`llm_call` message) and emitted as a Prometheus counter (`llm_cost_usd_total` labeled by agent). This lets us see exactly which agent burns the most money. To prevent overruns: token budgets cap prompt sizes per agent, response caching avoids repeat calls, and embedding-based pre-filtering reduces LLM calls per pipeline run.

---

**Q: How do you evaluate LLM output quality in production?**

After every LLM call, the output goes through a quality scorer that checks: required fields present, lists non-empty, nested paths exist, numeric scores in range, minimum output length met. Each check is binary — passed or failed. The ratio gives a 0–1 quality score. Scores below 0.7 emit a WARNING log with which checks failed. This creates a quality trend over time — if a prompt change silently degrades outputs, we catch it in the next deployment via quality score drop.

---

**Q: How do you handle observability for an AI system specifically?**

Standard HTTP metrics (latency, error rate) aren't enough for LLM systems — you need AI-specific signals. We added: (1) per-agent token tracking so you know which prompt is most expensive, (2) LLM latency histograms by agent and call type (chat vs embedding vs image), (3) quality scores to catch prompt regressions, (4) retrieval evaluation (cosine similarity scores on RAG results), and (5) pipeline tracing per project so you can see where users drop off. All emitted as structured JSON logs (indexed by Cloud Logging) and Prometheus metrics (queryable via `/metrics`).

---

**Q: How does your caching strategy work for LLM responses?**

We use a DB-backed cache (`llm_cache` table) keyed by SHA-256 of the agent name + canonical inputs. For competitive benchmarking (the most expensive step — Google Places API calls + LLM enrichment), results are cached for 24 hours. The cache key is computed from inputs that affect the output (business address + interview responses), not the full HTTP payload, so irrelevant field changes don't bust the cache. Cache hits skip the entire pipeline — zero OpenAI calls, zero Google Places calls. Hits/misses/expirations are logged and tracked in Prometheus.
