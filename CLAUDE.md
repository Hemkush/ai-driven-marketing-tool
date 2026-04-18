# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend

```bash
cd apps/backend
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload        # starts on http://localhost:8000
```

Run all tests (must use venv Python, not global):
```bash
cd apps/backend
.venv\Scripts\python -m pytest -q
```

Run a single test file:
```bash
.venv\Scripts\python -m pytest tests/test_mvp_onboarding.py -q
```

Tests set `PYTEST_CURRENT_TEST` env var automatically — `settings.can_use_openai()` returns `False` during tests so no real OpenAI calls are made.

### Frontend

```bash
cd apps/frontend
npm install
npm run dev        # http://localhost:5173
npm run build
firebase deploy --only hosting
```

### Deploy to Production

Backend (Cloud Run):
```bash
gcloud builds submit C:\Users\kushw\Downloads\CodingProjects\ai-driven-marketing-tool\apps\backend --tag gcr.io/ai-marketing-prod/ai-marketing-backend && gcloud run deploy backend --image gcr.io/ai-marketing-prod/ai-marketing-backend --region us-central1 --platform managed
```

DB migrations (production):
```bash
gcloud run jobs execute alembic-migrate --region us-central1
```

---

## Architecture

### Request Flow

```
React SPA (Firebase)
  → FastAPI (Cloud Run) — routes.py + api/mvp/*.py
    → services/*.py (AI agents)
      → OpenAI API / Google Places API
      → PostgreSQL + pgvector (Supabase)
```

### Backend structure

- `app/main.py` — app startup: logging, Sentry init, CORS, rate limiter, Prometheus at `/metrics`
- `app/api/routes.py` — auth (register/login/me) + projects CRUD + legacy generate endpoints
- `app/api/mvp/` — the main pipeline routes: `questionnaire.py`, `analysis.py`, `positioning.py`, `personas.py`, `research.py`, `strategy.py`, `content.py`
- `app/api/mvp/deps.py` — shared Pydantic schemas, auth helpers (`_owned_project_or_404`), all serializers (`_serialize_*`), question dedup logic (`_is_duplicate_question`), and the cross-domain workflow snapshot builder (`_build_session_workflow_snapshot`)
- `app/services/` — one file per AI agent; each agent has deterministic fallback logic that fires when `settings.can_use_openai()` is False
- `app/core/` — config, auth (JWT), rate limiting, and the observability stack (see below)
- `app/models.py` — all 15 SQLAlchemy models
- `app/db.py` — engine setup + pgvector type registration on every psycopg v3 connection

### Frontend structure

- `src/state/useMvpWorkflow.js` — single custom hook that holds ALL app state; passed as `workflow` prop everywhere. Contains all API actions (register, login, pipeline steps).
- `src/lib/api.js` — Axios instance with Bearer token injector + 401 redirect handler
- `src/lib/mvpClient.js` — typed wrappers over all API endpoints
- `src/pages/` — one page per pipeline step; all read from `workflow.state`, call `workflow.actions`

### Observability stack (`app/core/`)

| Module | Purpose |
|---|---|
| `logging_config.py` | JSON formatter → Cloud Logging severity; call `setup_logging()` once at startup |
| `llm_tracker.py` | `tracked_responses/chat/embeddings/image` wrappers — log tokens, cost, latency per agent |
| `quality_scorer.py` | `score_*(output)` returns 0.0–1.0 schema completeness after each LLM call |
| `response_cache.py` | `make_cache_key / get_cached / set_cached` — SHA-256 keyed, 24h TTL, DB-backed |
| `metrics.py` | 7 Prometheus counters/histograms; `record_llm_call / record_cache_op / record_pipeline_step` |
| `pipeline_tracer.py` | `trace_step(db, step, project_id)` context manager → writes to `pipeline_runs` table |
| `token_budget.py` | Per-agent token budgets; `trim_str / trim_list` enforce before prompt assembly |

### DB schema key points

- All pipeline outputs (analysis, positioning, personas, strategy, roadmap, content) are stored as JSON text columns linked by `project_id` + `source_session_id`
- `memory_chunks` holds 1536-dim pgvector embeddings of interview Q&A for RAG retrieval
- `llm_cache` — SHA-256 keyed response cache; TTL enforced in app code, not DB
- `pipeline_runs` — step tracing with `duration_ms` and `status`
- `pending_registrations` — unused; email verification is disabled. Registration goes directly to `users`

### Critical integration notes

- **pgvector + psycopg v3**: `db.py` registers the vector type adapter on every new connection via a SQLAlchemy `connect` event. Without this, embeddings silently store as NULL.
- **OpenAI regional keys**: `OPENAI_BASE_URL` must be `https://us.api.openai.com/v1` for regional keys. Wrong base URL causes 401 `incorrect_hostname`.
- **Supabase pooler**: `DATABASE_URL` username must be `postgres.PROJECT_REF`, not just `postgres`.
- **LLM fallbacks**: Every agent checks `settings.can_use_openai()` and returns deterministic rule-based output if False. This is how tests work — no mocking needed.
- **`business_profile_id` = `project_id`**: The API accepts both field names interchangeably (legacy alias). `_resolve_business_profile_id()` in `deps.py` handles the resolution.
- **Artifact lookup**: `_artifact_for_session()` in `deps.py` looks up pipeline outputs first by exact `source_session_id`, then falls back to timestamp range between sessions.
