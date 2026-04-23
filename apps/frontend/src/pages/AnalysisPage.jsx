import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { CompetitorCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { WhyThis } from "../components/WhyThis";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";

/* ── StructuredMessage: parses free-text AI responses into blocks ─────── */
function StructuredMessage({ text }) {
  const clean = (s) =>
    String(s || "")
      .replace(/\*\*/g, "")
      .replace(/\s+/g, " ")
      .trim();

  const rawLines = String(text || "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  const lines = [];
  for (let i = 0; i < rawLines.length; i++) {
    const current = rawLines[i];
    const next = rawLines[i + 1] || "";
    if (/^\d+$/.test(current) && next) {
      lines.push(`${current}. ${clean(next)}`);
      i++;
      continue;
    }
    lines.push(clean(current));
  }

  const isBullet = (line) => /^([-*•]\s+|\d+[.)]\s+)/.test(line);
  const stripBullet = (line) => line.replace(/^([-*•]\s+|\d+[.)]\s+)/, "").trim();
  const stripMarkdownHeading = (line) => line.replace(/^#{1,3}\s*/, "").trim();
  const isMarkdownHeading = (line) => /^#{1,3}\s+/.test(line);
  const isHeading = (line, nextLine) => {
    if (!line) return false;
    if (isMarkdownHeading(line)) return true;
    if (line.endsWith(":")) return true;
    if (isBullet(line)) return false;
    if (/^[A-Za-z][A-Za-z0-9 /&-]{2,70}$/.test(line) && nextLine)
      return isBullet(nextLine) || nextLine.endsWith(":");
    return false;
  };

  const blocks = [];
  let currentBlock = { heading: "Response", items: [], paragraphs: [] };
  const pushCurrent = () => {
    if (currentBlock.items.length || currentBlock.paragraphs.length)
      blocks.push(currentBlock);
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const nextLine = lines[i + 1] || "";
    // Check bullets first — a line starting with "- " is always a bullet, never a heading
    if (isBullet(line)) { currentBlock.items.push(stripBullet(line)); continue; }
    if (isHeading(line, nextLine)) {
      pushCurrent();
      const headingText = isMarkdownHeading(line)
        ? stripMarkdownHeading(line)
        : line.replace(/:$/, "").trim();
      currentBlock = { heading: headingText, items: [], paragraphs: [] };
      continue;
    }
    const sentences = line.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
    if (sentences.length > 1 && !currentBlock.items.length)
      currentBlock.items.push(...sentences.map((s) => s.replace(/[.!?]$/, "")));
    else
      currentBlock.paragraphs.push(line);
  }
  pushCurrent();

  return (
    <div className="cb-structured">
      {blocks.map((b, idx) => (
        <div key={idx} className="cb-structured-block">
          {b.heading && <p className="cb-structured-heading">{b.heading}</p>}
          {b.items.length > 0 && (
            <ul className="cb-structured-list">
              {b.items.map((item, i) => (
                <li key={i}><span className="cb-bullet-dot" aria-hidden="true">•</span>{item}</li>
              ))}
            </ul>
          )}
          {b.paragraphs.map((p, i) => (
            <p key={i} className="cb-structured-para">{p}</p>
          ))}
        </div>
      ))}
    </div>
  );
}

function AiAvatar() {
  return (
    <div className="cb-avatar" aria-hidden="true">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74z" />
      </svg>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="cb-typing" aria-label="AI is thinking">
      <span /><span /><span />
    </div>
  );
}

const SAMPLE_QUESTIONS = [
  "Which competitor poses the highest threat and why?",
  "What are the 3 biggest gaps in my local market?",
  "How should I price my services vs these competitors?",
  "Which competitor's weaknesses can I exploit?",
  "What would make customers choose me over the top competitor?",
  "How saturated is my local market really?",
  "Which services should I add to stand out?",
  "Give me a SWOT based on this competitive landscape.",
];

const EMPTY_FEATURES = [
  "Local competitor profiles, pricing & reviews",
  "Price vs quality scatter map",
  "SWOT analysis vs the local market",
  "Hours gap — when competitors are closed",
  "Market opportunity gaps to exploit",
];

export default function AnalysisPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const assistantLogRef = useRef(null);

  const [suggestions, setSuggestions] = useState(() =>
    [...SAMPLE_QUESTIONS].sort(() => Math.random() - 0.5).slice(0, 4)
  );

  useEffect(() => {
    if (!assistantLogRef.current) return;
    assistantLogRef.current.scrollTop = assistantLogRef.current.scrollHeight;
  }, [state.analysisAssistantMessages.length, state.analysisAssistantBusy]);

  const sendMessage = () => actions.askAnalysisAssistant();

  /* ── Gate: interview not complete ─────────────────────────────────────── */
  if (!state.interviewCompleted) {
    return (
      <div className="cb-gate">
        <div className="cb-gate-icon" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>
        <h2 className="cb-gate-title">Complete Your Discovery Interview First</h2>
        <p className="cb-gate-sub">
          Competitive Benchmarking unlocks after the business interview — the AI needs your
          business type, location, and competitor context to accurately benchmark your local market.
        </p>
        <div className="cb-gate-steps">
          <div className="cb-gate-step cb-gate-step-done">
            <span className="cb-step-badge cb-step-done">✓</span>
            <div className="cb-step-body">
              <p className="cb-step-title">Business Profile Selected</p>
              <p className="cb-step-sub">Active project is set</p>
            </div>
          </div>
          <div className="cb-gate-step">
            <span className="cb-step-badge">2</span>
            <div className="cb-step-body">
              <p className="cb-step-title">Complete the Discovery Interview</p>
              <p className="cb-step-sub">Answer all questions and click "Complete Interview"</p>
            </div>
          </div>
          <div className="cb-gate-step">
            <span className="cb-step-badge">3</span>
            <div className="cb-step-body">
              <p className="cb-step-title">Return Here and Run Benchmarking</p>
              <p className="cb-step-sub">AI scans local competitors, pricing, reviews, and gaps</p>
            </div>
          </div>
        </div>
        <button className="btn" onClick={() => navigate("/questionnaire")}>
          Go to Marketing Discovery →
        </button>
      </div>
    );
  }

  /* ── Main page ─────────────────────────────────────────────────────────── */
  return (
    <div className="cb-page">

      {/* Gate error */}
      {state.gateError?.agent === "competitive_benchmarker" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {/* Action bar */}
      <div className="cb-action-bar">
        <div className="cb-action-info">
          <span className="cb-action-badge">Interview Complete</span>
          <p className="cb-action-sub">
            AI will scan local competitors, pricing, reviews, hours, and market gaps to build your report.
          </p>
        </div>
        <button
          className="btn"
          onClick={actions.runAnalysis}
          disabled={state.busy || !state.activeProjectId}
        >
          {state.busy
            ? "Scanning…"
            : state.analysis
              ? "Re-run Benchmarking"
              : "Run Competitive Benchmarking"}
        </button>
      </div>

      {/* Loading */}
      {state.busy && (
        <LoadingSkeleton lines={4} message="Scanning your local market and benchmarking competitors…" />
      )}

      {/* Empty — not yet run */}
      {!state.busy && !state.analysis && (
        <div className="cb-empty">
          <div className="cb-empty-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6"  y1="20" x2="6"  y2="14" />
            </svg>
          </div>
          <h3 className="cb-empty-title">No Benchmarking Data Yet</h3>
          <p className="cb-empty-sub">
            Click "Run Competitive Benchmarking" above to scan your local market.
          </p>
          <ul className="cb-empty-features">
            {EMPTY_FEATURES.map((f) => (
              <li key={f} className="cb-empty-feature">
                <span className="cb-empty-check" aria-hidden="true">✓</span>
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Results + assistant */}
      {!state.busy && state.analysis && (
        <>
        <div className="cb-layout">

          {/* Left: results */}
          <div className="cb-main">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
              <AiChip />
              <TrustBadge score={state.analysis?.quality_score} />
            </div>
            <CompetitorCards analysis={state.analysis} />
            <WhyThis reasoning={state.analysis?.reasoning} />
            <div style={{ marginTop: "12px" }}>
              <FeedbackThumbs projectId={state.activeProjectId} agent="competitive_benchmarker" qualityScore={state.analysis?.quality_score} />
            </div>
          </div>

          {/* Right: analysis assistant */}
          <aside className="cb-assistant">
            <div className="cb-assistant-head">
              <div className="cb-assistant-title-row">
                <span className="cb-assistant-title">Analysis Assistant</span>
                <span className="cb-assistant-live">Live</span>
              </div>
              <p className="cb-assistant-sub">
                Ask follow-up questions about competitors, pricing, or market gaps.
                Context here is used when you re-run the analysis.
              </p>
            </div>

            <div ref={assistantLogRef} className="cb-log">
              {/* Welcome bubble */}
              <div className="cb-row cb-row-bot">
                <AiAvatar />
                <div className="cb-bubble cb-bubble-bot">
                  <p>
                    I can help you interpret the competitor data, identify market gaps, and suggest
                    how to position against local competition. Pick a question or type your own.
                  </p>
                </div>
              </div>

              {state.analysisAssistantMessages.map((m, idx) => (
                <div key={`${m.role}-${idx}`}
                  className={`cb-row ${m.role === "assistant" ? "cb-row-bot" : "cb-row-user"}`}>
                  {m.role === "assistant" && <AiAvatar />}
                  <div className={`cb-bubble ${m.role === "assistant" ? "cb-bubble-bot" : "cb-bubble-user"}`}>
                    {m.role === "assistant"
                      ? <StructuredMessage text={m.content} />
                      : <p>{m.content}</p>}
                  </div>
                </div>
              ))}

              {state.analysisAssistantBusy && (
                <div className="cb-row cb-row-bot">
                  <AiAvatar />
                  <div className="cb-bubble cb-bubble-bot">
                    <TypingDots />
                  </div>
                </div>
              )}
            </div>

            <div className="cb-composer">
              {suggestions.length > 0 && (
                <div className="cb-chips">
                  {suggestions.map((q, idx) => (
                    <button
                      key={idx}
                      className="cb-chip"
                      disabled={state.analysisAssistantBusy}
                      onClick={() => {
                        setSuggestions((prev) => prev.filter((x) => x !== q));
                        actions.askAnalysisAssistant(q);
                      }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
              <div className="cb-composer-row">
                <textarea
                  rows={3}
                  placeholder="Ask about competitors, pricing gaps, win strategies…"
                  value={state.analysisAssistantInput}
                  onChange={(e) => set.setAnalysisAssistantInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!state.analysisAssistantBusy && state.analysisAssistantInput.trim())
                        sendMessage();
                    }
                  }}
                />
                <button
                  className="btn cb-send-btn"
                  onClick={sendMessage}
                  disabled={state.analysisAssistantBusy || !state.analysisAssistantInput.trim()}
                >
                  {state.analysisAssistantBusy ? "Asking…" : "Ask →"}
                </button>
              </div>
            </div>
          </aside>
        </div>
        <NextStepCta to="/positioning" label="Next: Positioning" disabled={false} />
        </>
      )}
    </div>
  );
}
