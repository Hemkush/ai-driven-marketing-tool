import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { ResearchCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function ResearchPage({ workflow }) {
  const { state, actions } = workflow;
  return (
    <div>
      <ActionRow>
        <button className="btn" onClick={actions.runResearch} disabled={state.busy || !state.activeProjectId}>
          Run Research
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={5} />}
      {!state.busy && state.research && <ResearchCards research={state.research} />}
      {!state.busy && !state.research && (
        <EmptyState
          glyph="◔"
          title="Research Pending"
          description="Run research to gather deeper customer and competitor insights with evidence."
        />
      )}
      <NextStepCta
        to="/personas"
        label="Next: Personas"
        disabled={!state.research}
      />
    </div>
  );
}
