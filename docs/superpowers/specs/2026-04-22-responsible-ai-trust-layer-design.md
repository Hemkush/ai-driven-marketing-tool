# Responsible AI Trust Layer — Design Spec
**Date:** 2026-04-22
**Approach:** Explain & Gate (Approach B)
**Primary audience:** Small business owners using the platform
**Core problem:** The platform doesn't feel credible enough for users to trust and act on AI advice

---

## Expert Panel Summary

Panel: Dr. Maya Chen (AI Ethics), Sam Okafor (UX Trust), Priya Patel (Privacy), Marcus Webb (Marketing strategy)

**Refined consensus — four root causes of the credibility gap:**

| Priority | Root Cause | Symptom |
|---|---|---|
| 1 | No confidence signals | Every output looks equally authoritative |
| 2 | No source attribution | Can't see what drove the AI's conclusions |
| 3 | No quality gate | Low-quality outputs reach users silently |
| 4 | No data privacy notice | Latent anxiety about business data |

---

## Architecture

```
Existing flow:
  Agent → LLM → quality_scorer (silent) → DB → API response → UI card

New flow:
  Agent → LLM (with reasoning prompt) → quality_scorer → GATE → DB → API response
                                                              ↓ (if score < 0.65)
                                                         422 "incomplete_profile"
                                                              ↓
                                                         UI prompts user to add details
```

**What doesn't change:** DB schema (except additions below), auth, caching, rate limiting, pipeline tracing, observability stack.

---

## Backend

### 1. Reasoning prompt patch — all 8 agents

Every agent prompt gains one instruction and one field in its JSON schema:

**Prompt addition (identical across all agents):**
```
Also include a "reasoning" field (2–3 sentences) explaining which of the user's
specific inputs drove the key conclusions. Reference actual details — never be generic.
```

**JSON schema addition:**
```json
{
  "...existing fields...": "...",
  "reasoning": "Based on your focus on eco-friendly products, Austin location, and $80 avg order value, we identified the weekend-wellness segment as the strongest fit because..."
}
```

`reasoning` is stored in the existing JSON columns (`plan_json`, `content_json`, etc.) — no extra storage column needed.

Files to update: `services/segment_analyst.py`, `services/positioning_copilot.py`, `services/persona_builder.py`, `services/market_researcher.py`, `services/roadmap_planner.py`, `services/content_studio.py`

Each agent's fallback dict (used during tests when `can_use_openai()` is False) must also include a hardcoded `reasoning` string.

---

### 2. Quality gate — `api/mvp/deps.py`

New shared helper:

```python
def _quality_gate(score: float, agent: str) -> None:
    if score < 0.65:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "incomplete_profile",
                "agent": agent,
                "score": round(score, 2),
                "message": (
                    "Your business profile needs more detail to generate reliable output. "
                    "Go back to the questionnaire and answer any skipped questions."
                ),
            },
        )
```

Every agent route already calls `score_*(output)`. After that call, add:
```python
_quality_gate(score, agent="<agent_name>")
```
Then store `score` alongside the output row.

Route files to update: `api/mvp/analysis.py`, `api/mvp/positioning.py`, `api/mvp/personas.py`, `api/mvp/research.py`, `api/mvp/roadmap.py`, `api/mvp/content.py`

---

### 3. Feedback endpoint — new route

**`POST /api/mvp/feedback`**

```python
class FeedbackRequest(BaseModel):
    project_id: int
    agent: str          # e.g. "persona_builder"
    quality_score: float | None
    polarity: int       # +1 (thumbs up) or -1 (thumbs down)
```

Writes one row to `output_feedback`. Returns `204 No Content`. No auth required beyond the existing Bearer token.

---

## Database

### Alembic migration — one file

