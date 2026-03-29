import { NextStepCta } from "../components/UiBlocks";
import { StrategyCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function StrategyPage({ workflow }) {
  const { state, actions } = workflow;
  const hasStrategy = !!state.strategy;
  const hasPersonas = state.personas?.length > 0;

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasStrategy) {
    return (
      <div className="stp-page">
        <div className="stp-gate">
          <div className="stp-gate-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="4" rx="1" />
              <rect x="3" y="10" width="13" height="4" rx="1" />
              <rect x="3" y="17" width="8" height="4" rx="1" />
            </svg>
          </div>
          <h2 className="stp-gate-title">No Channel Strategy Yet</h2>
          <p className="stp-gate-sub">
            Your channel strategy maps out exactly which marketing channels to use, how to use them,
            and in what priority — tailored to your audience, budget, and competitive position.
          </p>
          <div className="stp-gate-steps">
            <div className="stp-gate-step">
              <span className={`stp-step-badge${hasPersonas ? " stp-step-done" : ""}`}>
                {hasPersonas ? "✓" : "1"}
              </span>
              <div className="stp-step-body">
                <p className="stp-step-title">Buyer Personas</p>
                <p className="stp-step-sub">
                  {hasPersonas ? "Complete" : "Generate personas from the Personas page first"}
                </p>
              </div>
            </div>
            <div className="stp-gate-step">
              <span className="stp-step-badge">2</span>
              <div className="stp-step-body">
                <p className="stp-step-title">Generate Channel Strategy</p>
                <p className="stp-step-sub">AI builds a prioritised channel playbook specific to your market — ~25 seconds</p>
              </div>
            </div>
          </div>
          <button
            className="btn stp-gate-cta"
            onClick={actions.generateStrategy}
            disabled={state.busy || !state.activeProjectId}
          >
            Generate Strategy →
          </button>
        </div>
        <NextStepCta to="/roadmap" label="Next: Roadmap" disabled={true} />
      </div>
    );
  }

  /* ── Main page ────────────────────────────────────────────────────────── */
  return (
    <div className="stp-page">
      <div className="stp-header">
        <div className="stp-header-text">
          <h3 className="stp-title">Channel Strategy</h3>
          <p className="stp-desc">
            A prioritised marketing channel playbook — showing where to focus, how to show up,
            and what tactics will drive the highest return for your business.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.generateStrategy}
          disabled={state.busy || !state.activeProjectId}
        >
          {hasStrategy ? "Regenerate Strategy" : "Generate Strategy"}
        </button>
      </div>

      {state.busy && (
        <LoadingSkeleton lines={5} message="Building your channel strategy…" />
      )}

      {!state.busy && hasStrategy && (
        <StrategyCards strategy={state.strategy} />
      )}

      <NextStepCta to="/roadmap" label="Next: Roadmap" disabled={!hasStrategy} />
    </div>
  );
}
