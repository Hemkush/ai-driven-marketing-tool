# MarketPilot — Frontend Pages Overview

## What is MarketPilot?

MarketPilot is an AI-powered marketing strategy tool for small businesses, marketing agencies, and business consultants. It guides users through a structured 8-step pipeline that transforms basic business information into a complete, data-driven marketing strategy — including competitor analysis, buyer personas, market research, a 90-day execution roadmap, and ready-to-use content assets.

---

## How the Application Works (High-Level)

```
Landing Page (unauthenticated)
        ↓  Sign Up / Login
1. Business Profile (/projects)       — create or select a business workspace
        ↓
2. Marketing Discovery (/questionnaire) — AI interview captures business context
        ↓
3. Competitive Benchmarking (/analysis) — live Google Places competitor scan
        ↓
4. Positioning (/positioning)         — AI-generated market positioning statement
        ↓
5. Buyer Personas (/personas)         — detailed customer segment profiles
        ↓
6. Market Research (/research)        — deep evidence-backed market insights
        ↓
7. 90-Day Roadmap (/roadmap)          — week-by-week execution plan
        ↓
8. Content Studio (/content)          — on-brand content assets for every channel
```

Each step feeds into the next. The output of earlier steps is used as input context for later AI agents (e.g., personas inform the roadmap; positioning informs content).

---

## Technical Architecture

### State Management
All application state lives in a single custom hook: `src/state/useMvpWorkflow.js`. This hook is instantiated once in `App.jsx` and passed to every page and component as a `workflow` prop with three sub-objects:

| Property | Contains |
|---|---|
| `workflow.state` | All reactive state values (current project, interview data, AI outputs, loading flags, etc.) |
| `workflow.set` | Setter functions for user-controlled fields (e.g., `set.setProjectName`) |
| `workflow.actions` | Async API actions (e.g., `actions.runAnalysis()`, `actions.generatePersonas()`) |

### Routing
React Router v6. Routes are defined in `App.jsx`. All pipeline routes (`/projects` through `/content`) are protected — unauthenticated users are redirected to the landing page.

### API Layer
`src/lib/mvpClient.js` contains typed wrappers for all backend endpoints, using an Axios instance defined in `src/lib/api.js` that automatically injects the JWT Bearer token on every request.

### Progress Tracking
`App.jsx` computes a `progress` object (one boolean per route) and passes it to `AppShell`, which renders it as a sidebar step indicator with checkmarks.

### AI Output Trust System
Every AI-generated output page includes three shared trust components:
- **`AiChip`** — identifies content as AI-generated
- **`TrustBadge`** — displays the backend quality score (0–1) as a color-coded badge
- **`FeedbackThumbs`** — thumbs up/down for the user to rate the output quality
- **`WhyThis`** — expands to show the AI's reasoning for the output

---

## Page Index

| # | Route | File | Purpose |
|---|---|---|---|
| — | `/` | `LandingPage.jsx` | Public marketing + auth entry |
| 1 | `/projects` | `ProjectsPage.jsx` | Create/manage business workspaces |
| 2 | `/questionnaire` | `QuestionnairePage.jsx` | AI-powered discovery interview |
| 3 | `/analysis` | `AnalysisPage.jsx` | Competitive benchmarking report |
| 4 | `/positioning` | `PositioningPage.jsx` | Market positioning statement |
| 5 | `/personas` | `PersonasPage.jsx` | Buyer persona generation |
| 6 | `/research` | `ResearchPage.jsx` | Deep market research |
| 7 | `/roadmap` | `RoadmapPage.jsx` | 90-day execution roadmap |
| 8 | `/content` | `ContentPage.jsx` | Content asset generation |

---

## Shared Layout — AppShell

Every authenticated page is wrapped in `AppShell`, which provides:
- **Sidebar** with nav links, progress checkmarks per step, project name, and a ⌘K keyboard shortcut hint
- **Usage stats widget** pinned to the bottom of the sidebar showing step progress (e.g., "3 / 8")
- **Page transition animations** — `key={location.pathname}` on the content div triggers a CSS `page-enter` animation on every route change

---

## Key Design Patterns

### Gate / Empty States
Pages that require prior steps show a "gate" UI instead of the main content. The gate explains what is needed, shows which prerequisites are complete (with checkmarks), and provides a direct action button.

### Background Prefetch
After completing the questionnaire, the app prefetches positioning, personas, and roadmap in the background. If the user navigates to one of these pages before the prefetch finishes, a loading skeleton is shown. This eliminates perceived wait time.

### Streaming Progress
For long-running AI operations (competitive analysis, content generation), the backend streams step-by-step progress events via SSE (Server-Sent Events). The frontend renders these as a live pipeline log with spinners and checkmarks.

### Ghost Previews
Pages that haven't been run yet show a blurred, low-opacity preview of what the output will look like, created by `GhostPreview.jsx` components. This gives users a sense of what they're working toward before generating.
