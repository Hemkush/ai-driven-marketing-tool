import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { ResearchCards } from "../components/cards/ResearchCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";
import { GhostPreviewResearch } from "../components/GhostPreview";
import { ScanSearch } from "lucide-react";

function FocusInput({ value, onChange, onRun, busy, hasResearch }) {
  return (
    <div className="rsp-focus-card">
      <div className="rsp-focus-header">
        <span className="rsp-focus-badge">Optional</span>
        <p className="rsp-focus-label">
          {hasResearch ? "Refocus the research" : "Focus this research"}
        </p>
      </div>
      <p className="rsp-focus-hint">
        Direct the AI toward a specific angle — e.g. Instagram marketing, the premium segment, or a particular competitor. Leave blank for a broad overview.
      </p>
      <div className="rsp-focus-row">
        <input
          className="rsp-focus-input"
          type="text"
          placeholder="e.g. Instagram marketing, weekend customers…"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !busy && onRun()}
        />
        <button
          className="btn rsp-focus-btn"
          onClick={onRun}
          disabled={busy}
        >
          {busy
            ? "Running…"
            : hasResearch
            ? value.trim() ? "Re-run with Focus →" : "Re-run Research →"
            : value.trim() ? "Run with Focus →" : "Run Research →"}
        </button>
      </div>
    </div>
  );
}

export default function ResearchPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const hasResearch = !!state.research;
  const hasPersonas = state.personas?.length > 0;

  /* ── Prefetch in progress ─────────────────────────────────────────────── */
  if (state.prefetch.research && !hasResearch) {
    return (
      <div className="rsp-page">
        <LoadingSkeleton lines={5} message="Preparing your market research in the background…" />
      </div>
    );
  }

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasResearch) {
    return (
      <div className="rsp-page">
        {state.gateError?.agent === "market_researcher" && (
          <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
            <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
              ⚠ {state.gateError.message}
            </p>
            <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
              Back to Questionnaire →
            </button>
          </div>
        )}
        <div style={{ position: "relative", marginBottom: "24px" }}>
          <div className="gp-wrap" style={{ position: "absolute", inset: 0, zIndex: 0, filter: "blur(6px) saturate(0.4)", opacity: 0.35, overflow: "hidden", pointerEvents: "none", userSelect: "none" }}>
            <GhostPreviewResearch />
          </div>
          <div style={{ position: "relative", zIndex: 1 }}>
            <div className="rsp-gate">
              <div className="rsp-gate-icon" aria-hidden="true">
                <ScanSearch size={28} strokeWidth={1.8} />
              </div>
              <h2 className="rsp-gate-title">No Market Research Yet</h2>
              <p className="rsp-gate-sub">
                Deep market research uncovers evidence-backed customer insights, buying journeys per
                persona, quick wins, and untapped opportunities — giving your strategy a competitive
                edge grounded in data.
              </p>
              <div className="rsp-gate-steps">
                <div className="rsp-gate-step">
                  <span className={`rsp-step-badge${hasPersonas ? " rsp-step-done" : ""}`}>
                    {hasPersonas ? "✓" : "1"}
                  </span>
                  <div className="rsp-step-body">
                    <p className="rsp-step-title">Buyer Personas</p>
                    <p className="rsp-step-sub">
                      {hasPersonas
                        ? `Complete — ${state.personas.length} persona${state.personas.length !== 1 ? "s" : ""} will be used to personalise research`
                        : "Generate personas from the Personas page first"}
                    </p>
                  </div>
                </div>
                <div className="rsp-gate-step">
                  <span className="rsp-step-badge">2</span>
                  <div className="rsp-step-body">
                    <p className="rsp-step-title">Run Deep Research</p>
                    <p className="rsp-step-sub">
                      AI produces buying journeys per persona, quick wins, and market insights — ~30 seconds
                    </p>
                  </div>
                </div>
              </div>
              <button
                className="btn"
                onClick={actions.runResearch}
                disabled={state.busy}
                style={{ marginTop: "8px" }}
              >
                Run Research →
              </button>
            </div>
          </div>
        </div>
        <NextStepCta to="/roadmap" label="Next: Roadmap" disabled={true} />
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
            Evidence-backed customer insights, per-persona buying journeys, and actionable
            quick wins — researched specifically for your business type, location, and audience.
          </p>
        </div>
      </div>

      {/* Gate error */}
      {state.gateError?.agent === "market_researcher" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {/* Focus / re-run control */}
      <FocusInput
        value={state.researchFocus}
        onChange={set.setResearchFocus}
        onRun={actions.runResearch}
        busy={state.busy}
        hasResearch={hasResearch}
      />

      {state.busy && (
        <LoadingSkeleton lines={5} message="Running deep market research…" />
      )}

      {!state.busy && hasResearch && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
            <AiChip />
            <TrustBadge score={state.research?.quality_score} />
          </div>
          <ResearchCards research={state.research} />
          <WhyThis reasoning={state.research?.reasoning} />
          <div style={{ marginTop: "12px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="market_researcher" qualityScore={state.research?.quality_score} />
          </div>
        </>
      )}

      <NextStepCta to="/roadmap" label="Next: Roadmap" disabled={!hasResearch} />
    </div>
  );
}
