# Buyer Personas Page

**File:** `apps/frontend/src/pages/PersonasPage.jsx`
**Route:** `/personas`
**Pipeline step:** 5 of 8
**Access:** Authenticated users only

---

## Purpose

This page generates detailed **buyer personas** — fictional but data-grounded profiles representing the business's most valuable customer segments. Each persona describes a specific type of customer: who they are, what they want, what frustrates them, how they make purchasing decisions, and which marketing channels they use.

Personas are used as input context by:
- The Market Research agent (to personalise buying journey analysis)
- The Roadmap agent (to target the right channels with the right messages)
- The Content Studio (to write copy that resonates with specific segments)

---

## What the User Sees

### Page Header
- Title: "Buyer Personas"
- Description: "Detailed profiles of your most valuable customer segments — built from your real business data."
- "Generate Personas" button (only visible when no personas exist yet)
- Once personas exist, the header has no button — the regenerate control is at the bottom of the page inside the refine section

### Empty / No Personas State
When no personas have been generated:
- A blurred ghost preview (`GhostPreviewPersonas`) with a placeholder message
- The ghost preview gives the user a visual sense of the card layout before they generate

### Loading States
- **Prefetch in progress**: skeleton with "Building your buyer personas in the background…"
- **Manual generate**: skeleton with "Building your buyer personas…"

### Persona Cards
Once personas are generated, they appear as individual `PersonaCards`:
- **Meta row** above the cards: count badge (e.g., "3 personas generated"), `AiChip`, `TrustBadge`, a hint about data sources, and the `PersonaExportBar`
- Each card typically shows: name, age, occupation, goal, pain point, how they make decisions, key marketing channels, and the most effective marketing message for that persona

### Export Bar (`PersonaExportBar`)
Two action buttons above the persona cards:
- **Copy** — formats all personas as plain text and copies to the clipboard via `navigator.clipboard.writeText()`. Shows "Copied!" for 2 seconds, then resets.
- **Print / PDF** — calls `window.print()`, which opens the browser's print dialog. The user can save as PDF.

### Generation Trace (Collapsible)
If `state.personaGenerationContext` is available, a collapsible "How these personas were generated" section appears:
- Shows the AI model used (e.g., "gpt-4o")
- Lists the agent steps (the reasoning chain the AI followed)
- Lists the data sources used (e.g., "Business questionnaire answers", "Competitor analysis", "Local market data")

This transparency helps users understand why the personas look the way they do and builds trust in the output.

### Feedback + Regenerate Section
At the bottom, a refine card allows users to iterate:
- Textarea with placeholder examples: "focus more on small business owners", "remove the price-sensitive segment and add a premium buyer"
- Button label changes based on whether feedback is entered:
  - No feedback: "Regenerate Personas →"
  - With feedback: "Regenerate with Feedback →"

### Gate Error Banner
Orange warning banner if the backend's gate validation fails, with a "Back to Questionnaire →" link.

---

## Logic Flow

```
User arrives at /personas
  → no side effect on load (personas are loaded via workflow state)

User clicks "Generate Personas"
  → actions.generatePersonas()
      → POST /api/mvp/personas/generate
      → sends current questionnaire context + competitor analysis as input
      → state.personas set to array of persona objects
      → state.personaGenerationContext set (agent steps + data sources)

User types feedback and clicks "Regenerate with Feedback →"
  → actions.generatePersonas()  ← same action, feedback is in state.personaFeedback
      → POST /api/mvp/personas/generate  (includes feedback as refinement context)
      → replaces state.personas with the new set

User clicks "Copy" in ExportBar
  → personasToText(personas)  ← formats personas as readable text
  → navigator.clipboard.writeText(text)
  → "Copied!" flash for 2 seconds

User clicks "Print / PDF"
  → window.print()

User clicks "Next: Research →"
  → navigate to /research
  → disabled until hasPersonas is true
```

---

## personasToText Helper

```javascript
function personasToText(personas) {
  return personas.map((p) => [
    `== ${p.name} ==`,
    p.age ? `Age: ${p.age}` : "",
    p.occupation ? `Occupation: ${p.occupation}` : "",
    p.goal ? `Goal: ${p.goal}` : "",
    p.pain_point ? `Pain point: ${p.pain_point}` : "",
    p.channels?.length ? `Channels: ${p.channels.join(", ")}` : "",
  ].filter(Boolean).join("\n")).join("\n\n");
}
```

Produces clean plain-text output suitable for pasting into documents or other tools.

---

## State Used

| State field | How it's used |
|---|---|
| `state.personas` | Array of persona objects |
| `state.personaFeedback` | Bound to the refinement textarea |
| `state.personaGenerationContext` | Agent trace data (steps + data sources) |
| `state.prefetch.personas` | If true + no personas → show prefetch skeleton |
| `state.gateError` | Backend validation error (shown if `agent === "persona_builder"`) |
| `state.busy` | Disables buttons during generation |
| `state.activeProjectId` | Required for all API calls |

---

## Why Personas Are Generated Here (Not Earlier)

Personas are generated after positioning because the positioning statement helps the AI understand which customer segments to focus on. A business positioned as "premium" will attract different personas than one positioned as "budget-friendly." Running personas after positioning ensures the segments are coherent with the business's chosen market position.

---

## Next Step

"Next: Research →" navigates to `/research`. The button is **disabled** until `hasPersonas` is true (at least one set of personas has been generated).
