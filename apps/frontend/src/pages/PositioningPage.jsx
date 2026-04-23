import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { PositioningCard } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";

export default function PositioningPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();

  useEffect(() => {
    if (!state.activeProjectId) return;
    actions.loadPositioningHistory(state.selectedProjectSessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.activeProjectId, state.selectedProjectSessionId]);

  const hasHistory = state.positioningHistory?.length > 0;
  const latest = state.positioningHistory?.[0];
  const olderVersions = state.positioningHistory?.slice(1) || [];
  const isPrefetching = !hasHistory && state.prefetch?.positioning;

  return (
    <div className="psp-page">
      {/* Page header */}
      <div className="psp-header">
        <div className="psp-header-text">
          <h3 className="psp-title">Positioning Statement</h3>
          <p className="psp-desc">
            Your unique market position — the space your business owns in your customers' minds.
            Refine it with feedback until it resonates perfectly.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.generatePositioning}
          disabled={state.busy || isPrefetching || !state.activeProjectId}
        >
          {hasHistory ? "Regenerate Positioning" : "Generate Positioning"}
        </button>
      </div>

      {/* Background prefetch in progress */}
      {isPrefetching && !state.busy && (
        <LoadingSkeleton lines={5} message="Preparing your positioning statement…" />
      )}

      {/* Manual generate loading */}
      {state.busy && (
        <LoadingSkeleton lines={5} message="Generating your positioning statement…" />
      )}

      {/* Gate error */}
      {state.gateError?.agent === "positioning_copilot" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {/* Latest version — hero display */}
      {!state.busy && !isPrefetching && latest && (
        <div className="psp-latest">
          <div className="psp-version-badge" style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span className="psp-live-dot" aria-hidden="true" />
            Latest · Version {latest.version}
            {latest.created_at && (
              <span className="psp-version-date">
                {" · "}{new Date(latest.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
              </span>
            )}
            <AiChip />
            <TrustBadge score={latest.quality_score} />
          </div>
          <PositioningCard positioning={latest} isLatest />
          <WhyThis reasoning={latest.reasoning} />
          <div style={{ marginTop: "12px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="positioning_copilot" qualityScore={latest.quality_score} />
          </div>
        </div>
      )}

      {/* Refine section */}
      {!state.busy && hasHistory && (
        <div className="psp-refine">
          <div className="psp-refine-head">
            <p className="psp-refine-title">Refine with Your Feedback</p>
            <p className="psp-refine-hint">
              Tell the AI what to change —
              e.g. <em>"Focus more on weekend clients"</em>,{" "}
              <em>"Emphasise our natural hair specialisation"</em>, or{" "}
              <em>"The tone is too formal, make it friendlier"</em>
            </p>
          </div>
          <textarea
            className="psp-refine-textarea"
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

      {/* Version history — collapsed accordion */}
      {!state.busy && olderVersions.length > 0 && (
        <div className="psp-history">
          <p className="psp-history-label">
            Previous Versions
            <span className="psp-history-count">{olderVersions.length}</span>
          </p>
          <div className="psp-history-list">
            {olderVersions.map((entry, idx) => (
              <details key={entry.id || `${entry.version}-${idx}`} className="psp-history-item">
                <summary className="psp-history-summary">
                  <span className="psp-history-version">Version {entry.version}</span>
                  {entry.created_at && (
                    <span className="psp-history-date">
                      {new Date(entry.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                    </span>
                  )}
                  {entry.tagline && (
                    <span className="psp-history-tagline">"{entry.tagline}"</span>
                  )}
                  <svg className="psp-history-chevron" aria-hidden="true" width="14" height="14"
                    viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </summary>
                <div className="psp-history-body">
                  <PositioningCard positioning={entry} />
                </div>
              </details>
            ))}
          </div>
        </div>
      )}

      <NextStepCta to="/personas" label="Next: Personas" disabled={!hasHistory} />
    </div>
  );
}
