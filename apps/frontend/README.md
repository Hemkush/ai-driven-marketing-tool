# MarketPilot AI — Frontend

React 19 SPA for the MarketPilot AI platform, built with Vite and deployed to Firebase Hosting.

## Quick Start (Local)

```bash
cd apps/frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

## Environment Variables

Create `apps/frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

For production, `apps/frontend/.env.production`:

```env
VITE_API_URL=https://your-backend-cloud-run-url
```

## Deploy to Firebase Hosting

```bash
cd C:\Users\kushw\Downloads\CodingProjects\ai-driven-marketing-tool\apps\frontend && npm run build && firebase deploy --only hosting
```

## Pages

| Page | Route | Description |
|---|---|---|
| Landing | `/` | Marketing homepage |
| Login / Register | `/login` | Auth panel — creates account and logs in immediately |
| Questionnaire | `/questionnaire` | Adaptive AI interview |
| Analysis | `/analysis` | Competitive benchmarking + market analysis + Q&A copilot |
| Positioning | `/positioning` | Brand positioning statement |
| Personas | `/personas` | Buyer persona profiles |
| Research | `/research` | Market research insights |
| Strategy | `/strategy` | Channel strategy + 90-day roadmap |
| Content | `/content` | Text + image content generation |
| Verify Email | `/verify-email` | Email verification (currently unused) |

## State Management

All workflow state lives in `src/state/useMvpWorkflow.js` — a single custom hook passed as `workflow` prop through the app. No Redux or external state library.

Key state slices:
- `auth` — JWT token, current user, login/register actions
- `projects` — list of business profiles, active project selection
- `session` — questionnaire session ID and chat messages
- `pipeline` — analysis, positioning, personas, strategy, research, roadmap reports

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| React | 19.2.0 | UI framework |
| React Router | 7.13.1 | Client-side routing with auth-gated routes |
| Vite | 7.3.1 | Build tool with HMR |
| TailwindCSS | latest | Utility-first styling |
| Axios | 1.13.6 | HTTP client with auth interceptors |
| Firebase Hosting | — | CDN-backed static hosting |

## Auth Flow

Registration creates the account and logs in immediately — no email verification step. The register API returns a JWT token directly, which is stored in `localStorage` via `setAuthToken`.

## Notes

- Protected routes redirect to `/login` if no valid token is present.
- All API calls go through `src/lib/api.js` which automatically attaches the Bearer token and handles 401 redirects.
- The `CompactCards.jsx` component renders pipeline output cards shared across multiple pages.