```sql
-- quality_score on all output tables (actual table names from models.py)
ALTER TABLE analysis_reports        ADD COLUMN quality_score FLOAT;
ALTER TABLE positioning_statements  ADD COLUMN quality_score FLOAT;
ALTER TABLE persona_profiles        ADD COLUMN quality_score FLOAT;
ALTER TABLE research_reports        ADD COLUMN quality_score FLOAT;
ALTER TABLE roadmap_plans           ADD COLUMN quality_score FLOAT;
ALTER TABLE media_assets            ADD COLUMN quality_score FLOAT;

-- consent flag on projects (default true = notice-and-continue)
ALTER TABLE projects ADD COLUMN consent_given BOOLEAN DEFAULT TRUE;

-- feedback signals
CREATE TABLE output_feedback (
    id            SERIAL PRIMARY KEY,
    project_id    INTEGER REFERENCES projects(id),
    agent         VARCHAR(50) NOT NULL,
    quality_score FLOAT,
    polarity      SMALLINT NOT NULL,   -- +1 or -1
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

SQLAlchemy model additions: `quality_score` column on `AnalysisReport`, `PositioningStatement`, `PersonaProfile`, `ResearchReport`, `RoadmapPlan`, `MediaAsset`; `consent_given` on `Project`; new `OutputFeedback` model.

---

## Frontend

### New components

**`TrustBadge`** (`src/components/TrustBadge.jsx`)

Reads `quality_score` prop. Renders inline chip:
- `score ≥ 0.85` → `● High confidence` (green)
- `score 0.65–0.84` → `◑ Good confidence` (amber)
- `score` absent / null → renders nothing

Placed in the header row of every generated output card.

---

**`WhyThis`** (`src/components/WhyThis.jsx`)

Reads `reasoning` string prop. Renders a collapsible below the card body:
- Collapsed by default, single chevron toggle
- No modal, no new route — inline expansion only
- If `reasoning` is absent, renders nothing

---

**`AiChip`** (`src/components/AiChip.jsx`)

Small pill label: `AI-generated`. Placed on the same line as the card title on every generated output card. Subtle, always visible, not a warning.

---

### Pages updated

Add `<TrustBadge>`, `<WhyThis>`, `<AiChip>`, and feedback thumbs to:
- `pages/AnalysisPage.jsx`
- `pages/PositioningPage.jsx`
- `pages/PersonasPage.jsx`
- `pages/ResearchPage.jsx`
- `pages/RoadmapPage.jsx`
- `pages/ContentPage.jsx`

Feedback thumb calls `POST /api/mvp/feedback` via `mvpClient.js`. On success: brief "Thanks" toast via existing `ToastStack`. Fire-and-forget — no blocking UI.

---

### Quality gate error handling

In `useMvpWorkflow.js`, catch `422` responses with `code === "incomplete_profile"`:

```js
// Set on state:
{ gateError: { agent, message } }
```

Each page renders inline (not modal):
```
⚠ We need more detail to generate reliable output.
  Go back to the questionnaire and answer any skipped questions.
  [Back to Questionnaire →]
```

Generate button re-enables after the user navigates back to the questionnaire and saves new answers (existing `state.activeProjectId` trigger already handles re-enabling).

---

### Privacy notice

In `QuestionnaireChatPanel.jsx` (or `QuestionnairePanel.jsx`), render once above the first question if `project.consent_given` is not yet set:

> *Your answers are used only to generate your marketing plan. We don't use your data to train AI models or share it with third parties.*

Notice-and-continue pattern — no checkbox required. `consent_given` is set to `true` on project creation (default), so this is a display-only notice, not a gate.

---

## Testing

**Two new test cases** in existing test files:

1. **Quality gate** (`tests/test_mvp_*.py`)
   - Stub `score_*(output)` to return `0.4`
   - Assert route returns `422` with `code == "incomplete_profile"`

2. **Reasoning field** (one assertion per agent test)
   - Assert fallback output dict includes `"reasoning"` key with non-empty string
   - Ensures the frontend never receives a card with a missing `WhyThis` field in production

No new test infrastructure needed — fits existing `pytest -q` pattern with `PYTEST_CURRENT_TEST` env var.

---

## Scope Summary

| Area | Files | Effort |
|---|---|---|
| Reasoning prompts + fallbacks | 6 `services/*.py` | Medium |
| Quality gate helper | `deps.py` + 6 route files | Small |
| Feedback endpoint + model | `api/mvp/` new route + `models.py` | Small |
| DB migration | 1 Alembic file | Small |
| Trust UI components | 3 new `.jsx` files | Small |
| Page integration | 6 page files | Medium |
| Quality gate UX + workflow | `useMvpWorkflow.js` + 6 pages | Small |
| Privacy notice | 1 component | Tiny |
| Tests | 2 new test cases + fallback dict patches | Small |

**Not in scope:** Data deletion endpoint, explicit consent checkbox, GDPR compliance docs, bias auditing — deferred until enterprise need arises.
