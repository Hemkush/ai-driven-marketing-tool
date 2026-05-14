import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { RoadmapCards } from "../components/cards/RoadmapCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";
import { GhostPreviewRoadmap } from "../components/GhostPreview";
import { ClipboardList, Copy, Printer } from "lucide-react";

function roadmapToText(roadmap) {
  if (!roadmap?.phases) return "";
  return roadmap.phases
    .map((phase) => {
      const weeks = (phase.weeks || [])
        .map((w) => `  Week ${w.week}: ${w.action}`)
        .join("\n");
      return `${phase.phase}\n${weeks}`;
    })
    .join("\n\n");
}

function ExportBar({ roadmap }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(roadmapToText(roadmap));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard blocked */
    }
  };

  return (
    <div className="export-btn-group" style={{ marginBottom: "12px" }}>
      <button
        className={`export-btn${copied ? " export-btn-copied" : ""}`}
        onClick={handleCopy}
        title="Copy roadmap as text"
      >
        <Copy size={13} strokeWidth={2} />
        {copied ? "Copied!" : "Copy"}
      </button>
      <button
        className="export-btn"
        onClick={() => window.print()}
        title="Print or save as PDF"
      >
        <Printer size={13} strokeWidth={2} />
        Print / PDF
      </button>
    </div>
  );
}

export default function RoadmapPage({ workflow }) {
  const { state, actions } = workflow;
  const navigate = useNavigate();
  const hasRoadmap = !!state.roadmap;
  const hasPersonas = state.personas.length > 0;

  /* ── Prefetch in progress ─────────────────────────────────────────────── */
  if (state.prefetch.roadmap && !hasRoadmap) {
    return (
      <div className="rmp-page">
        <LoadingSkeleton lines={6} message="Preparing your 90-day roadmap in the background…" />
      </div>
    );
  }

  /* ── Gate / empty state ───────────────────────────────────────────────── */
  if (!state.busy && !hasRoadmap) {
    return (
      <div className="rmp-page">
        {state.gateError?.agent === "roadmap_planner" && (
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
            <GhostPreviewRoadmap />
          </div>
          <div style={{ position: "relative", zIndex: 1 }}>
            <div className="rmp-gate">
              <div className="rmp-gate-icon" aria-hidden="true">
                <ClipboardList size={28} strokeWidth={1.8} />
              </div>
              <h2 className="rmp-gate-title">No 90-Day Roadmap Yet</h2>
              <p className="rmp-gate-sub">
                Your roadmap turns your personas and positioning into a concrete, week-by-week execution plan —
                so you know exactly what to do in months 1, 2, and 3 to build momentum.
              </p>
              <div className="rmp-gate-steps">
                <div className="rmp-gate-step">
                  <span className={`rmp-step-badge${hasPersonas ? " rmp-step-done" : ""}`}>
                    {hasPersonas ? "✓" : "1"}
                  </span>
                  <div className="rmp-step-body">
                    <p className="rmp-step-title">Buyer Personas</p>
                    <p className="rmp-step-sub">
                      {hasPersonas ? "Complete" : "Generate personas from the Personas page first"}
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
          </div>
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

      {/* Gate error */}
      {state.gateError?.agent === "roadmap_planner" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {state.busy && (
        <LoadingSkeleton lines={6} message="Creating your 90-day roadmap…" />
      )}

      {!state.busy && hasRoadmap && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
            <AiChip />
            <TrustBadge score={state.roadmap?.quality_score} />
            <div style={{ marginLeft: "auto" }}>
              <ExportBar roadmap={state.roadmap} />
            </div>
          </div>
          <RoadmapCards roadmap={state.roadmap} />
          <WhyThis reasoning={state.roadmap?.reasoning} />
          <div style={{ marginTop: "12px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="roadmap_planner" qualityScore={state.roadmap?.quality_score} />
          </div>
        </>
      )}

      <NextStepCta to="/content" label="Next: Content Studio" disabled={!hasRoadmap} />
    </div>
  );
}
