import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { PersonaCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";

export default function PersonasPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const hasPersonas = state.personas.length > 0;
  const isPrefetching = !hasPersonas && state.prefetch?.personas;
  const firstPersona = state.personas[0];
  const [traceOpen, setTraceOpen] = useState(false);

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
        {!hasPersonas && (
          <button
            className="btn"
            onClick={actions.generatePersonas}
            disabled={state.busy || isPrefetching || !state.activeProjectId}
          >
            Generate Personas
          </button>
        )}
      </div>

      {/* Gate error */}
      {state.gateError?.agent === "persona_builder" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {/* Background prefetch in progress */}
      {isPrefetching && !state.busy && (
        <LoadingSkeleton lines={6} message="Building your buyer personas in the background…" />
      )}

      {/* Manual generate loading */}
      {state.busy && (
        <LoadingSkeleton lines={6} message="Building your buyer personas…" />
      )}

      {/* Persona cards */}
      {!state.busy && !isPrefetching && hasPersonas && (
        <div className="pp-personas">
          <div className="pp-personas-meta">
            <span className="pp-personas-count">
              {state.personas.length} persona{state.personas.length !== 1 ? "s" : ""} generated
            </span>
            <AiChip />
            <TrustBadge score={firstPersona?.quality_score} />
            <span className="pp-personas-hint">
              Each persona is synthesised from your specific business data, location, and market context.
            </span>
          </div>
          <PersonaCards personas={state.personas} />
          <WhyThis reasoning={firstPersona?.reasoning} />

          {/* Generation trace */}
          {state.personaGenerationContext && (
            <div className="pp-trace-card">
              <button
                className="pp-trace-toggle"
                onClick={() => setTraceOpen((o) => !o)}
                aria-expanded={traceOpen}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points={traceOpen ? "18 15 12 9 6 15" : "6 9 12 15 18 9"} />
                </svg>
                How these personas were generated
                <span className="pp-trace-model">{state.personaGenerationContext.model}</span>
              </button>

              {traceOpen && (
                <div className="pp-trace-body">
                  {/* Agent steps */}
                  <p className="pp-trace-section-label">Agent steps</p>
                  <ol className="pp-trace-steps">
                    {state.personaGenerationContext.agent_steps.map((step, i) => (
                      <li key={i} className="pp-trace-step">
                        <span className="pp-trace-step-num">{i + 1}</span>
                        <span className="pp-trace-step-text">{step}</span>
                      </li>
                    ))}
                  </ol>

                  {/* Data sources */}
                  <p className="pp-trace-section-label" style={{ marginTop: "16px" }}>Data sources used</p>
                  <div className="pp-trace-sources">
                    {state.personaGenerationContext.data_sources.map((src, i) => (
                      <div key={i} className="pp-trace-source-row">
                        <span className="pp-trace-source-label">{src.label}</span>
                        <span className="pp-trace-source-detail">{src.detail}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div style={{ marginTop: "12px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="persona_builder" qualityScore={firstPersona?.quality_score} />
          </div>

          {/* Feedback + regenerate */}
          <div className="pp-refine-card">
            <p className="pp-refine-title">Refine These Personas</p>
            <p className="pp-refine-desc">
              Not quite right? Tell the AI what to change — e.g. "focus more on small business owners"
              or "remove the price-sensitive segment and add a premium buyer".
            </p>
            <textarea
              className="pp-refine-textarea"
              placeholder="e.g. Add a persona for eco-conscious millennials, make the third persona older (50+)…"
              value={state.personaFeedback}
              onChange={(e) => set.setPersonaFeedback(e.target.value)}
              rows={3}
            />
            <button
              className="btn"
              onClick={actions.generatePersonas}
              disabled={state.busy || !state.activeProjectId}
            >
              {state.busy ? "Regenerating…" : state.personaFeedback.trim() ? "Regenerate with Feedback →" : "Regenerate Personas →"}
            </button>
          </div>
        </div>
      )}

      <NextStepCta to="/research" label="Next: Research" disabled={!hasPersonas} />
    </div>
  );
}
