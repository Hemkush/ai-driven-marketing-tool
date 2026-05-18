# Content Studio Page

**File:** `apps/frontend/src/pages/ContentPage.jsx`
**Route:** `/content`
**Pipeline step:** 8 of 8
**Access:** Authenticated users only

---

## Purpose

The Content Studio is the final step in the pipeline. It generates ready-to-use, on-brand marketing content assets — written copy, structured documents, and visual assets — using the business's positioning, personas, roadmap, and market research as context.

Unlike generic AI writing tools, every asset generated here is written for this specific business, targeting its specific customer segments, with its specific competitive differentiators woven in.

---

## Content Categories and Types

Assets are organised into three categories:

### Text Content
| Asset Type | Description |
|---|---|
| Social Media Post | Short-form post for Facebook, LinkedIn, or Twitter |
| Instagram Caption | Visual-first caption with hashtag guidance |
| Google Business Post | Short update for Google Business Profile |
| Ad Copy (Google/Meta) | Headline + description pairs for paid ads |
| SMS Campaign | Short, action-oriented SMS marketing message |

### Structured Content
| Asset Type | Description |
|---|---|
| Email Newsletter | Full newsletter with subject line, sections, and CTA |
| Blog Post Intro | Opening section of a blog post to attract search traffic |
| Landing Page Copy | Headline, sub-copy, and CTA text for a web page |
| Press Release | Formal announcement format for news or launches |

### Visual Assets *(AI-generated image + design brief)*
| Asset Type | Description |
|---|---|
| Logo Concept | Brand logo concept as an image |
| Poster / Banner | Print or digital poster/banner |
| Social Media Visual | Graphic designed for social channels |

Visual asset generation produces both an AI-generated image AND a detailed design brief (fonts, colours, layout, style notes) — the design brief can be handed to a designer to recreate or iterate on the concept.

---

## What the User Sees

### Generator Form (`csp-form-card`)

**1. Category + Type Picker**
All asset types are shown as clickable chip buttons, grouped by category. Clicking a chip selects it (toggles if clicking the same chip again). Only one type can be selected at a time.

**2. Brand Tone Selector**
Five tone options: Professional, Friendly, Urgent, Playful, Bold.

Above the selector, an **AI Recommendation Banner** appears based on the business's questionnaire answers:
- Shows the recommended tone and reasoning (e.g., "Friendly tone is recommended for your business. Your answers suggest a community-focused, approachable brand.")
- If the user overrides the recommendation, the banner shows "Override active" and a "Use recommended tone" button to revert

**3. Additional Context / Visual Direction**
A textarea for optional free-form direction:
- For visual assets: "e.g. Use deep navy and gold tones, modern sans-serif, convey premium quality…"
- For text assets: "e.g. Promote our summer special, target weekend clients, warm and local tone…"

**4. Variants Picker**
Buttons 1–5 to select how many variants to generate. For visual assets, each variant = one image + one design brief.

**5. Visual Asset Notice**
When a visual asset type is selected, an info banner explains: "AI generates the image; a detailed design brief is always included as a reference. Images are stored permanently — download anytime."

**6. Generate Button**
- "Generate Content →" for text/structured assets
- "Generate Visual →" for visual assets
- Disabled if no asset type is selected or the app is busy

---

### Streaming Progress Log
Same pattern as the Analysis page — SSE events stream in real time showing pipeline steps with spinners and checkmarks. A fallback skeleton is shown before the first event arrives.

---

### Generated Assets

Assets are displayed grouped by type (newest generation first within each group). For each type group:
- A heading row with the type label, variant count, and a "Clear" button for that group
- `ContentAssetCards` renders the individual asset cards

Above all groups:
- Asset count badge, `AiChip`, `TrustBadge`
- "Ready to copy, download, or schedule" hint
- `FeedbackThumbs`
- "Clear all" button to remove all assets from the current view

---

### Empty State
When no assets have been generated yet, a placeholder with icon, heading "No Content Assets Yet", and instructional sub-copy.

---

## Tone Suggestion Logic

On page load (when `activeProjectId` is set and no tone suggestion exists yet):
```javascript
useEffect(() => {
  if (state.activeProjectId && !state.toneSuggestion) {
    actions.fetchToneSuggestion();
  }
}, [state.activeProjectId]);
```

This calls the backend to analyse the questionnaire answers and return a suggested tone. The suggestion is stored in `state.toneSuggestion` and displayed in the recommendation banner. The AI star icon (★) also appears on the suggested tone button in the tone picker.

---

## Asset Grouping Logic

Assets from multiple generations are grouped by type in the display:
```javascript
const groups = [];
const seen = new Map();
state.contentAssets.forEach((a) => {
  const t = a.asset_type || "other";
  if (!seen.has(t)) { seen.set(t, []); groups.push(t); }
  seen.get(t).push(a);
});
```

This means if the user generates 3 social posts, then 2 email newsletters, then 2 more social posts, the display shows:
- Social Media Post (5 variants)
- Email Newsletter (2 variants)

---

## Logic Flow

```
Page loads
  → if activeProjectId && !toneSuggestion: actions.fetchToneSuggestion()

User selects asset type
  → set.setAssetType(value)  (toggle off if same type clicked)

User selects tone
  → set.setAssetTone(value)

User types optional context
  → set.setAssetPrompt(value)

User selects variant count
  → set.setNumVariants(n)

User clicks "Generate Content →"
  → actions.generateContent()
      → POST /api/mvp/content/generate  (SSE stream)
      → sends: assetType, assetTone, assetPrompt, numVariants
      → as context: positioning, personas, roadmap, analysis
      → state.contentAssets updated with new assets (prepended)

User clicks "Clear" on a type group
  → actions.clearAssetsByType(type)
      → removes assets of that type from state.contentAssets

User clicks "Clear all"
  → actions.clearAllAssets()
      → clears state.contentAssets

User clicks "Load Saved Assets"
  → actions.loadContentAssets()
      → GET /api/mvp/content/assets
      → loads previously generated assets from the DB

User clicks "Back to Projects →"
  → navigate to /projects  (always enabled — this is the last step)
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.contentAssets` | Array of all generated content asset objects |
| `state.assetType` | Currently selected asset type value |
| `state.assetTone` | Currently selected tone value |
| `state.assetPrompt` | Bound to the context textarea |
| `state.numVariants` | Number of variants to generate (1–5) |
| `state.toneSuggestion` | AI tone recommendation object `{ suggested_tone, reasoning }` |
| `state.contentStreamProgress` | SSE step events for the progress log |
| `state.gateError` | Backend validation error (shown if `agent === "content_studio"`) |
| `state.busy` | Disables the generate button during generation |
| `state.activeProjectId` | Required for all API calls |

---

## Why Content Is Last

The Content Studio is deliberately placed last because it uses every other pipeline output as context:
- **Positioning** → shapes the brand voice and key messages in all copy
- **Personas** → the AI writes to specific persona types depending on the asset (e.g., an Instagram caption is written to attract the "Instagram-first" persona)
- **Roadmap** → makes content relevant to current execution priorities (e.g., Week 3 = Google Ads launch → generate ad copy)
- **Research** → uses buying journey insights to write copy that addresses the right stage (awareness vs. consideration vs. decision)

Without these prior steps, the content would be generic. With them, it reads like it was written by someone who deeply understands the business and its customers.

---

## Closing the Loop

After the Content Studio, the "Back to Projects →" button returns the user to `/projects`. From there they can:
- Review their session history
- Start a new strategy session (e.g., quarterly re-run)
- Switch to a different business workspace
