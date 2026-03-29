import { useEffect } from "react";
import { NextStepCta } from "../components/UiBlocks";
import { PositioningCard } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PositioningPage({ workflow }) {
  const { state, set, actions } = workflow;

  useEffect(() => {
    if (!state.activeProjectId) return;
    actions.loadPositioningHistory(state.selectedProjectSessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.activeProjectId, state.selectedProjectSessionId]);

  const hasHistory = state.positioningHistory?.length > 0;
  const latest = state.positioningHistory?.[0];
  const olderVersions = state.positioningHistory?.slice(1) || [];

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasHistory) {
    return (
      <div className="psp-page">
        <div className="psp-gate">
          <div className="psp-gate-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          </div>
          <h2 className="psp-gate-title">No Positioning Draft Yet</h2>
          <p className="psp-gate-sub">
            The AI crafts your unique market position by synthesising your discovery interview and
            competitive benchmarking data — make sure both steps are complete for the best result.
          </p>
          <div className="psp-gate-steps">
            <div className="psp-gate-step">
              <span className={`psp-step-badge${state.interviewCompleted ? " psp-step-done" : ""}`}>
                {state.interviewCompleted ? "✓" : "1"}
              </span>
              <div className="psp-step-body">
                <p className="psp-step-title">Discovery Interview</p>
                <p className="psp-step-sub">
                  {state.interviewCompleted ? "Complete" : "Answer all interview questions and click Complete Interview"}
                </p>
              </div>
            </div>
            <div className="psp-gate-step">
              <span className={`psp-step-badge${state.analysis ? " psp-step-done" : ""}`}>
                {state.analysis ? "✓" : "2"}
              </span>
              <div className="psp-step-body">
                <p className="psp-step-title">Competitive Benchmarking</p>
                <p className="psp-step-sub">
                  {state.analysis ? "Complete" : "Run the competitor analysis from the Benchmarking page"}
                </p>
              </div>
            </div>
            <div className="psp-gate-step">
              <span className="psp-step-badge">3</span>
              <div className="psp-step-body">
                <p className="psp-step-title">Generate Positioning</p>
                <p className="psp-step-sub">Click the button below — AI generates in ~20 seconds</p>
              </div>
            </div>
          </div>
          <button
            className="btn psp-gate-cta"
            onClick={actions.generatePositioning}
            disabled={state.busy || !state.activeProjectId}
          >
            Generate Positioning →
          </button>
        </div>
        <NextStepCta to="/personas" label="Next: Personas" disabled={true} />
      </div>
    );
  }

  /* ── Main page ────────────────────────────────────────────────────────── */
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
          disabled={state.busy || !state.activeProjectId}
        >
          {hasHistory ? "Regenerate Positioning" : "Generate Positioning"}
        </button>
      </div>

      {/* Loading */}
      {state.busy && (
        <LoadingSkeleton lines={5} message="Generating your positioning statement…" />
      )}

      {/* Latest version — hero display */}
      {!state.busy && latest && (
        <div className="psp-latest">
          <div className="psp-version-badge">
            <span className="psp-live-dot" aria-hidden="true" />
            Latest · Version {latest.version}
            {latest.created_at && (
              <span className="psp-version-date">
                {" · "}{new Date(latest.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
              </span>
            )}
          </div>
          <PositioningCard positioning={latest} isLatest />
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
