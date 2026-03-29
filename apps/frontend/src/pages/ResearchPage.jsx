import { NextStepCta } from "../components/UiBlocks";
import { ResearchCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function ResearchPage({ workflow }) {
  const { state, actions } = workflow;
  const hasResearch = !!state.research;
  const hasPersonas = state.personas?.length > 0;

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasResearch) {
    return (
      <div className="rsp-page">
        <div className="rsp-gate">
          <div className="rsp-gate-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
              <path d="M11 8v6M8 11h6" />
            </svg>
          </div>
          <h2 className="rsp-gate-title">No Market Research Yet</h2>
          <p className="rsp-gate-sub">
            Deep market research uncovers evidence-backed customer insights, emerging trends,
            and untapped opportunities — giving your strategy a competitive edge grounded in data.
          </p>
          <div className="rsp-gate-steps">
            <div className="rsp-gate-step">
              <span className={`rsp-step-badge${hasPersonas ? " rsp-step-done" : ""}`}>
                {hasPersonas ? "✓" : "1"}
              </span>
              <div className="rsp-step-body">
                <p className="rsp-step-title">Buyer Personas</p>
                <p className="rsp-step-sub">
                  {hasPersonas ? "Complete" : "Generate personas from the Personas page first"}
                </p>
              </div>
            </div>
            <div className="rsp-gate-step">
              <span className="rsp-step-badge">2</span>
              <div className="rsp-step-body">
                <p className="rsp-step-title">Run Deep Research</p>
                <p className="rsp-step-sub">AI scans for customer trends and market gaps — ~30 seconds</p>
              </div>
            </div>
          </div>
          <button
            className="btn rsp-gate-cta"
            onClick={actions.runResearch}
            disabled={state.busy || !state.activeProjectId}
          >
            Run Market Research →
          </button>
        </div>
        <NextStepCta to="/strategy" label="Next: Strategy" disabled={true} />
      </div>
    );
  }

  /* ── Main page ────────────────────────────────────────────────────────── */
  return (
    <div className="rsp-page">
      <div className="rsp-header">
        <div className="rsp-header-text">
          <h3 className="rsp-title">Market Research</h3>
          <p className="rsp-desc">
            Evidence-backed customer insights and market opportunities, researched specifically for
            your business type, location, and target audience.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.runResearch}
          disabled={state.busy || !state.activeProjectId}
        >
          {hasResearch ? "Re-run Research" : "Run Market Research"}
        </button>
      </div>

      {state.busy && (
        <LoadingSkeleton lines={5} message="Running deep market research…" />
      )}

      {!state.busy && hasResearch && (
        <ResearchCards research={state.research} />
      )}

      <NextStepCta to="/strategy" label="Next: Strategy" disabled={!hasResearch} />
    </div>
  );
}
