import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { RoadmapCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function RoadmapPage({ workflow }) {
  const { state, actions } = workflow;
  return (
    <div>
      <ActionRow>
        <button className="btn" onClick={actions.generateRoadmap} disabled={state.busy || !state.activeProjectId}>
          Generate Roadmap
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={6} />}
      {!state.busy && state.roadmap && <RoadmapCards roadmap={state.roadmap} />}
      {!state.busy && !state.roadmap && (
        <EmptyState
          glyph="◑"
          title="Roadmap Not Generated"
          description="Generate a 90-day execution roadmap based on your strategy and personas."
        />
      )}
      <NextStepCta
        to="/content"
        label="Next: Content Studio"
        disabled={!state.roadmap}
      />
    </div>
  );
}
