# 90-Day Roadmap Page

**File:** `apps/frontend/src/pages/RoadmapPage.jsx`
**Route:** `/roadmap`
**Pipeline step:** 7 of 8
**Access:** Authenticated users only

---

## Purpose

This page generates a concrete, week-by-week 90-day marketing execution plan for the business. Rather than generic marketing advice, the roadmap is built from the specific outputs already gathered in the pipeline — the competitive gaps, positioning, personas, and market research — and translates them into prioritised, actionable tasks with specific channels, timing, and expected outcomes.

The roadmap is organised into three phases (roughly corresponding to months 1, 2, and 3), ordered by impact so the highest-leverage actions come first.

---

## What the User Sees

### Gate / Empty State (No Roadmap Yet)
When no roadmap has been generated:
- A blurred ghost preview (`GhostPreviewRoadmap`) is visible behind the gate card
- The gate card shows:
  - **Step 1: Buyer Personas** — checkmark if `state.personas.length > 0`
  - **Step 2: Generate 90-Day Roadmap** — description with approximate time (~25 seconds)
  - "Generate Roadmap →" button

### Prefetch Loading State
If background prefetch is running (`state.prefetch.roadmap && !hasRoadmap`), the entire page is replaced with: "Preparing your 90-day roadmap in the background…"

### Main Layout (After Generation)
Once a roadmap exists:
- `AiChip` and `TrustBadge` (quality score)
- `ExportBar` aligned to the right
- `RoadmapCards` — the main output component
- `WhyThis` — AI reasoning section
- `FeedbackThumbs` — thumbs up/down rating

### Regenerate
In the main layout header, a "Regenerate Roadmap" button allows re-running the roadmap agent to get a refreshed plan.

### Gate Error Banner
Orange warning banner if backend validation fails, with "Back to Questionnaire →" link.

---

## Export Bar (`ExportBar` component)

Defined inside `RoadmapPage.jsx`. Provides:
- **Copy button** — converts the roadmap to plain text (phases → weeks → actions) and copies to clipboard via `navigator.clipboard.writeText()`. Shows "Copied!" for 2 seconds.
- **Print / PDF button** — calls `window.print()` to open the browser print dialog

### roadmapToText Helper

```javascript
function roadmapToText(roadmap) {
  if (!roadmap?.phases) return "";
  return roadmap.phases.map((phase) => {
    const weeks = (phase.weeks || [])
      .map((w) => `  Week ${w.week}: ${w.action}`)
      .join("\n");
    return `${phase.phase}\n${weeks}`;
  }).join("\n\n");
}
```

Example output:
```
Phase 1: Quick Wins (Weeks 1-4)
  Week 1: Set up Google Business Profile and request reviews
  Week 2: Launch Instagram with 3× weekly posts
  ...

Phase 2: Build Momentum (Weeks 5-8)
  Week 5: Partner with UMD Events
  ...
```

---

## Logic Flow

```
User arrives at /roadmap
  → if prefetch.roadmap && !hasRoadmap: show full-page skeleton
  → if !busy && !hasRoadmap: show gate

User clicks "Generate Roadmap →"
  → actions.generateRoadmap()
      → POST /api/mvp/roadmap/generate
      → sends personas, research, positioning, analysis as context
      → state.roadmap populated on completion

User clicks "Regenerate Roadmap"
  → same action — replaces existing roadmap

User clicks "Copy" in ExportBar
  → roadmapToText(roadmap)
  → navigator.clipboard.writeText(text)

User clicks "Print / PDF"
  → window.print()

User clicks "Next: Content Studio →"
  → navigate to /content
  → disabled until hasRoadmap is true
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.roadmap` | The roadmap object (contains `phases` array) |
| `state.personas` | `personas.length > 0` determines Step 1 checkmark in gate |
| `state.prefetch.roadmap` | If true + no roadmap → full-page loading skeleton |
| `state.gateError` | Backend validation error (shown if `agent === "roadmap_planner"`) |
| `state.busy` | Disables buttons during generation |
| `state.activeProjectId` | Required for the API call |

---

## What Makes a Good Roadmap Output

The backend roadmap agent uses all previous pipeline outputs to produce the plan:
- **Competitor analysis** → identifies quick wins (e.g., "no competitor offers online booking → add it in week 1")
- **Positioning** → shapes messaging for each channel
- **Personas** → matches channels to where each customer segment actually spends time
- **Market research** → prioritises actions based on buying journey stages

The output is ordered by impact, meaning the highest-leverage, easiest-to-execute actions come in Phase 1 (month 1). Longer-term compounding activities (e.g., SEO, referral programmes) appear in Phase 3.

---

## Relationship to Other Steps

The roadmap is the strategic synthesis of everything gathered so far. It's the most actionable output in the pipeline — the user can start executing it the same day without needing to do any further analysis.

The Content Studio (next step) uses the roadmap to make content assets relevant to the execution plan. For example, if week 3 of the roadmap says "launch Instagram," the Content Studio can generate exactly the Instagram captions needed for that week.

---

## Next Step

"Next: Content Studio →" navigates to `/content`. The button is **disabled** until `hasRoadmap` is true.
