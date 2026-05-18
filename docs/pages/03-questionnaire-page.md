# Marketing Discovery Page (Questionnaire)

**File:** `apps/frontend/src/pages/QuestionnairePage.jsx`
**Component:** Delegates to `src/components/QuestionnaireChatPanel.jsx`
**Route:** `/questionnaire`
**Pipeline step:** 2 of 8
**Access:** Authenticated users only

---

## Purpose

This page conducts an AI-powered discovery interview with the user about their business. The AI asks targeted marketing questions one at a time in a conversational chat format. The user's answers form the foundational context used by every subsequent AI agent in the pipeline — competitor analysis, positioning, personas, roadmap, and content all depend on what is collected here.

---

## What the User Sees

The page is entirely composed of `QuestionnaireChatPanel`, which renders:

### Chat Interface
- A scrollable message thread showing AI questions and user replies
- The AI asks questions sequentially — one at a time
- The user types a reply and sends it
- A typing indicator appears while the AI is processing

### Topics Covered in the Interview
The AI's questions are dynamically generated based on what has already been answered, but they typically cover:
- Business type and primary offering
- Target customer profile
- Current marketing channels and what's working
- Main competitors (known or suspected)
- Biggest marketing challenge
- Geographic focus and service area
- Pricing position (budget, mid-range, premium)
- Unique strengths or differentiators
- Goals for the next 90 days

The backend deduplicates questions using semantic similarity — if the user's answers have already covered a topic, the AI won't ask again.

### Interview Analysis Panel
As the user answers questions, a live "Interview Coverage" analysis appears below the chat showing which marketing topics have been covered and which are still outstanding. This helps users know when they've given the AI enough context.

### "Complete Interview" Button
Once the AI determines sufficient context has been gathered, a "Complete Interview" button appears. Clicking this:
1. Calls `actions.finishQuestionnaireChat()`
2. Sets `state.interviewCompleted = true`
3. Triggers background prefetching of positioning, personas, and roadmap outputs (so those pages load faster later)
4. Enables the "Next: Competitive Benchmarking" CTA at the bottom of the page

---

## Logic Flow

```
User arrives at this page
  → if no active session: actions.startQuestionnaireChat()
      → POST /api/mvp/questionnaire/start
      → creates a session, gets the first AI question
      → stores sessionId in state

  → if session already exists: actions.loadQuestionnaireChat()
      → GET /api/mvp/questionnaire/messages
      → restores the chat history

User types a reply and sends
  → actions.sendQuestionnaireChatReply(message)
      → POST /api/mvp/questionnaire/reply
      → backend stores answer, generates next question via AI
      → response includes the next question message

User clicks "Complete Interview"
  → actions.finishQuestionnaireChat()
      → POST /api/mvp/questionnaire/finish
      → marks interview as complete in DB
      → triggers background prefetch (positioning, personas, roadmap)
      → sets interviewCompleted = true

User clicks "Next: Competitive Benchmarking"
  → navigate to /analysis
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.activeProjectId` | Identifies which project this interview belongs to |
| `state.sessionId` | The current interview session's ID |
| `state.chatMessages` | Array of `{ role: "user" | "assistant", content: string }` |
| `state.interviewAnalysis` | Coverage analysis object — which topics are covered |
| `state.interviewCompleted` | Boolean — true once the user has clicked "Complete Interview" |
| `state.busy` | Disables send button during API calls |

---

## Gate Behavior

This page has no hard gate — users can start the interview at any time after creating a project. However, all downstream pages require `state.interviewCompleted` to be `true` before they will run their AI agents.

---

## Privacy Notice

A small disclaimer is displayed below the chat:
> "Your answers are used only to generate your personalised marketing strategy. No data is sold or shared with third parties. AI-generated outputs are for guidance only — review before acting."

---

## Next Step

After completing the interview, the CTA button "Next: Competitive Benchmarking" becomes enabled and navigates to `/analysis`. The button is disabled until `state.interviewCompleted` is `true`.

---

## Why This Step Matters

The questionnaire is the most important step in the pipeline because its output shapes everything else:
- The competitor analysis uses the business address and type to scope the Google Places search
- The positioning agent uses the business description and differentiators to craft the statement
- Persona generation uses the target customer description to build accurate profiles
- The roadmap uses the 90-day goals and current channels to prioritise actions
- Content generation uses the tone, messaging, and channels identified here

Skimping on the answers produces generic, less useful AI outputs downstream. The interview is deliberately conversational to encourage detailed, natural responses rather than short one-word answers.
