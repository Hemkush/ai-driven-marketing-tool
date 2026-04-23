import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { PersonaCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";

export default function PersonasPage({ workflow }) {
  const { state, actions } = workflow;
  const navigate = useNavigate();
  const hasPersonas = state.personas.length > 0;
  const isPrefetching = !hasPersonas && state.prefetch?.personas;
  const firstPersona = state.personas[0];

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
          disabled={state.busy || isPrefetching || !state.activeProjectId}
        >
          {hasPersonas ? "Regenerate Personas" : "Generate Personas"}
        </button>
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
          <div style={{ marginTop: "12px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="persona_builder" qualityScore={firstPersona?.quality_score} />
          </div>
        </div>
      )}

      <NextStepCta to="/research" label="Next: Research" disabled={!hasPersonas} />
    </div>
  );
}
