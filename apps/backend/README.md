## Backend Setup

1. Create and activate virtual environment
```powershell
cd apps/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies
```powershell
pip install -r requirements.txt
```

3. Run database migrations
```powershell
alembic upgrade head
```

4. Start API server
```powershell
uvicorn app.main:app --reload
```

## Run Tests (Use Project venv)

Always run tests with the backend virtual environment Python:

```powershell
cd apps/backend
.venv\Scripts\python -m pytest -q
```

Run onboarding/chatbot tests only:

```powershell
.venv\Scripts\python -m pytest tests/test_mvp_onboarding.py -q
```

## Required Environment Variables

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `INTERNAL_API_KEY`
- `OPENAI_API_KEY` (optional for fallback mode)
- `OPENAI_MODEL` (optional)
- `OPENAI_BASE_URL` (optional)
- `OPENAI_EMBEDDING_MODEL` (optional, default `text-embedding-3-small`)
- `MEMORY_TOP_K` (optional, default `6`)
- `CORS_ORIGINS` (comma-separated origins, example: `http://localhost:5173,http://localhost:5174`)

Recommended defaults:

- `OPENAI_MODEL=gpt-4o-mini`
- `OPENAI_BASE_URL=https://us.api.openai.com/v1`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `MEMORY_TOP_K=6`

## Notes

- Runtime schema auto-creation is disabled. Always run Alembic migrations before starting the app.
- CORS now uses `CORS_ORIGINS` from environment configuration.
- If tests fail with `ModuleNotFoundError` (for example `sqlalchemy`), you are likely using global Python instead of `.venv\Scripts\python`.

## Chatbot Workflow (Current)

1. Create/select a Business Profile in UI.
2. Click `Start Interview` in Questionnaire page.
3. Answer each bot question.
4. Live Marketing Analysis updates after each answer.
5. Click `Finish Interview`.
6. Go to Analysis page and run full analysis.

UI behavior:

- `Restart Interview` creates a fresh chat session after confirmation.
- Live analysis shows:
  - `Source: ai` when OpenAI output is used
  - `Source: fallback` when deterministic fallback logic is used

## Troubleshooting

If important points are not AI-generated:

1. Verify `OPENAI_API_KEY` in `apps/backend/.env`.
2. Restart backend after `.env` changes:
```powershell
uvicorn app.main:app --reload
```
3. Check analysis payload:
   - `analysis_source`
   - `fallback_reason` (if present)
