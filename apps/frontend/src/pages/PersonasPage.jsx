import { NextStepCta } from "../components/UiBlocks";
import { PersonaCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

export default function PersonasPage({ workflow }) {
  const { state, actions } = workflow;
  const hasPersonas = state.personas.length > 0;
  const prerequisitesMet = state.positioningHistory?.length > 0;

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasPersonas) {
    return (
      <div className="pp-page">
        <div className="pp-gate">
          <div className="pp-gate-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <h2 className="pp-gate-title">No Buyer Personas Yet</h2>
          <p className="pp-gate-sub">
            The AI builds detailed buyer personas by synthesising your positioning statement,
            competitive benchmarking data, and discovery interview — giving you rich profiles
            of the customers most likely to convert.
          </p>
          <div className="pp-gate-steps">
            <div className="pp-gate-step">
              <span className={`pp-step-badge${state.interviewCompleted ? " pp-step-done" : ""}`}>
                {state.interviewCompleted ? "✓" : "1"}
              </span>
              <div className="pp-step-body">
                <p className="pp-step-title">Discovery Interview</p>
                <p className="pp-step-sub">
                  {state.interviewCompleted ? "Complete" : "Answer all questions and click Complete Interview"}
                </p>
              </div>
            </div>
            <div className="pp-gate-step">
              <span className={`pp-step-badge${state.analysis ? " pp-step-done" : ""}`}>
                {state.analysis ? "✓" : "2"}
              </span>
              <div className="pp-step-body">
                <p className="pp-step-title">Competitive Benchmarking</p>
                <p className="pp-step-sub">
                  {state.analysis ? "Complete" : "Run competitor analysis from the Benchmarking page"}
                </p>
              </div>
            </div>
            <div className="pp-gate-step">
              <span className={`pp-step-badge${prerequisitesMet ? " pp-step-done" : ""}`}>
                {prerequisitesMet ? "✓" : "3"}
              </span>
              <div className="pp-step-body">
                <p className="pp-step-title">Positioning Statement</p>
                <p className="pp-step-sub">
                  {prerequisitesMet ? "Complete" : "Generate your positioning from the Positioning page"}
                </p>
              </div>
            </div>
            <div className="pp-gate-step">
              <span className="pp-step-badge">4</span>
              <div className="pp-step-body">
                <p className="pp-step-title">Generate Personas</p>
                <p className="pp-step-sub">Click the button below — AI generates 3–5 personas in ~25 seconds</p>
              </div>
            </div>
          </div>
          <button
            className="btn pp-gate-cta"
            onClick={actions.generatePersonas}
            disabled={state.busy || !state.activeProjectId}
          >
            Generate Personas →
          </button>
        </div>
        <NextStepCta to="/research" label="Next: Research" disabled={true} />
      </div>
    );
  }

  /* ── Main page ────────────────────────────────────────────────────────── */
  return (
    <div className="pp-page">
      {/* Page header */}
      <div className="pp-header">
        <div className="pp-header-text">
          <h3 className="pp-title">Buyer Personas</h3>
          <p className="pp-desc">
            Detailed profiles of your most valuable customer segments — built from your real business data.
            Use these to shape messaging, channel selection, and content strategy.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.generatePersonas}
          disabled={state.busy || !state.activeProjectId}
        >
          {hasPersonas ? "Regenerate Personas" : "Generate Personas"}
        </button>
      </div>

      {/* Loading */}
      {state.busy && (
        <LoadingSkeleton lines={6} message="Building your buyer personas…" />
      )}

      {/* Persona cards */}
      {!state.busy && hasPersonas && (
        <div className="pp-personas">
          <div className="pp-personas-meta">
            <span className="pp-personas-count">
              {state.personas.length} persona{state.personas.length !== 1 ? "s" : ""} generated
            </span>
            <span className="pp-personas-hint">
              Each persona is synthesised from your specific business data, location, and market context.
            </span>
          </div>
          <PersonaCards personas={state.personas} />
        </div>
      )}

      <NextStepCta to="/research" label="Next: Research" disabled={!hasPersonas} />
    </div>
  );
}
