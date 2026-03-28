# MarketPilot — Developer Handoff Report

**Project:** AI-Driven Marketing Tool (MarketPilot)
**Report Date:** March 2026
**Purpose:** Complete technical handoff for any developer joining this project

---

## Table of Contents

1. [What This Product Is](#1-what-this-product-is)
2. [Who It Is For](#2-who-it-is-for)
3. [Tech Stack](#3-tech-stack)
4. [Repository Structure](#4-repository-structure)
5. [Local Development Setup](#5-local-development-setup)
6. [Environment Variables](#6-environment-variables)
7. [Database Schema](#7-database-schema)
8. [Alembic Migrations](#8-alembic-migrations)
9. [The 9-Step Workflow Pipeline](#9-the-9-step-workflow-pipeline)
10. [Backend Services Reference](#10-backend-services-reference)
11. [API Endpoints Reference](#11-api-endpoints-reference)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Authentication System](#13-authentication-system)
14. [Competitive Benchmarking Pipeline](#14-competitive-benchmarking-pipeline)
15. [Memory System (pgvector)](#15-memory-system-pgvector)
16. [Key Decisions and Why](#16-key-decisions-and-why)
17. [Known Gotchas and Quirks](#17-known-gotchas-and-quirks)
18. [What Is Not Built Yet](#18-what-is-not-built-yet)

---

## 1. What This Product Is

MarketPilot is a full-stack AI-powered marketing strategy tool for small and mid-size business (SMB) owners. It guides business owners through a structured 9-step workflow to produce a complete, AI-generated marketing strategy — from initial business discovery through to content-ready marketing assets.

The product asks the business owner questions about their business through an AI-driven chat interview, then progressively generates:

- A local competitor benchmarking report (using Google Places API + OpenAI)
- A positioning statement and tagline
- Buyer personas grounded in real competitor reviews
- Market research
- A channel strategy
- A 90-day execution roadmap
- Campaign content assets (social posts, copy, etc.)

Every output is tied to the session in which it was generated, so re-running any step produces a new version without destroying prior work.

---

## 2. Who It Is For

The end user is a **non-technical small business owner** — e.g. a hair salon owner, a florist, a landscaper, a plumber. They have no marketing background. The product does all the strategic thinking for them and presents outputs in plain language.

The product is built by a **solo developer + Claude AI** pair. All major implementation decisions were made iteratively in conversation with Claude Code.

---

## 3. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React | 19.2.0 |
| Frontend Router | React Router DOM | 7.13.1 |
| Frontend HTTP | Axios | 1.13.6 |
| Frontend Build | Vite | 7.x |
| Backend | FastAPI | 0.133.1 |
| Backend Server | Uvicorn | 0.41.0 |
| ORM | SQLAlchemy | 2.0.47 |
| DB Driver | psycopg (v3) | 3.3.3 |
| Database | PostgreSQL | 14+ |
| Vector Extension | pgvector | 0.4.1 |
| Migrations | Alembic | 1.18.4 |
| AI Provider | OpenAI API | SDK 2.24.0 |
| AI Model | gpt-4o-mini | (configurable) |
| Embeddings | text-embedding-3-small | 1536 dimensions |
| Competitor Data | Google Places API | v1 (REST) |
| Rate Limiting | SlowAPI | 0.1.9 |
| Validation | Pydantic | 2.12.5 |
| Testing | Pytest | 9.0.2 |

**No charting library is used on the frontend.** The Price vs Rating scatter chart is built with raw SVG inside React.

---

## 4. Repository Structure

```
ai-driven-marketing-tool/
├── apps/
│   ├── backend/
│   │   ├── alembic/
│   │   │   └── versions/           ← Database migration files
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── mvp_routes.py   ← All MVP workflow endpoints (~2000 lines)
│   │   │   │   └── routes.py       ← Auth + legacy endpoints
│   │   │   ├── core/
│   │   │   │   ├── auth.py         ← JWT + password hashing
│   │   │   │   ├── config.py       ← All env vars (single source of truth)
│   │   │   │   ├── settings.py     ← Pydantic-based settings (secondary, mostly unused)
│   │   │   │   ├── mvp_registry.py ← Agent and MCP server registry
│   │   │   │   ├── rate_limit.py   ← Rate limiter setup
│   │   │   │   └── security.py     ← Internal API key validation
│   │   │   ├── services/
│   │   │   │   ├── onboarding_interviewer.py    ← Chat interview AI
│   │   │   │   ├── competitive_benchmarker.py  ← Google Places + OpenAI pipeline
│   │   │   │   ├── segment_analyst.py          ← Analysis assistant chat
│   │   │   │   ├── positioning_copilot.py      ← Positioning statement generator
│   │   │   │   ├── market_researcher.py        ← Research report generator
│   │   │   │   ├── persona_builder.py          ← Buyer persona generator
│   │   │   │   ├── channel_strategy_planner.py ← Channel strategy generator
│   │   │   │   ├── roadmap_planner.py          ← 90-day roadmap generator
│   │   │   │   ├── content_studio.py           ← Content asset generator
│   │   │   │   └── memory_store.py             ← pgvector embeddings store/retrieve
│   │   │   ├── models.py           ← All SQLAlchemy ORM models
│   │   │   ├── db.py               ← DB engine + session setup
│   │   │   └── main.py             ← FastAPI app entry point
│   │   ├── tests/                  ← 11 test files
│   │   ├── .env                    ← Local secrets (never commit)
│   │   ├── alembic.ini
│   │   └── requirements.txt
│   └── frontend/
│       └── src/
│           ├── pages/              ← One page per workflow step (9 pages)
│           ├── components/         ← Shared UI components (12 components)
│           ├── state/
│           │   └── useMvpWorkflow.js ← ALL global state + API actions (single hook)
│           ├── lib/
│           │   ├── api.js          ← Axios instance + auth token management
│           │   └── mvpClient.js    ← Typed API method wrappers
│           ├── App.jsx             ← Router + progress tracking
│           └── index.css           ← All styles (single file, ~2700 lines)
```

---

## 5. Local Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ with pgvector extension installed
- An OpenAI API key
- (Optional) A Google Places API key

### Backend Setup

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create the database
psql -U postgres -c "CREATE DATABASE aimarketing;"
psql -U postgres -d aimarketing -c "CREATE EXTENSION vector;"

# Copy env template and fill in your values
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd apps/frontend
npm install
npm run dev        # Starts at http://localhost:5173
```

### Verify It Works

Open `http://localhost:5173`, register an account, create a business profile, and start the marketing discovery interview.

---

## 6. Environment Variables

All environment variables are read in `apps/backend/app/core/config.py`. This is the single source of truth — do not use `settings.py` for new variables.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API access |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Which OpenAI model to use |
| `OPENAI_BASE_URL` | No | `https://us.api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_TIMEOUT_SECONDS` | No | `45` | Per-request timeout |
| `OPENAI_MAX_RETRIES` | No | `1` | Retry count on failure |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Model for embeddings |
| `MEMORY_TOP_K` | No | `6` | Max memory chunks returned in semantic search |
| `DATABASE_URL` | No | `postgresql+psycopg://postgres:postgres@localhost:5432/aimarketing` | Full DB connection string |
| `GOOGLE_PLACES_API_KEY` | No | — | Enables real competitor data. Without this, benchmarking returns an AI-only fallback |
| `BENCHMARKING_RADIUS_METERS` | No | `5000` | Search radius for nearby competitors (5km) |
| `JWT_SECRET_KEY` | No (dev) | `dev-insecure-secret` | JWT signing key. MUST be set in production |
| `INTERNAL_API_KEY` | No | — | Key for `/api/generations` internal endpoint |
| `APP_ENV` | No | `dev` | Set to `prod` to enforce JWT_SECRET_KEY |
| `FRONTEND_URL` | No | `http://localhost:5173` | Used in CORS origins |
| `CORS_ORIGINS` | No | localhost:5173,5174 | Comma-separated allowed origins |

---

## 7. Database Schema

All models are defined in `apps/backend/app/models.py`.

### `users`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| email | String(255) | Unique, indexed |
| password_hash | String(255) | PBKDF2-SHA256 |
| full_name | String(255) | nullable |
| created_at | DateTime(tz) | server default now() |

### `projects` (Business Profiles)
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| name | String(200) | Business name |
| description | Text | nullable |
| business_address | String(500) | Used for Google Places geocoding |
| owner_id | Integer FK → users.id | indexed |
| created_at | DateTime(tz) | |

### `questionnaire_sessions`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| project_id | Integer FK → projects.id | |
| status | String(40) | `in_progress` or `completed` |
| conversation_analysis_json | Text | nullable. JSON blob of AI analysis of the chat transcript. Saved after each reply so it persists. |
| created_at | DateTime(tz) | |
| updated_at | DateTime(tz) | auto-updated |

### `questionnaire_responses`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| session_id | Integer FK → questionnaire_sessions.id | |
| sequence_no | Integer | Order within session |
| question_text | Text | |
| answer_text | Text | |
| question_type | String(40) | `open_ended` or `mcq` |
| question_options_json | Text | JSON array of options for MCQ |
| source | String(40) | `system_seeded`, `chatbot_generated`, `agent_suggested`, `user_entered` |
| created_at / updated_at | DateTime(tz) | |

### `memory_chunks`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| project_id | Integer FK | |
| session_id | Integer FK | nullable |
| response_id | Integer FK | nullable |
| source_type | String(40) | `questionnaire_response` |
| topic_tag | String(80) | e.g. `pricing`, `target_customer` |
| content_text | Text | The chunk text |
| content_hash | String(64) | SHA-256 for dedup |
| embedding | vector(1536) | pgvector column — 1536 dims for text-embedding-3-small |
| metadata_json | Text | JSON blob |
| created_at | DateTime(tz) | |

### `analysis_reports`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| project_id | Integer FK | |
| source_session_id | Integer FK | nullable — which session generated this |
| status | String(40) | `queued` or `ready` |
| report_json | Text | Full competitive benchmarking JSON |
| created_at / updated_at | DateTime(tz) | |

### `positioning_statements`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| project_id | Integer FK | |
| source_session_id | Integer FK | nullable |
| version | Integer | Auto-incremented per project |
| statement_text | Text | The positioning statement text |
| rationale | Text | Why this positioning was chosen |
| payload_json | Text | Full JSON: target_segment, tagline, key_differentiators, proof_points, rationale |
| created_at | DateTime(tz) | |

### `research_reports`
Same structure as `analysis_reports`. Stores market + competitor + customer research JSON.

### `persona_profiles`
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| project_id | Integer FK | |
| source_session_id | Integer FK | nullable |
| persona_name | String(160) | Quick-access name |
| persona_json | Text | Full persona JSON (see persona structure below) |
| created_at | DateTime(tz) | |

**Persona JSON structure:**
```json
{
  "name": "Loyal Local Laura",
  "basic_profile": { "age", "occupation", "income", "location", "family_status", "photo_prompt" },
  "psychographic_profile": { "goals_and_motivations", "pain_points_and_frustrations", "values_and_priorities", "lifestyle_and_interests" },
  "behavioral_profile": { "shopping_preferences", "decision_making_process", "information_sources", "buying_triggers_and_barriers" },
  "engagement_strategy": { "preferred_channels", "resonant_content_topics", "best_times_to_reach", "key_messages_that_convert" }
}
```

### `channel_strategies`, `roadmap_plans`, `media_assets`
All follow the same pattern: `id`, `project_id`, `source_session_id`, a `_json` column, `created_at`.

---

## 8. Alembic Migrations

Migrations live in `apps/backend/alembic/versions/`. Run with `alembic upgrade head`.

| Revision | Description |
|---|---|
| `c5ce00361ea6` | Create initial `generations` table |
| `b7cf93d4cfc5` | Add `users` and `projects` tables; link generations to projects |
| `54d1d5566ba4` | Empty placeholder (no-op) |
| `54c3c445c9d4` | Full MVP schema: questionnaire sessions, responses, all artifact tables |
| `7c1d9e2a4b11` | Add `source_session_id` FK to all artifact tables |
| `e3a7c9b2d1f4` | Add `payload_json` to `positioning_statements` |
| `a3f1b2c4d8e9` | Add `conversation_analysis_json` to `questionnaire_sessions` |
| `a1f2b3c4d5e6` | Add `business_address` to `projects` |
| `f2b9a8c1d4e7` | Add `memory_chunks` table with pgvector extension + IVFFlat index |
| `9a6b2d4e7f01` | Normalize `question_options_json` storage format |

**Important:** Always run `alembic upgrade head` after pulling new code. Never edit migration files after they are merged.

---

## 9. The 9-Step Workflow Pipeline

The entire product follows this linear pipeline. Each step depends on the previous.

```
Step 1: Business Profile (projects table)
    ↓ owner creates a named workspace with address
Step 2: Marketing Discovery Interview (questionnaire_sessions + questionnaire_responses)
    ↓ AI chatbot asks adaptive questions, saves Q&A + embeddings
Step 3: Competitive Benchmarking (analysis_reports)
    ↓ Google Places API → nearby competitors → OpenAI enrichment
Step 4: Positioning Statement (positioning_statements)
    ↓ AI reads benchmarking report → generates tagline + differentiators
Step 5: Buyer Personas (persona_profiles)
    ↓ AI reads benchmarking + positioning + customer reviews → 3 personas
Step 6: Research Report (research_reports)
    ↓ AI reads analysis → deeper market + customer + competitor research
Step 7: Channel Strategy (channel_strategies)
    ↓ AI reads research + personas → prioritized marketing channels
Step 8: 90-Day Roadmap (roadmap_plans)
    ↓ AI reads strategy + personas → weekly plan with milestones
Step 9: Content Assets (media_assets)
    ↓ AI reads roadmap + strategy → social posts, copy, campaign assets
```

**Session scoping:** Every artifact (analysis, positioning, personas, etc.) is linked via `source_session_id` to the questionnaire session that produced it. If you re-run the interview and generate new artifacts, old ones are not deleted — they remain linked to their original session. The UI shows the most recent per project.

---

## 10. Backend Services Reference

### `competitive_benchmarker.py`
The most complex service. Pipeline:
1. `_infer_business_keyword()` — 3-priority system to find the right Google Places search term:
   - Priority 1: Read stored `conversation_analysis_json` from DB → small AI call on summary
   - Priority 2: Full transcript AI call (fallback if no stored analysis)
   - Priority 3: Extract from primary-service answer (no AI, last resort)
2. `_geocode_address()` — Google Geocoding API → lat/lng
3. `_text_search_competitors()` — Google Places Text Search (primary, works without Geocoding API)
4. `_fetch_nearby_competitors()` — Google Places Nearby Search (used if geocoding works)
5. `_fetch_place_details()` — Fetch full details for each competitor (reviews, hours, phone, website)
6. `_enrich_with_ai()` — Single OpenAI call that generates:
   - Business model, services, threat level, pricing notes per competitor
   - Hours gap analysis (when no competitor is open)
   - SWOT analysis for the owner's business
   - Market opportunity gaps and win strategies

Returns JSON structure:
```json
{
  "report_type": "competitive_benchmarking",
  "analysis_source": "hybrid" | "ai_only" | "fallback",
  "business_keyword": "hair salon",
  "business_location": "College Park, MD",
  "competitors": [...],
  "market_overview": { "total_competitors_found", "market_density", "avg_rating", "avg_price_level", "opportunity_gaps", "win_strategies" },
  "hours_gap_analysis": { "opportunity_windows", "coverage_notes", "recommendation" },
  "swot_analysis": { "strengths", "weaknesses", "opportunities", "threats" },
  "diagnostics": { "keyword", "geocode_status", "text_search_status", "raw_places_count" }
}
```

### `onboarding_interviewer.py`
Runs the AI chat interview. Key behaviours:
- Tracks 6 required topics: business, customer, competitors, budget, cost, goal
- Uses semantic deduplication to avoid repeating similar questions (word-token overlap check)
- `analyze_chat_response()` returns a structured analysis of the conversation which is persisted to `QuestionnaireSession.conversation_analysis_json` after every reply
- Interview ends when all 6 topics are covered OR the owner sends a finish signal

### `positioning_copilot.py`
- Reads the competitive benchmarking report (NOT the old segment analysis format)
- Extracts: business_type, location, competitor data, SWOT, opportunity gaps
- Generates: positioning_statement, tagline, target_segment, key_differentiators, proof_points, rationale
- Refine mode: owner writes free-text feedback → AI re-generates incorporating it
- Saves each version with an incrementing `version` number

### `persona_builder.py`
- Reads: competitive benchmarking report + (optional) latest positioning statement
- Extracts: business_type, location, competitor services, SWOT, customer review snippets, review summaries
- Real Google Places review text is passed verbatim to the AI as "real customer voice" — this produces more grounded personas
- Does NOT require Research report (personas were moved before Research in the workflow)
- Generates 3 distinct personas with different demographics, motivations, and behaviours

### `segment_analyst.py`
- Powers the "Analysis Assistant" chat on the Competitive Benchmarking page
- Renamed from AnalysisCopilot to CompetitiveBenchmarkingCopilot
- Uses memory chunks + analysis report for context-aware answers

### `memory_store.py`
- After each questionnaire response is saved, its text is chunked and embedded using `text-embedding-3-small`
- Embeddings stored in pgvector `memory_chunks` table
- At query time, `retrieve_relevant_memory()` does cosine similarity search (top-k=6)
- Used by the analysis assistant to answer questions with relevant context

---

## 11. API Endpoints Reference

Base URL: `http://localhost:8000/api`

All MVP endpoints require `Authorization: Bearer <token>` header.

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register new user. Body: `{email, password, full_name}` |
| POST | `/auth/login` | Login. Body: `{email, password}`. Returns `{access_token}` |
| GET | `/auth/me` | Get current user info |

### Business Profiles
| Method | Path | Description |
|---|---|---|
| GET | `/business-profiles` | List all profiles for current user |
| POST | `/business-profiles` | Create profile. Body: `{name, description, business_address}` |

### Discovery Interview
| Method | Path | Description |
|---|---|---|
| POST | `/mvp/questionnaire/chat/start` | Start interview. Body: `{business_profile_id}`. Returns session_id + first question |
| GET | `/mvp/questionnaire/chat/{session_id}` | Get all messages so far |
| POST | `/mvp/questionnaire/chat/{session_id}/reply` | Send answer. Body: `{answer_text}`. Returns next question |
| POST | `/mvp/questionnaire/chat/{session_id}/finish` | End interview. Body: `{force: bool}` |

### Workflow Pipeline
| Method | Path | Description |
|---|---|---|
| POST | `/mvp/analysis/run` | Run competitive benchmarking. Body: `{business_profile_id}` |
| POST | `/mvp/analysis/assistant/query` | Chat with analysis assistant. Body: `{business_profile_id, message, history}` |
| POST | `/mvp/positioning/generate` | Generate positioning. Body: `{business_profile_id}` |
| POST | `/mvp/positioning/refine` | Refine with feedback. Body: `{business_profile_id, owner_feedback}` |
| GET | `/mvp/positioning/{project_id}` | List all positioning versions |
| POST | `/mvp/personas/generate` | Generate personas. Body: `{business_profile_id}` |
| POST | `/mvp/research/run` | Generate research. Body: `{business_profile_id}` |
| POST | `/mvp/strategy/generate` | Generate channel strategy. Body: `{business_profile_id}` |
| POST | `/mvp/roadmap/generate` | Generate roadmap. Body: `{business_profile_id}` |
| POST | `/mvp/content/generate` | Generate content asset. Body: `{business_profile_id, asset_type, prompt_text, num_variants}` |

### Session & Workflow Summary
| Method | Path | Description |
|---|---|---|
| GET | `/mvp/questionnaire/sessions/by-business-profile/{id}` | List sessions for a profile |
| GET | `/mvp/workflow/session-summary/{session_id}` | Full snapshot: all artifacts + progress for a session |

---

## 12. Frontend Architecture

### State Management
Everything lives in one React hook: `apps/frontend/src/state/useMvpWorkflow.js`

This was a deliberate architectural choice — the entire application state (auth, projects, sessions, all workflow artifacts) is managed in a single hook exported from this file. No Redux, no Zustand, no Context API.

The hook exposes:
- `state` — all state values
- `set` — direct state setters (e.g. `set.setProjectName`)
- `actions` — async actions that call the API (e.g. `actions.generatePersonas()`)

The `run()` helper wraps every async action with loading state, error toasting, and success state management:
```javascript
const run = async (fn, loadingMsg = "Working...") => {
  setBusy(true);
  setMsg(loadingMsg);
  try { return { ok: true, result: await fn() }; }
  catch (e) { setMsg(e?.response?.data?.detail || e?.message || "Request failed"); return { ok: false }; }
  finally { setBusy(false); }
};
```

### Routing
React Router DOM v7. All routes defined in `App.jsx`. The `progress` object tracks which steps are done (drives nav badges):
```
/projects → /questionnaire → /analysis → /positioning → /personas → /research → /strategy → /roadmap → /content
```

### Toast Notifications
`ToastStack` component with per-toast auto-dismiss using `useEffect`. Each toast has its own 2-second timer tied to its own lifecycle — this avoids a bug where a shared `setTimeout` cleanup would cancel the dismiss if any other state changed.

### 401 Handling
An Axios response interceptor in `api.js` catches 401 responses globally, clears the token from localStorage, and redirects to `/`. This handles expired JWT tokens (24-hour expiry) automatically.

### No Charting Library
The Price vs Rating scatter chart on the Competitive Benchmarking page is built with raw SVG inside React. Decision: keep the bundle lean (no Recharts/Chart.js dependency for a single chart). Uses a deterministic jitter function based on competitor name hash to prevent dot overlap.

### CSS
A single `index.css` file (~2700 lines). All styles are written in plain CSS — no Tailwind, no CSS Modules, no styled-components. CSS variables are used for the brand colour (`--brand: #c72832`), muted text, and border lines.

---

## 13. Authentication System

Custom JWT implementation in `apps/backend/app/core/auth.py` — no PyJWT or python-jose library.

**Password hashing:** PBKDF2-SHA256 with 310,000 rounds + random 16-byte salt. Each password hash is stored as `{salt}:{hash}`.

**JWT structure:**
- Payload: `{sub: user_id, iat: timestamp, exp: timestamp}`
- Encoded as: `base64url(payload).HMAC-SHA256-signature`
- Expiry: 24 hours by default

**Secret key:**
- In development: falls back to `"dev-insecure-secret"` if `JWT_SECRET_KEY` is not set
- In production (`APP_ENV=prod`): raises `RuntimeError` if `JWT_SECRET_KEY` is missing
- All tokens signed and verified with the same secret — if you change the secret, all existing tokens become invalid

**Why custom JWT?** The original developer chose to avoid adding a JWT library dependency and implement the minimal signing logic directly.

---

## 14. Competitive Benchmarking Pipeline

This is the most externally-dependent feature. It uses two Google APIs:

### Google APIs Required
1. **Places API** — for Text Search and Place Details
2. **Geocoding API** — optional, for radius-based Nearby Search

### API Key Setup
1. Go to Google Cloud Console → APIs & Services → Library
2. Enable: **Places API** and **Geocoding API**
3. Create an API key → paste into `apps/backend/.env` as `GOOGLE_PLACES_API_KEY`
4. Enable billing on your Google Cloud project (Places API requires billing)

### Search Strategy (Two-Tier Fallback)
The system tries two approaches in order:

1. **Geocode → Nearby Search** (preferred, radius-controlled):
   - Converts business address to lat/lng using Geocoding API
   - Searches for competitors within `BENCHMARKING_RADIUS_METERS` (default 5km)
   - More accurate — only shows truly local competitors

2. **Text Search** (fallback, used when Geocoding is denied or unavailable):
   - Sends query like "hair salon near College Park, MD" directly to Places Text Search
   - Does not require Geocoding API
   - Slightly less location-precise but works without Geocoding enabled

### Diagnostics
Every response includes a `diagnostics` field showing exactly what happened:
```json
"diagnostics": {
  "keyword": "hair salon",
  "geocode_status": "geocoding_status:REQUEST_DENIED",
  "text_search_status": "OK",
  "raw_places_count": 10
}
```
If you see `competitors: []`, check `diagnostics` first before debugging the code.

### Keyword Inference
The system figures out what kind of business to search for using a 3-priority chain:
1. Read stored `conversation_analysis_json` from the session → small AI call on summary
2. Full transcript AI call (if no stored analysis)
3. Extract from primary-service answer directly (no AI)

This was implemented after a bug where a flower business was incorrectly matched to "spa" because the original approach used a hardcoded keyword map with substring matching ("beautiful" matching "beauty").

---

## 15. Memory System (pgvector)

After each questionnaire response is saved, `memory_store.py` runs automatically:

1. Chunks the response text (if very long)
2. Generates an embedding using `text-embedding-3-small` (1536 dimensions)
3. Checks content hash to avoid storing duplicates
4. Stores in the `memory_chunks` table with `source_type`, `topic_tag`, and `embedding`

At query time (e.g. Analysis Assistant chat), `retrieve_relevant_memory()` does:
1. Embeds the query text
2. Runs cosine similarity search via pgvector: `embedding <=> query_vector`
3. Returns top-k chunks (default k=6)

This gives the AI assistants awareness of what the owner said in their interview, even for follow-up questions asked much later in the workflow.

**pgvector index:** An IVFFlat index is created on the `embedding` column for performance at scale.

---

## 16. Key Decisions and Why

### Decision 1: Single monolithic route file (`mvp_routes.py`)
**What:** All ~70 MVP endpoints live in one ~2000-line file.
**Why:** Speed of development. The project was built iteratively in a single conversation context. Splitting into multiple route files would have added indirection with no immediate benefit. A future developer should consider splitting by domain (questionnaire, analysis, positioning, etc.) once the API stabilises.

### Decision 2: Single state hook (`useMvpWorkflow.js`)
**What:** All frontend state — auth, projects, sessions, every workflow artifact — lives in one React hook.
**Why:** The application has no need for per-component state isolation. Every page needs access to the global workflow state. Using Context API or Redux would add boilerplate with no benefit at this scale. The hook is large (~600 lines) but predictable — every action follows the same `run()` pattern.

### Decision 3: Google Places API over Yelp
**What:** Competitive benchmarking uses Google Places, not Yelp.
**Why:** Google Places has better coverage for small local businesses, official API support, and the owner already had a Google Cloud account. Yelp's API is more restrictive and has lower rate limits. Google Places data quality (ratings, reviews, hours, photos) is more reliable.

### Decision 4: Text Search as primary, Geocode + Nearby Search as enhancement
**What:** The system tries Text Search first (or as fallback), not Geocoding.
**Why:** The Geocoding API requires a separate API enable in Google Cloud Console. Many users would enable Places API but not Geocoding, causing silent failures. After the owner hit `REQUEST_DENIED` on geocoding, the system was redesigned to use Text Search as the primary path since it only needs Places API.

### Decision 5: Conversation analysis persisted to DB after every chat reply
**What:** `QuestionnaireSession.conversation_analysis_json` is updated on every chat reply.
**Why:** Originally, `analyze_chat_response()` ran during the interview but only returned to the frontend — it was never stored. This meant downstream services (like competitive benchmarking keyword inference) had no access to the interview analysis. Adding persistence ensures this rich context is available to all downstream agents.

### Decision 6: Personas moved before Research in the workflow
**What:** Step order changed from [Analysis → Positioning → Research → Personas] to [Analysis → Positioning → Personas → Research].
**Why:** Personas are more fundamental inputs — channel strategy and research are more useful when they know who the personas are. Research was added after personas to validate/deepen the strategy, not before it.

### Decision 7: Persona generation does not require Research report
**What:** `/mvp/personas/generate` was changed to use the analysis report + positioning (not research report) as its inputs.
**Why:** The original code required research to exist before personas could be generated. After personas were moved before research in the workflow, this created a hard 404 blocker. The fix uses competitive benchmarking data + positioning as richer, more specific inputs that are already available at this point.

### Decision 8: Customer review snippets fed into persona generation
**What:** Real Google Places review text is passed verbatim to the persona builder AI.
**Why:** Reviews are written in the customer's own voice — they contain authentic language, real pain points, and genuine motivations. AI-generated personas that incorporate real reviews produce more specific and believable pain points, triggers, and messaging than purely AI-inferred ones.

### Decision 9: Hours gap analysis and SWOT generated in the same AI call as competitor enrichment
**What:** Hours gap analysis and SWOT are added to the `_enrich_with_ai()` prompt in `competitive_benchmarker.py`, not in separate API calls.
**Why:** Each OpenAI call has latency and cost. Since the competitor data is already loaded in memory for the enrichment call, adding two more output sections to the same prompt is essentially free. The total token count increases slightly but latency stays the same.

### Decision 10: Positioning uses competitive benchmarking data (not old segment analysis)
**What:** `positioning_copilot.py` was rewritten to extract fields from the competitive benchmarking JSON structure.
**Why:** The original `positioning_copilot.py` was written for the old segment analysis format (with `segment_attractiveness_analysis`, `recommended_primary_segment` etc.). When the analysis was replaced with competitive benchmarking, the positioning service kept running but was receiving a JSON structure it didn't understand — producing generic, useless output. The rewrite extracts business_type, location, competitor data, and SWOT to produce market-specific positioning.

### Decision 11: No charting library on the frontend
**What:** The Price vs Rating scatter chart is built with raw SVG.
**Why:** Adding Recharts or Chart.js for a single chart is over-engineering. An SVG chart in React is about 80 lines of code and zero additional bundle size. A deterministic jitter function (hash of competitor name) prevents dot overlap without randomness.

### Decision 12: Toast auto-dismiss moved into ToastStack component
**What:** The 2-second auto-dismiss timer lives inside the `Toast` component (per-toast `useEffect`), not in `useMvpWorkflow.js`.
**Why:** The original implementation used a `setTimeout` inside a `useEffect` with `[msg]` dependency. The cleanup function (`return () => clearTimeout(t)`) was called whenever `msg` changed — which happened constantly during normal workflow actions. This cancelled the dismiss timer, leaving toasts permanently on screen. Moving the timer into each `Toast` component's own lifecycle fixes this cleanly.

### Decision 13: Custom JWT instead of a JWT library
**What:** JWT encoding/decoding is implemented manually in `auth.py`.
**Why:** The original developer chose to minimise dependencies. The implementation is correct (HMAC-SHA256, proper expiry, constant-time comparison) but non-standard — it does not produce RFC-compliant JWTs. If you need interoperability with other services, replace with `python-jose` or `PyJWT`.

### Decision 14: Single `config.py` as the settings source of truth
**What:** Both `config.py` (plain class with `os.getenv`) and `settings.py` (Pydantic BaseSettings) exist. Only `config.py` is used for new features.
**Why:** There was a bootstrap conflict where Pydantic's `BaseSettings` tried to read `DATABASE_URL` from `.env` but the format didn't match expected patterns in certain environments. `config.py` was created as a simpler fallback. New env vars should be added to `config.py`. `settings.py` exists only for legacy compatibility and should be removed in a future cleanup.

### Decision 15: `AnalysisCards` replaced with `CompetitorCards` in ProjectPanel
**What:** The Business Profile page session detail view was using `AnalysisCards` (old segment analysis component) to render the competitive benchmarking report.
**Why:** After the analysis format changed from segment analysis to competitive benchmarking, `AnalysisCards` received a JSON structure with none of the expected fields, rendering a blank card. `CompetitorCards` was built specifically for the new format and replaced it.

---

## 17. Known Gotchas and Quirks

### 1. Google Places `REQUEST_DENIED` on first run
If you see `geocode_status: "geocoding_status:REQUEST_DENIED"` in the diagnostics, the Geocoding API is not enabled for your key. The system will automatically fall back to Text Search — you do not need to fix this unless you want radius-based search.

### 2. `alembic upgrade head` must be run after every pull
Migrations are not automatically applied. If you see SQLAlchemy column errors on startup, run `alembic upgrade head`.

### 3. pgvector requires the extension in Postgres
Run `CREATE EXTENSION vector;` in the database before running migrations. If you forget, the `f2b9a8c1d4e7` migration will fail.

### 4. JWT tokens expire after 24 hours
If the frontend shows 401 errors after a day, the token has expired. The Axios interceptor in `api.js` catches 401s, clears localStorage, and redirects to the login page automatically.

### 5. Changing `JWT_SECRET_KEY` invalidates all existing tokens
All logged-in users will be immediately logged out if you rotate the secret.

### 6. `can_use_openai()` returns `False` during pytest
The method checks for `PYTEST_CURRENT_TEST` env var. All AI calls are bypassed in tests, using fallback responses instead. This is intentional to avoid API costs in CI.

### 7. Positioning versions accumulate — no auto-cleanup
Every call to `/mvp/positioning/generate` creates a new row. Old versions are never deleted. The UI shows the latest first, with older versions in a collapsed history. This is by design (audit trail) but the table will grow over time.

### 8. Persona regeneration deletes existing personas for the same session
When `/mvp/personas/generate` is called, existing personas linked to the same `source_session_id` are deleted before new ones are written. This is different from positioning (which accumulates versions).

### 9. `mvp_routes.py` has two settings classes in the codebase
Both `app.core.config.settings` (used by MVP routes and services) and `app.core.settings.settings` (Pydantic-based) exist. Competitive benchmarking and all new services use `config.py`. Do not mix them.

### 10. Frontend `.env` file
`apps/frontend/.env` sets `VITE_API_URL` if you need to change the backend URL. The default in `api.js` is hardcoded to `http://127.0.0.1:8000/api`. Override this for staging/production deployments.

---

## 18. What Is Not Built Yet

The following features were discussed or planned but not yet implemented:

| Feature | Notes |
|---|---|
| Export to PDF | Discussed — would generate a printable version of the full marketing strategy |
| Competitor map view | Google Maps iframe with pins for each competitor — data is available (google_maps_url per competitor) |
| Re-run / Refresh competitive data | A button to re-fetch fresh Google Places data without redoing the full interview |
| Email notifications | No email sending is implemented anywhere |
| Multi-user / Team access | Each project is owned by a single user. No sharing or team roles |
| Payment / Subscription | No billing system. The product is currently free to run |
| Production deployment | No production environment exists. Docker files are present but untested end-to-end |
| Webhook support | No webhooks for async pipeline completion |
| Mobile responsive design | Partially responsive. Not optimised for mobile |
| Dark mode | Not implemented |
| Research page improvements | Research page is functional but visually minimal compared to the redesigned Competitive Benchmarking and Positioning pages |

---

*This document was generated from the live codebase as of March 2026. If you are reading this significantly later, verify the code against this document — the codebase evolves faster than documentation.*
