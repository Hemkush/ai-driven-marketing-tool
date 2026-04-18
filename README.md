# MarketPilot AI

An AI-powered marketing strategy platform that transforms a 10-minute business interview into a complete 90-day go-to-market strategy.

**Live App:** Firebase Hosting + Google Cloud Run  
**Portfolio:** [portfolio.html](portfolio.html) — full technical showcase for recruiters

---

## What It Does

1. **Adaptive Interview** — AI conducts a ~10 min marketing Q&A, dynamically generating follow-up questions based on topic coverage gaps
2. **Competitive Analysis** — discovers real local competitors via Google Places, ranks by semantic relevance using embeddings, generates SWOT + opportunity gaps
3. **Market Analysis** — TAM/SAM/SOM sizing, CAC/LTV unit economics, segment attractiveness scoring, and a live Q&A copilot powered by RAG
4. **Brand Positioning** — differentiated positioning statement grounded in competitive intelligence
5. **Buyer Personas** — 3 psychographic profiles mined from Google review language
6. **Channel Strategy** — prioritized marketing channels with budget allocation
7. **90-Day Roadmap** — week-by-week implementation playbook with KPIs
8. **Content Studio** — text assets (social, email, ad copy) + DALL-E 3 visuals

---

## Architecture

```
React 19 (Firebase Hosting)
    ↕ HTTPS / REST + JWT
FastAPI (Google Cloud Run)
    ↕ Service calls
10 AI Agents (OpenAI gpt-4o-mini + text-embedding-3-small + DALL-E 3)
    ↕ External APIs
Google Places · OpenAI · SendGrid
    ↕ SQLAlchemy ORM
PostgreSQL + pgvector (Supabase)
```

---

## Tech Stack

**Backend:** Python · FastAPI · OpenAI SDK · SQLAlchemy · psycopg v3 · pgvector · Alembic · NumPy · Sentry  
**Frontend:** React 19 · Vite · TailwindCSS · React Router · Axios  
**Infrastructure:** Google Cloud Run · Firebase Hosting · Supabase · Google Container Registry  
**Observability:** Structured JSON logging · LLM cost tracking · Quality scoring · Prometheus metrics · Pipeline tracing · Response caching · Token budgets

---

## Project Structure

```
ai-driven-marketing-tool/
├── apps/
│   ├── backend/          # FastAPI app — see apps/backend/README.md
│   │   ├── app/
│   │   │   ├── api/mvp/  # Route handlers (analysis, content, personas…)
│   │   │   ├── core/     # Auth, config, logging, metrics, caching, tracing
│   │   │   ├── services/ # 10 AI agent implementations
│   │   │   └── models.py # SQLAlchemy models (15 tables)
│   │   └── alembic/      # DB migration versions
│   └── frontend/         # React SPA — see apps/frontend/README.md
│       └── src/
│           ├── pages/    # Route-level page components
│           ├── components/
│           ├── state/    # useMvpWorkflow.js — global workflow state
│           └── lib/      # API clients
├── portfolio.html         # Technical project showcase
├── Developer_Handoff.md   # Comprehensive engineering reference
├── DEPLOYMENT.md          # Cloud deployment guide
└── docker-compose.yml     # Local full-stack dev environment
```

---

## Local Development

**Backend:**
```bash
cd apps/backend
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd apps/frontend
npm install
npm run dev
```

Or use Docker Compose:
```bash
docker-compose up
```

---

## Deployment

**Backend (Cloud Run):**
```bash
gcloud builds submit apps/backend --tag gcr.io/ai-marketing-prod/ai-marketing-backend && gcloud run deploy backend --image gcr.io/ai-marketing-prod/ai-marketing-backend --region us-central1 --platform managed
```

**Frontend (Firebase):**
```bash
cd apps/frontend && npm run build && firebase deploy --only hosting
```

---

## Key Engineering Details

- **No email verification** — registration creates account + returns JWT immediately
- **pgvector psycopg v3** — SQLAlchemy `connect` event registers vector type adapter (without it, embeddings store as NULL)
- **OpenAI regional keys** — requires `OPENAI_BASE_URL=https://us.api.openai.com/v1`
- **Supabase pooler** — username must be `postgres.PROJECT_REF` format
- **Response caching** — SHA-256 keyed DB cache with 24h TTL eliminates redundant LLM calls
- **Token budgets** — per-agent limits prevent runaway costs from large context windows

See [Developer_Handoff.md](Developer_Handoff.md) for the full engineering reference.
