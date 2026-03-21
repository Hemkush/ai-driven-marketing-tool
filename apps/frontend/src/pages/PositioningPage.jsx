import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { PositioningCard } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PositioningPage({ workflow }) {
  const { state, set, actions } = workflow;
  return (
    <div>
      <ActionRow>
        <button className="btn" onClick={actions.generatePositioning} disabled={state.busy || !state.activeProjectId}>
          Generate Positioning
        </button>
      </ActionRow>
      <div style={{ marginTop: 12 }}>
        <textarea
          placeholder="Owner feedback for refinement"
          value={state.positioningFeedback}
          onChange={(e) => set.setPositioningFeedback(e.target.value)}
          rows={3}
          style={{ width: "100%", maxWidth: 760 }}
        />
      </div>
      <ActionRow>
        <button className="btn ghost" onClick={actions.refinePositioning} disabled={state.busy || !state.positioningFeedback.trim()}>
          Refine Positioning
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={4} />}
      {!state.busy && state.positioning && <PositioningCard positioning={state.positioning} />}
      {!state.busy && !state.positioning && (
        <EmptyState
          glyph="◎"
          title="No Positioning Draft Yet"
          description="Generate a first positioning statement and refine it with business-owner feedback."
        />
      )}
      <NextStepCta
        to="/research"
        label="Next: Research"
        disabled={!state.positioning}
      />
    </div>
  );
}
