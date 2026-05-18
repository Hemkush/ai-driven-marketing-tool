# Competitive Benchmarking Page (Analysis)

**File:** `apps/frontend/src/pages/AnalysisPage.jsx`
**Route:** `/analysis`
**Pipeline step:** 3 of 8
**Access:** Authenticated users only; requires completed interview

---

## Purpose

This page runs a live competitive intelligence scan for the user's local market. It uses the business address from the project profile to query Google Places for real competitors, then applies AI analysis to produce:
- Competitor profiles (name, rating, price tier, threat level, review count)
- A price-vs-quality scatter analysis
- SWOT breakdown relative to the local market
- Hours gaps (when competitors are closed)
- Market opportunity gaps to exploit

It also includes a persistent **Analysis Assistant** — an AI chat panel on the right side where users can ask follow-up questions about their competitive landscape.

---

## Gate: Interview Must Be Complete

If `state.interviewCompleted` is `false`, the page shows a locked "gate" UI instead of the main content. The gate:
- Displays a lock icon and heading "Complete Your Discovery Interview First"
- Shows a three-step checklist: Business Profile (marked done) → Complete Discovery Interview → Return Here and Run Benchmarking
- Provides a "Go to Marketing Discovery →" button

This prevents the user from running the analysis without the business context needed to interpret results correctly.

---

## What the User Sees

### Action Bar
Once the interview is complete, an action bar appears at the top with:
- A green "Interview Complete" badge
- A description of what the scan will do
- A button: "Run Competitive Benchmarking" (or "Re-run Benchmarking" if results already exist)

### Streaming Progress Log
When the scan is running, a real-time step log appears showing each pipeline step as it completes:
- Each step appears as a row with a spinner (in progress) or a green checkmark (done)
- Shows "Step X of Y" sub-label
- Before the first step event arrives, a generic `LoadingSkeleton` is shown

This streaming is powered by Server-Sent Events (SSE) from the backend. Each event contains `{ message, step, total, done }`.

### Results (Left Panel)
Once the scan completes, the left side shows:
- `AiChip` and `TrustBadge` (quality score)
- `CompetitorCards` — the main output component showing all competitor data
- `WhyThis` — expandable section showing the AI's reasoning
- `FeedbackThumbs` — thumbs up/down rating for the analysis quality

### Analysis Assistant (Right Panel / Sidebar)
A chat interface that persists alongside the results:
- Welcome message explaining what the assistant can help with
- Rotating suggestion chips (4 shown, chosen randomly from 8 pre-written questions):
  - "Which competitor poses the highest threat and why?"
  - "What are the 3 biggest gaps in my local market?"
  - "How should I price my services vs these competitors?"
  - etc.
- Clicking a chip sends it as a question immediately and removes the chip from the list
- Free-text textarea for custom questions (Enter sends; Shift+Enter = newline)
- Assistant responses use `StructuredMessage` for formatted output

### Gate Error Banner
If the backend's gate validation fails (e.g., missing business address), an orange warning banner appears above the action bar with the error message and a "Back to Questionnaire →" link.

---

## StructuredMessage Component

The Analysis Assistant's responses are rendered through a custom `StructuredMessage` component defined inside `AnalysisPage.jsx`. This component:
1. Takes raw AI text (which may contain markdown headings, bullet lists, numbered lists, or free paragraphs)
2. Parses it into logical blocks: each block has a heading and either bullet items or paragraph text
3. Renders each block cleanly — headings in bold, items in `<ul>`, paragraphs in `<p>`

This avoids rendering raw markdown as plain text (ugly) and avoids a full markdown library dependency.

---

## Logic Flow

```
User arrives at /analysis
  → if !interviewCompleted: show gate UI, stop

User clicks "Run Competitive Benchmarking"
  → actions.runAnalysis()
      → POST /api/mvp/analysis/run (SSE stream)
      → streamProgress events update state.streamProgress in real time
      → on completion: state.analysis is set

User clicks a suggestion chip
  → actions.askAnalysisAssistant(chipText)
      → adds user message to state.analysisAssistantMessages
      → POST /api/mvp/analysis/ask-assistant
      → appends AI response to state.analysisAssistantMessages

User types in the textarea and clicks "Ask →" (or presses Enter)
  → actions.askAnalysisAssistant(state.analysisAssistantInput)
      → same flow as chip selection

User clicks "Next: Positioning →"
  → navigate to /positioning
  → button is always enabled once analysis exists
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.interviewCompleted` | Controls gate — page is locked until this is true |
| `state.analysis` | The competitor analysis object from the backend |
| `state.analysisAssistantMessages` | Chat history for the analysis assistant |
| `state.analysisAssistantInput` | Current value of the assistant textarea |
| `state.analysisAssistantBusy` | Disables the "Ask →" button while a request is in flight |
| `state.streamProgress` | Array of pipeline step events for the progress log |
| `state.gateError` | Backend validation error (shown as warning banner if `agent === "competitive_benchmarker"`) |
| `state.busy` | Disables the "Run Benchmarking" button during the scan |

---

## Auto-Scroll Behavior

The assistant chat log auto-scrolls to the bottom whenever a new message is added or the assistant starts typing:

```javascript
useEffect(() => {
  if (!assistantLogRef.current) return;
  assistantLogRef.current.scrollTop = assistantLogRef.current.scrollHeight;
}, [state.analysisAssistantMessages.length, state.analysisAssistantBusy]);
```

---

## Next Step

"Next: Positioning →" navigates to `/positioning`. This button is **always enabled** once `state.analysis` exists (the analysis assistant context is sent along with the re-run if the user re-runs the analysis later).
