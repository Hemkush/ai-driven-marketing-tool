import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { StrategyCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function StrategyPage({ workflow }) {
  const { state, actions } = workflow;
  return (
    <div>
      <ActionRow>
        <button className="btn" onClick={actions.generateStrategy} disabled={state.busy || !state.activeProjectId}>
          Generate Strategy
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={5} />}
      {!state.busy && state.strategy && <StrategyCards strategy={state.strategy} />}
      {!state.busy && !state.strategy && (
        <EmptyState
          glyph="◒"
          title="Strategy Not Ready"
          description="Generate channel strategy once personas are available."
        />
      )}
      <NextStepCta
        to="/roadmap"
        label="Next: Roadmap"
        disabled={!state.strategy}
      />
    </div>
  );
}
