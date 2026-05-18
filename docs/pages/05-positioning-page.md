# Positioning Page

**File:** `apps/frontend/src/pages/PositioningPage.jsx`
**Route:** `/positioning`
**Pipeline step:** 4 of 8
**Access:** Authenticated users only

---

## Purpose

This page generates and refines the business's **positioning statement** — a concise description of the unique market position the business owns in its customers' minds. A positioning statement answers:
- Who is the target customer?
- What does the business offer?
- How is it different from competitors?
- What is the single most compelling reason to choose this business?

The output is versioned — each time the user generates or refines, a new version is stored and the previous ones are kept in an expandable history.

---

## What the User Sees

### Page Header
- Title: "Positioning Statement"
- Description explaining the purpose of positioning
- "Generate Positioning" button (becomes "Regenerate Positioning" after first generation)

### Empty / No History State
When no positioning statement has been generated yet:
- A blurred ghost preview (`GhostPreviewPositioning`) is shown behind a placeholder message: "Generate your positioning statement to see your unique market position."
- This gives the user a visual sense of what the output will look like before they generate

### Loading State
- A `LoadingSkeleton` with the message "Generating your positioning statement…" appears while the request is in flight
- A separate skeleton with "Preparing your positioning statement…" appears during background prefetch (when the app is prefetching in the background after questionnaire completion)

### Latest Version Display
The most recent version is prominently displayed:
- A "Latest · Version N" badge with a live indicator dot, the version date, `AiChip`, and `TrustBadge`
- `PositioningCard` component renders the full positioning content (tagline, statement, differentiators, target segment)
- `WhyThis` — expandable AI reasoning section
- `FeedbackThumbs` — thumbs up/down

### Refine with Feedback
Below the latest version, a feedback form allows the user to refine the positioning:
- Textarea with placeholder examples: "Focus more on weekend clients", "Emphasise our natural hair specialisation", "The tone is too formal, make it friendlier"
- "Refine Positioning →" button (ghost style) — disabled until the textarea has content
- Submitting this creates a **new version** rather than overwriting the old one

### Version History Accordion
If there are older versions:
- A "Previous Versions" heading with a count badge
- Each old version is a collapsible `<details>` element showing: version number, creation date, and the tagline as a preview in the summary row
- Expanding reveals the full `PositioningCard` for that version

### Gate Error Banner
If the backend validation fails (missing questionnaire answers, etc.), an orange warning banner appears with the error message and a "Back to Questionnaire →" link.

---

## Versioning Logic

```javascript
const hasHistory = state.positioningHistory?.length > 0;
const latest = state.positioningHistory?.[0];          // most recent
const olderVersions = state.positioningHistory?.slice(1); // all others
```

The backend stores each generated version as a separate row. The frontend loads them newest-first. The latest version gets full display treatment; older versions are collapsed into the history accordion.

---

## Logic Flow

```
Page loads
  → if activeProjectId: actions.loadPositioningHistory(selectedProjectSessionId)
      → GET /api/mvp/positioning/history
      → populates state.positioningHistory

User clicks "Generate Positioning"
  → actions.generatePositioning()
      → POST /api/mvp/positioning/generate
      → creates a new version in the DB
      → state.positioningHistory updated (new version prepended)

User types feedback and clicks "Refine Positioning →"
  → actions.refinePositioning()
      → POST /api/mvp/positioning/refine  (sends positioningFeedback as context)
      → creates another new version
      → state.positioningHistory updated

User clicks "Next: Personas →"
  → navigate to /personas
  → disabled until hasHistory is true
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.positioningHistory` | Array of all positioning versions, newest first |
| `state.positioningFeedback` | Bound to the refinement textarea |
| `state.prefetch.positioning` | If true + no history → show prefetch skeleton |
| `state.gateError` | Backend validation error (shown if `agent === "positioning_copilot"`) |
| `state.busy` | Disables buttons during generation |
| `state.activeProjectId` | Required for all API calls |
| `state.selectedProjectSessionId` | Used to load history for a specific session |

---

## Side Effect on Load

```javascript
useEffect(() => {
  if (!state.activeProjectId) return;
  actions.loadPositioningHistory(state.selectedProjectSessionId);
}, [state.activeProjectId, state.selectedProjectSessionId]);
```

History is loaded whenever the project or selected session changes. This ensures the page reflects the correct session's positioning history even when the user switches between sessions on the Projects page.

---

## Why Versioning Matters

Users typically need 2–3 iterations to get a positioning statement they're happy with. Keeping old versions visible means:
1. Users can compare different versions and understand how the statement evolved
2. If a refinement makes things worse, users can reference the previous version
3. The history serves as an audit trail for how thinking about the business position developed over time

---

## Next Step

"Next: Personas →" navigates to `/personas`. The button is **disabled** until `hasHistory` is true (at least one positioning version has been generated).
