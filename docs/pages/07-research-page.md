# Market Research Page

**File:** `apps/frontend/src/pages/ResearchPage.jsx`
**Route:** `/research`
**Pipeline step:** 6 of 8
**Access:** Authenticated users only

---

## Purpose

This page runs deep AI market research specifically for the user's business. Unlike the competitor benchmarking step (which scans live Google data), the market research step synthesises evidence-backed insights from the business context already gathered — competitor data, questionnaire answers, buyer personas, and positioning — to produce:

- Customer insights and buying behaviour patterns
- Per-persona buying journeys (how each persona discovers, considers, and buys)
- Quick wins (low-effort, high-impact marketing actions)
- Untapped market opportunities
- Channel-specific recommendations

The research is grounded in the specific business type, location, and audience — not generic marketing advice.

---

## What the User Sees

### Gate / Empty State (No Research Yet)
When no research has been run:
- A blurred ghost preview is shown behind the gate card, giving a visual preview of what the output will look like
- The gate card shows:
  - **Step 1: Buyer Personas** — marked with a checkmark if `state.personas.length > 0`, otherwise shows "Generate personas from the Personas page first"
  - **Step 2: Run Deep Research** — description of what the AI will produce and approximate time (~30 seconds)
  - "Run Research →" button

### Prefetch Loading State
If background prefetch is in progress (`state.prefetch.research && !hasResearch`), the entire page is replaced with a loading skeleton: "Preparing your market research in the background…"

### Focus Input (`FocusInput` component)
Once research exists (or before it's been run for the first time in the main layout), a "Focus This Research" control appears:
- An optional text input: "e.g. Instagram marketing, weekend customers…"
- Lets the user direct the AI toward a specific angle (e.g., "premium segment", "competitor X's weaknesses", "Instagram marketing")
- Leaving it blank runs a broad overview
- Button label adapts:
  - No research + no focus: "Run Research →"
  - No research + has focus: "Run with Focus →"
  - Has research + no focus: "Re-run Research →"
  - Has research + has focus: "Re-run with Focus →"
- Pressing Enter in the input triggers the run

### Loading State
`LoadingSkeleton` with message "Running deep market research…" while the request is in flight.

### Research Results
Once complete:
- `AiChip` and `TrustBadge` (quality score)
- `ResearchCards` — renders the structured research output (insights, buying journeys per persona, quick wins, opportunities)
- `WhyThis` — AI reasoning section
- `FeedbackThumbs` — thumbs up/down rating

### Gate Error Banner
If the backend validation fails (e.g., no personas generated yet), an orange warning banner appears with the error and a "Back to Questionnaire →" link.

---

## Logic Flow

```
User arrives at /research
  → if prefetch.research && !hasResearch: show full-page skeleton

  → if !busy && !hasResearch: show gate + focus input

User clicks "Run Research →" (from gate or focus area)
  → actions.runResearch()
      → POST /api/mvp/research/run  (sends researchFocus if set)
      → state.research populated on completion

User types a focus and clicks "Run with Focus →"
  → same as above, but the focus string is sent as additional context

User clicks "Re-run Research →" (to refresh with new focus)
  → same flow — previous research is replaced

User clicks "Next: Roadmap →"
  → navigate to /roadmap
  → disabled until hasResearch is true
```

---

## FocusInput Component

Defined inside `ResearchPage.jsx`. A self-contained card with:
- A badge "Optional"
- A dynamic label: "Focus this research" (before first run) or "Refocus the research" (after)
- A hint explaining what kinds of focus inputs work well
- The text input and action button

```jsx
function FocusInput({ value, onChange, onRun, busy, hasResearch }) {
  // renders the rsp-focus-card
}
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.research` | The research output object |
| `state.researchFocus` | Bound to the focus text input (`set.setResearchFocus`) |
| `state.personas` | `personas.length > 0` determines the Step 1 checkmark in the gate |
| `state.prefetch.research` | If true + no research → full-page loading skeleton |
| `state.gateError` | Backend validation error (shown if `agent === "market_researcher"`) |
| `state.busy` | Disables buttons during the research run |
| `state.activeProjectId` | Required for the API call |

---

## How the Research Differs from Competitor Analysis

| Aspect | Competitor Analysis (`/analysis`) | Market Research (`/research`) |
|---|---|---|
| Data source | Live Google Places API | Synthesised from gathered context |
| Focus | Who are the competitors? | How do customers behave? |
| Output | Competitor profiles, SWOT, gaps | Buying journeys, quick wins, opportunities |
| Timing | After interview | After personas |
| Can be refocused | No (re-run re-scans Google) | Yes (focus input directs AI) |

---

## Why This Step Comes After Personas

The market research uses the buyer personas to personalise the output. For each persona, the research produces a specific buying journey (how that type of customer discovers, evaluates, and purchases from businesses like yours). Without personas, the buying journeys would be generic. With them, they're specific enough to drive concrete marketing decisions.

---

## Next Step

"Next: Roadmap →" navigates to `/roadmap`. The button is **disabled** until `hasResearch` is true.
