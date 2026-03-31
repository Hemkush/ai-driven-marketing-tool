# Deployment Guide
## Stack: Firebase Hosting (frontend) + Cloud Run (backend) + Supabase (database)

---

## Prerequisites — Install these once

```bash
# 1. Google Cloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Firebase CLI
npm install -g firebase-tools

# 3. Verify installs
gcloud --version
firebase --version
```

---

## Part 1 — Supabase Database (5 min)

1. Go to https://supabase.com → **New project**
2. Choose a name, region closest to your users, strong password
3. Wait ~2 min for provisioning

**Enable pgvector:**
4. Go to **SQL Editor** → run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

**Get your connection string:**
5. Go to **Project Settings → Database → Connection String**
6. Select **URI** tab → copy the string
7. It looks like:
   ```
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
   ```
8. Add `?sslmode=require` at the end and change `postgresql://` to `postgresql+psycopg://`

Final format:
```
postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
```

---

## Part 2 — Google Cloud Project (5 min)

```bash
# Login
gcloud auth login

# Create a new project (or use existing)
gcloud projects create your-project-id --name="AI Marketing Tool"

# Set it as default
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com
```

---

## Part 3 — Deploy the Backend to Cloud Run (10 min)

### 3a. Generate strong secrets
```bash
# Run these and save the output — you'll need them below
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('INTERNAL_API_KEY=' + secrets.token_hex(24))"
```

### 3b. Build and push the Docker image
```bash
cd apps/backend

# Build the image
gcloud builds submit --tag gcr.io/your-project-id/ai-marketing-backend
```

### 3c. Deploy to Cloud Run
```bash
gcloud run deploy ai-marketing-backend \
  --image gcr.io/your-project-id/ai-marketing-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120 \
  --set-env-vars "DATABASE_URL=postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" \
  --set-env-vars "JWT_SECRET_KEY=YOUR_GENERATED_JWT_SECRET" \
  --set-env-vars "INTERNAL_API_KEY=YOUR_GENERATED_INTERNAL_KEY" \
  --set-env-vars "OPENAI_API_KEY=sk-..." \
  --set-env-vars "OPENAI_MODEL=gpt-4o-mini" \
  --set-env-vars "OPENAI_BASE_URL=https://api.openai.com/v1" \
  --set-env-vars "GOOGLE_PLACES_API_KEY=AIza..." \
  --set-env-vars "APP_ENV=production" \
  --set-env-vars "CORS_ORIGINS=https://your-project-id.web.app"
```

> After deploy, Cloud Run shows the backend URL. It looks like:
> `https://ai-marketing-backend-xxxxxxxxxx-uc.a.run.app`
> **Save this URL — you need it for the next step.**

### 3d. Run database migrations
```bash
# Set the DATABASE_URL locally and run migrations against Supabase
cd apps/backend
DATABASE_URL="postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" \
  alembic upgrade head
```

---

## Part 4 — Deploy the Frontend to Firebase Hosting (5 min)

### 4a. Set the backend URL
Edit `apps/frontend/.env.production`:
```
VITE_API_BASE_URL=https://ai-marketing-backend-xxxxxxxxxx-uc.a.run.app/api
```

### 4b. Build the frontend
```bash
cd apps/frontend
npm install
npm run build
# This creates apps/frontend/dist/
```

### 4c. Set up Firebase project
```bash
# From the project root
firebase login
firebase use --add
# Select your Google Cloud project → alias: default
```

Update `.firebaserc` with your real Firebase project ID.

### 4d. Deploy
```bash
# From the project root
firebase deploy --only hosting
```

> Firebase will print your live URL:
> `https://your-project-id.web.app`

### 4e. Update CORS on the backend
```bash
gcloud run services update ai-marketing-backend \
  --region us-central1 \
  --update-env-vars "CORS_ORIGINS=https://your-project-id.web.app,https://your-custom-domain.com"
```

---

## Part 5 — Verify Everything Works

```bash
# 1. Check backend health
curl https://ai-marketing-backend-xxxxxxxxxx-uc.a.run.app/health
# Expected: {"status": "ok"}

# 2. Open frontend in browser
open https://your-project-id.web.app
# Try registering and logging in
```

---

## Updating the App (Future Deploys)

### Redeploy backend after code changes:
```bash
cd apps/backend
gcloud builds submit --tag gcr.io/your-project-id/ai-marketing-backend
gcloud run deploy ai-marketing-backend \
  --image gcr.io/your-project-id/ai-marketing-backend \
  --region us-central1
```

### Redeploy frontend after code changes:
```bash
cd apps/frontend
npm run build
cd ../..
firebase deploy --only hosting
```

---

## Cost Estimate (10 users)

| Service | Free Tier | Expected Cost |
|---|---|---|
| Cloud Run | 2M requests/mo free | **$0** |
| Firebase Hosting | 10GB/mo free | **$0** |
| Supabase | 500MB DB, 2GB bandwidth | **$0** |
| **Total** | | **$0/mo** |

Cloud Run charges only activate if you exceed 2M requests/month (extremely unlikely for 10 users).

---

## Troubleshooting

**Backend cold start is slow (first request takes ~5s):**
- Expected behaviour — Cloud Run scales to zero when idle
- Set `--min-instances 1` to keep it warm (~$5/mo)

**CORS error in browser:**
- Make sure `CORS_ORIGINS` env var on Cloud Run includes your Firebase URL exactly
- No trailing slash in the URL

**Database connection refused:**
- Supabase requires `?sslmode=require` in the connection string
- Check the Supabase dashboard → Project Settings → Database is not paused

**Alembic migration fails:**
- Make sure pgvector extension is enabled in Supabase SQL Editor first
- Run `CREATE EXTENSION IF NOT EXISTS vector;` before migrations
