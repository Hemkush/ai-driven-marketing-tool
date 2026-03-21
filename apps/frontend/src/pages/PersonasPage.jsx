import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { PersonaCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PersonasPage({ workflow }) {
  const { state, actions } = workflow;
  return (
    <div>
      <ActionRow>
        <button className="btn" onClick={actions.generatePersonas} disabled={state.busy || !state.activeProjectId}>
          Generate Personas
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={5} />}
      {!state.busy && state.personas.length > 0 && <PersonaCards personas={state.personas} />}
      {!state.busy && state.personas.length === 0 && (
        <EmptyState
          glyph="◕"
          title="No Personas Generated"
          description="Generate buyer personas to drive channel strategy and message targeting."
        />
      )}
      <NextStepCta
        to="/strategy"
        label="Next: Strategy"
        disabled={state.personas.length === 0}
      />
    </div>
  );
}
