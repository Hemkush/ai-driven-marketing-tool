import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { ContentAssetCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function ContentPage({ workflow }) {
  const { state, set, actions } = workflow;
  return (
    <div>
      <input
        placeholder="Asset type"
        value={state.assetType}
        onChange={(e) => set.setAssetType(e.target.value)}
      />
      <br />
      <textarea
        placeholder="Asset prompt"
        value={state.assetPrompt}
        onChange={(e) => set.setAssetPrompt(e.target.value)}
        rows={3}
        style={{ width: "100%", maxWidth: 760 }}
      />
      <br />
      <input
        type="number"
        min={1}
        max={5}
        value={state.numVariants}
        onChange={(e) => set.setNumVariants(Number(e.target.value))}
      />
      <ActionRow>
        <button className="btn" onClick={actions.generateContent} disabled={state.busy || !state.activeProjectId}>
          Generate Content Assets
        </button>
        <button className="btn ghost" onClick={actions.loadContentAssets} disabled={state.busy || !state.activeProjectId}>
          Load Stored Assets
        </button>
      </ActionRow>
      {state.busy && <LoadingSkeleton lines={4} />}
      {!state.busy && state.contentAssets.length > 0 && <ContentAssetCards assets={state.contentAssets} />}
      {!state.busy && state.contentAssets.length === 0 && (
        <EmptyState
          glyph="◐"
          title="No Content Assets Yet"
          description="Generate assets from roadmap and strategy to start execution."
        />
      )}
      <NextStepCta
        to="/projects"
        label="Back to Projects"
        disabled={false}
      />
    </div>
  );
}
