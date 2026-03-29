import { NextStepCta } from "../components/UiBlocks";
import { RoadmapCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function RoadmapPage({ workflow }) {
  const { state, actions } = workflow;
  const hasRoadmap = !!state.roadmap;
  const hasStrategy = !!state.strategy;

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasRoadmap) {
    return (
      <div className="rmp-page">
        <div className="rmp-gate">
          <div className="rmp-gate-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
              <rect x="9" y="3" width="6" height="4" rx="1" />
              <line x1="9" y1="11" x2="15" y2="11" />
              <line x1="9" y1="15" x2="13" y2="15" />
            </svg>
          </div>
          <h2 className="rmp-gate-title">No 90-Day Roadmap Yet</h2>
          <p className="rmp-gate-sub">
            Your roadmap breaks your strategy into a concrete, week-by-week execution plan —
            so you know exactly what to do in months 1, 2, and 3 to build momentum.
          </p>
          <div className="rmp-gate-steps">
            <div className="rmp-gate-step">
              <span className={`rmp-step-badge${hasStrategy ? " rmp-step-done" : ""}`}>
                {hasStrategy ? "✓" : "1"}
              </span>
              <div className="rmp-step-body">
                <p className="rmp-step-title">Channel Strategy</p>
                <p className="rmp-step-sub">
                  {hasStrategy ? "Complete" : "Generate your channel strategy from the Strategy page first"}
                </p>
              </div>
            </div>
            <div className="rmp-gate-step">
              <span className="rmp-step-badge">2</span>
              <div className="rmp-step-body">
                <p className="rmp-step-title">Generate 90-Day Roadmap</p>
                <p className="rmp-step-sub">AI creates a phased execution plan with weekly priorities — ~25 seconds</p>
              </div>
            </div>
          </div>
          <button
            className="btn rmp-gate-cta"
            onClick={actions.generateRoadmap}
            disabled={state.busy || !state.activeProjectId}
          >
            Generate Roadmap →
          </button>
        </div>
        <NextStepCta to="/content" label="Next: Content Studio" disabled={true} />
      </div>
    );
  }

  /* ── Main page ────────────────────────────────────────────────────────── */
  return (
    <div className="rmp-page">
      <div className="rmp-header">
        <div className="rmp-header-text">
          <h3 className="rmp-title">90-Day Execution Roadmap</h3>
          <p className="rmp-desc">
            A phased, week-by-week plan to launch and grow your marketing — from quick wins in month 1
            through to compounding growth by month 3.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.generateRoadmap}
          disabled={state.busy || !state.activeProjectId}
        >
          {hasRoadmap ? "Regenerate Roadmap" : "Generate Roadmap"}
        </button>
      </div>

      {state.busy && (
        <LoadingSkeleton lines={6} message="Creating your 90-day roadmap…" />
      )}

      {!state.busy && hasRoadmap && (
        <RoadmapCards roadmap={state.roadmap} />
      )}

      <NextStepCta to="/content" label="Next: Content Studio" disabled={!hasRoadmap} />
    </div>
  );
}
