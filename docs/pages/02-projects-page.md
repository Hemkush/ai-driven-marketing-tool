# Business Profile Page (Projects)

**File:** `apps/frontend/src/pages/ProjectsPage.jsx`
**Component:** Delegates entirely to `src/components/ProjectPanel.jsx`
**Route:** `/projects`
**Pipeline step:** 1 of 8
**Access:** Authenticated users only

---

## Purpose

This is the first page a user lands on after logging in. Its job is to:
1. Let users create a new business workspace (called a "project") by entering a business name, description, and physical address
2. Let users switch between multiple business workspaces if they have more than one
3. Show a list of previous strategy sessions for the selected project and let users load one to review past outputs
4. Start a new strategy session for the selected business

Every subsequent pipeline step (questionnaire → analysis → personas → etc.) belongs to a specific session under a specific project. The project stores the persistent business identity; the session stores the outputs from one run of the pipeline.

---

## Key Concepts

### Project
A "project" represents one business. It has a name (e.g., "The Bloom Room"), a description, and a physical business address. The address is used in the competitive benchmarking step to query Google Places for nearby competitors.

### Session
A "session" is one complete run of the pipeline for a project. A project can have many sessions (e.g., re-running the strategy quarterly). Each session stores its own questionnaire answers, competitor analysis, personas, roadmap, and content assets.

---

## What the User Sees

### Create New Project Form
- **Business Name** — text input, required. Used as the project identifier throughout the app.
- **Business Description** — textarea. Gives the AI context about the business type and what it offers. Example: "A boutique flower shop specialising in same-day arrangements and campus event floristry."
- **Business Address** — text input. Used by the competitive benchmarking agent to query Google Places for competitors within the same geographic area.
- **"Create & Continue" button** — calls `actions.createProject()`, and on success navigates to `/questionnaire`

### Project List
If the user has existing projects, they are shown as selectable items. Selecting a project:
1. Sets it as the active project (`set.setActiveProjectId`)
2. Loads its session history (`actions.loadProjectSessions`)

### Session History
Once a project is selected, its past sessions are listed. Each session shows:
- The date it was created
- How many questionnaire questions were answered
- A progress summary of which pipeline steps were completed

Clicking a session calls `actions.selectProjectSession`, which loads the full session detail and restores all the workflow state (analysis, personas, roadmap, etc.) from that session's saved outputs.

### "Start New Workflow" button
Calls `actions.resetForNewSession()` which clears all in-memory pipeline state, then navigates to `/questionnaire` to begin a fresh session for the currently selected project.

---

## Logic Flow

```
Page loads
  → if activeProjectId exists:
      actions.loadProjectSessions(activeProjectId)   ← refreshes session list

User fills in name + description + address
  → clicks "Create & Continue"
      → actions.createProject()
          → POST /api/projects
          → on success: activeProjectId set, navigate to /questionnaire

User selects existing project
  → setActiveProjectId(id)
      → useEffect in useMvpWorkflow fires
          → actions.loadProjectSessions(id)

User clicks a past session
  → actions.selectProjectSession(sessionId)
      → loads saved outputs into workflow state
      → user can review the old strategy

User clicks "Start New Workflow"
  → actions.resetForNewSession()   ← clears all state
  → navigate to /questionnaire
```

---

## State Used

| State field | How it's used |
|---|---|
| `state.projectName` | Bound to the business name input |
| `state.projectDescription` | Bound to the description textarea |
| `state.projectBusinessAddress` | Bound to the address input |
| `state.projects` | List of all projects for the current user |
| `state.activeProjectId` | The currently selected project's ID |
| `state.activeProject` | Full project object for the selected project |
| `state.projectSessions` | List of past sessions for the active project |
| `state.selectedProjectSessionId` | Which past session is currently selected |
| `state.selectedProjectSessionDetail` | Full detail of the selected session |
| `state.selectedProjectSessionWorkflow` | Restored workflow state from the selected session |
| `state.busy` | Disables buttons during async operations |

---

## Side Effects on Load

```javascript
useEffect(() => {
  if (state.activeProjectId) {
    actions.loadProjectSessions(String(state.activeProjectId));
  }
}, []);
```

Every time the user navigates to this page, the session list is refreshed. This ensures the `answered_count` (questionnaire progress) reflects any work done in the interview since the project was last viewed.

---

## Next Step

After creating a project or selecting an existing one, the user proceeds to the **Marketing Discovery** page (`/questionnaire`). The "Next Step" button at the bottom of the page is not shown here because `ProjectsPage` itself handles navigation via `navigate("/questionnaire")` directly after project creation.
