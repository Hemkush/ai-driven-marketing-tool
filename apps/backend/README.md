# MarketPilot AI — Backend

FastAPI backend powering the MarketPilot AI platform. Includes 10 AI agents, RAG memory, competitive intelligence, and a full MLOps observability stack.

## Quick Start (Local)

```powershell
cd apps/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## Required Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | Yes | Secret for signing JWT tokens |
| `INTERNAL_API_KEY` | Yes | Key for internal admin endpoints |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_BASE_URL` | No | Default: `https://us.api.openai.com/v1` (use regional URL for regional keys) |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | No | Default: `text-embedding-3-small` |
| `MEMORY_TOP_K` | No | Default: `6` — number of RAG chunks retrieved per query |
| `CORS_ORIGINS` | No | Comma-separated allowed origins, e.g. `https://your-app.web.app` |
| `SENTRY_DSN` | No | Sentry DSN for error tracking and APM |
| `SENTRY_ENVIRONMENT` | No | Default: `production` |
| `LOG_LEVEL` | No | Default: `INFO` |
| `GOOGLE_PLACES_API_KEY` | No | Required for competitive benchmarking (Google Places) |
| `SENDGRID_API_KEY` | No | Required for transactional emails |

## Deploy to Cloud Run

```bash
gcloud builds submit C:\Users\kushw\Downloads\CodingProjects\ai-driven-marketing-tool\apps\backend --tag gcr.io/ai-marketing-prod/ai-marketing-backend && gcloud run deploy backend --image gcr.io/ai-marketing-prod/ai-marketing-backend --region us-central1 --platform managed
```

## Run Database Migrations

Local:
```powershell
alembic upgrade head
```

Production (Cloud Run Job):
```bash
gcloud run jobs execute alembic-migrate --region us-central1
```

## Run Tests

```powershell
cd apps/backend
.venv\Scripts\python -m pytest -q
```

Run specific test suite:
```powershell
.venv\Scripts\python -m pytest tests/test_mvp_onboarding.py -q
```

## AI Agents

| Agent | File | Purpose |
|---|---|---|
| Onboarding Interviewer | `services/onboarding_interviewer.py` | Adaptive 10-min marketing interview |
| Competitive Benchmarker | `services/competitive_benchmarker.py` | Google Places + embedding-ranked competitor analysis |
| Segment Analyst | `services/segment_analyst.py` | TAM/SAM/SOM, CAC/LTV, SWOT, RAG Q&A copilot |
| Positioning Copilot | `services/positioning_copilot.py` | Brand positioning statements |
| Persona Builder | `services/persona_builder.py` | 3 psychographic buyer personas |
| Market Researcher | `services/market_researcher.py` | Multi-source insight synthesis |
| Channel Strategy Planner | `services/channel_strategy_planner.py` | Budget-split channel recommendations |
| Roadmap Planner | `services/roadmap_planner.py` | 90-day week-by-week playbook |
| Content Studio | `services/content_studio.py` | Text + DALL-E 3 marketing assets |
| Memory Store | `services/memory_store.py` | RAG embeddings (pgvector, 1536-dim) |

## Observability Stack

| Module | File | What it does |
|---|---|---|
| Structured Logging | `core/logging_config.py` | JSON logs → Google Cloud Logging with severity mapping |
| LLM Tracker | `core/llm_tracker.py` | Token counts, cost estimation, latency per agent call |
| Quality Scorer | `core/quality_scorer.py` | 0.0–1.0 schema completeness check on LLM outputs |
| Response Cache | `core/response_cache.py` | SHA-256 keyed DB cache with 24h TTL |
| Prometheus Metrics | `core/metrics.py` | 7 AI-specific metrics (cost, latency, quality, cache ops) |
| Pipeline Tracer | `core/pipeline_tracer.py` | Per-step duration_ms + status recorded to `pipeline_runs` table |
| Token Budget | `core/token_budget.py` | Per-agent token limits with trim_str/trim_list enforcement |

## Key Notes

- **Email verification is disabled.** Registration creates the account and returns a JWT immediately.
- **pgvector requires type registration.** A SQLAlchemy `connect` event registers the psycopg v3 adapter on every new connection — without this, embeddings store as NULL.
- **OpenAI regional keys** require `OPENAI_BASE_URL=https://us.api.openai.com/v1`. Setting the wrong base URL causes a 401 `incorrect_hostname` error.
- **Supabase pooler username** format is `postgres.PROJECT_REF` (not just `postgres`).
- Runtime schema auto-creation is disabled — always run Alembic migrations before starting.

## User Flow

1. Register / Login (no email verification required)
2. Create a Business Profile with name + address
3. Start Interview → answer adaptive questions (~10 min)
4. Run Analysis → competitive benchmarking + market analysis
5. Generate Positioning → brand differentiation statement
6. Build Personas → 3 buyer profiles
7. Run Research → synthesized insights
8. Generate Strategy → channel plan + 90-day roadmap
9. Content Studio → text assets + DALL-E 3 visuals
