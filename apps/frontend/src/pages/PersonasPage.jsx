import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { PersonaCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PersonasPage({ workflow }) {
  const { state, actions } = workflow;
  const hasPersonas = state.personas.length > 0;

  return (
    <div>
      {/* Header */}
      <div className="positioning-page-header">
        <div>
          <h3 className="positioning-page-title">Buyer Personas</h3>
          <p className="positioning-page-desc">
            AI builds detailed buyer personas from your competitive benchmarking data and positioning statement —
            covering goals, pain points, behaviour, channels, and the exact messages that convert each type.
          </p>
        </div>
        <ActionRow>
          <button
            className="btn"
            onClick={actions.generatePersonas}
            disabled={state.busy || !state.activeProjectId}
          >
            {hasPersonas ? "Regenerate Personas" : "Generate Personas"}
          </button>
        </ActionRow>
      </div>

      {state.busy && <LoadingSkeleton lines={6} />}

      {!state.busy && hasPersonas && (
        <PersonaCards personas={state.personas} />
      )}

      {!state.busy && !hasPersonas && (
        <EmptyState
          glyph="◕"
          title="No Personas Yet"
          description="Complete Competitive Benchmarking and Positioning first, then click Generate Personas. The AI will build personas specific to your business type and local market."
        />
      )}

      <NextStepCta
        to="/research"
        label="Next: Research"
        disabled={state.personas.length === 0}
      />
    </div>
  );
}
