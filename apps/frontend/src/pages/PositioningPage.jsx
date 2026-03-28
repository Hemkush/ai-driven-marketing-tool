import { useEffect } from "react";
import { ActionRow, EmptyState, NextStepCta } from "../components/UiBlocks";
import { PositioningCard } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PositioningPage({ workflow }) {
  const { state, set, actions } = workflow;

  useEffect(() => {
    if (!state.activeProjectId) return;
    actions.loadPositioningHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.activeProjectId]);

  const hasHistory = state.positioningHistory?.length > 0;
  const latest = state.positioningHistory?.[0];

  return (
    <div>
      {/* Header */}
      <div className="positioning-page-header">
        <div>
          <h3 className="positioning-page-title">Positioning Statement</h3>
          <p className="positioning-page-desc">
            AI generates your market positioning based on your discovery interview and competitor benchmarking.
            Refine it with your own feedback until it feels right.
          </p>
        </div>
        <ActionRow>
          <button
            className="btn"
            onClick={actions.generatePositioning}
            disabled={state.busy || !state.activeProjectId}
          >
            {hasHistory ? "Regenerate" : "Generate Positioning"}
          </button>
        </ActionRow>
      </div>

      {state.busy && <LoadingSkeleton lines={5} />}

      {/* Latest positioning — prominent display */}
      {!state.busy && latest && (
        <div className="positioning-latest-wrap">
          <div className="positioning-version-badge">
            Latest · Version {latest.version}
            {latest.created_at && (
              <span className="positioning-version-date">
                {" · "}{new Date(latest.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
              </span>
            )}
          </div>
          <PositioningCard positioning={latest} isLatest />
        </div>
      )}

      {/* Refine section */}
      {!state.busy && hasHistory && (
        <div className="positioning-refine-section">
          <h5 className="refine-title">Refine with Your Feedback</h5>
          <p className="refine-hint">
            Tell the AI what to change — e.g. <em>"Focus more on weekend clients"</em> or{" "}
            <em>"We specialize in natural hair, emphasise that"</em> or{" "}
            <em>"The tone is too formal, make it friendlier"</em>
          </p>
          <textarea
            className="refine-textarea"
            placeholder="What should change in the next version?"
            value={state.positioningFeedback}
            onChange={(e) => set.setPositioningFeedback(e.target.value)}
            rows={3}
          />
          <button
            className="btn ghost"
            onClick={actions.refinePositioning}
            disabled={state.busy || !state.positioningFeedback.trim()}
          >
            Refine Positioning →
          </button>
        </div>
      )}

      {/* Version history */}
      {!state.busy && state.positioningHistory?.length > 1 && (
        <div className="positioning-history-section">
          <h5 className="history-title">Version History</h5>
          <div className="stack-gap">
            {state.positioningHistory.slice(1).map((entry, idx) => (
              <div key={entry.id || `${entry.version}-${idx}`} className="history-entry">
                <div className="history-entry-meta">
                  Version {entry.version}
                  {entry.created_at && (
                    <span> · {new Date(entry.created_at).toLocaleDateString()}</span>
                  )}
                </div>
                <PositioningCard positioning={entry} />
              </div>
            ))}
          </div>
        </div>
      )}

      {!state.busy && !hasHistory && (
        <EmptyState
          glyph="◍"
          title="No Positioning Draft Yet"
          description="Run Competitive Benchmarking first, then click Generate Positioning. The AI will craft a statement specific to your business type and local market."
        />
      )}

      <NextStepCta to="/personas" label="Next: Personas" disabled={!state.positioning} />
    </div>
  );
}
