import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ActionRow, NextStepCta } from "../components/UiBlocks";
import { CompetitorCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

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

  // Normalize split numbered lines:
  // "1" + "**Launch ...** - ..." => "1. Launch ... - ..."
  const lines = [];
  for (let i = 0; i < rawLines.length; i += 1) {
    const current = rawLines[i];
    const next = rawLines[i + 1] || "";
    if (/^\d+$/.test(current) && next) {
      lines.push(`${current}. ${clean(next)}`);
      i += 1;
      continue;
    }
    lines.push(clean(current));
  }

  const isBullet = (line) => /^([-*•]\s+|\d+[.)]\s+)/.test(line);
  const stripBullet = (line) => line.replace(/^([-*•]\s+|\d+[.)]\s+)/, "").trim();
  const isHeading = (line, nextLine) => {
    if (!line) return false;
    if (line.endsWith(":")) return true;
    if (isBullet(line)) return false;
    // Single-line heading style like "Summary" or "Recommended Actions"
    if (/^[A-Za-z][A-Za-z0-9 /&-]{2,70}$/.test(line) && nextLine) {
      return isBullet(nextLine) || nextLine.endsWith(":");
    }
    return false;
  };

  const blocks = [];
  let currentBlock = { heading: "Response", items: [], paragraphs: [] };

  const pushCurrent = () => {
    if (currentBlock.items.length || currentBlock.paragraphs.length) {
      blocks.push(currentBlock);
    }
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const nextLine = lines[i + 1] || "";
    if (isHeading(line, nextLine)) {
      pushCurrent();
      currentBlock = {
        heading: line.replace(/:$/, "").trim(),
        items: [],
        paragraphs: [],
      };
      continue;
    }
    if (isBullet(line)) {
      currentBlock.items.push(stripBullet(line));
      continue;
    }
    // Convert long free text into list-like chunks where possible.
    const sentences = line
      .split(/(?<=[.!?])\s+/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (sentences.length > 1 && !currentBlock.items.length) {
      currentBlock.items.push(...sentences.map((s) => s.replace(/[.!?]$/, "")));
    } else {
      currentBlock.paragraphs.push(line);
    }
  }
  pushCurrent();

  return (
    <div className="structured-msg">
      {blocks.map((b, idx) => (
        <div key={`blk-${idx}`} className="structured-block">
          {b.heading ? <p className="structured-heading">{b.heading}</p> : null}
          {Array.isArray(b.items) && b.items.length ? (
            <ul className="structured-list">
              {b.items.map((item, itemIdx) => (
                <li key={`it-${idx}-${itemIdx}`}>{item}</li>
              ))}
            </ul>
          ) : null}
          {Array.isArray(b.paragraphs) && b.paragraphs.length
            ? b.paragraphs.map((p, pIdx) => (
                <p key={`p-${idx}-${pIdx}`} className="structured-para">
                  {p}
                </p>
              ))
            : null}
        </div>
      ))}
    </div>
  );
}

export default function AnalysisPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const assistantLogRef = useRef(null);
  const analysisMainRef = useRef(null);
  const [assistantMaxHeight, setAssistantMaxHeight] = useState(null);
  const sampleQuestions = useMemo(() => {
    const pool = [
      "Which competitor poses the highest threat and why?",
      "What are the 3 biggest gaps in my local market?",
      "How should I price my services compared to these competitors?",
      "Which competitor's weaknesses can I exploit?",
      "What would make customers choose me over the top competitor?",
      "How saturated is my local market really?",
      "Which services should I add to stand out?",
      "Give me a SWOT based on the competitive landscape.",
    ];
    const shuffled = [...pool].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 4);
  }, [state.analysis?.segment_attractiveness_analysis?.recommended_primary_segment, state.analysis?.analysis_source]);
  const [suggestions, setSuggestions] = useState(sampleQuestions);
  const assistantCount = state.analysisAssistantMessages.length;
  const assistantSizeClass = assistantCount > 10 ? "tall" : assistantCount > 3 ? "mid" : "short";

  useEffect(() => {
    if (!assistantLogRef.current) return;
    assistantLogRef.current.scrollTop = assistantLogRef.current.scrollHeight;
  }, [state.analysisAssistantMessages.length]);

  useEffect(() => {
    const measure = () => {
      if (!analysisMainRef.current || !state.analysis) {
        setAssistantMaxHeight(null);
        return;
      }
      const reportEl = analysisMainRef.current.querySelector(".analysis-report-box");
      if (!reportEl) {
        setAssistantMaxHeight(null);
        return;
      }
      const h = Math.max(420, reportEl.offsetHeight);
      setAssistantMaxHeight(h);
    };

    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [state.analysis, state.analysisAssistantMessages.length]);

  useEffect(() => {
    setSuggestions(sampleQuestions);
  }, [sampleQuestions]);

  const sendAssistantMessage = () => actions.askAnalysisAssistant();

  return (
    <div className="analysis-page">
      {!state.interviewCompleted ? (
        <section className="compact-card analysis-gate">
          <h4>Complete Marketing Discovery First</h4>
          <p className="page-subtitle">
            Competitive Benchmarking is unlocked after you finish the interview so the model has
            enough business, location, competitor, and budget context to benchmark your local market.
          </p>
          <div className="analysis-gate-steps">
            <div className="analysis-gate-step">
              <span className="analysis-gate-num">1</span>
              <span>Open the Marketing Discovery page.</span>
            </div>
            <div className="analysis-gate-step">
              <span className="analysis-gate-num">2</span>
              <span>Answer the interview questions and finish the session.</span>
            </div>
            <div className="analysis-gate-step">
              <span className="analysis-gate-num">3</span>
              <span>Return here and click Run Competitive Benchmarking.</span>
            </div>
          </div>
          <div className="action-row">
            <button type="button" className="btn" onClick={() => navigate("/questionnaire")}>
              Go To Marketing Discovery
            </button>
          </div>
        </section>
      ) : null}
      {state.interviewCompleted ? (
        <ActionRow>
          <button
            type="button"
            className="btn"
            onClick={actions.runAnalysis}
            disabled={state.busy || !state.activeProjectId || !state.interviewCompleted}
          >
            Run Competitive Benchmarking
          </button>
        </ActionRow>
      ) : null}
      <div className={`analysis-layout ${state.analysis ? "" : "single"}`.trim()}>
        <div ref={analysisMainRef} className="analysis-main">
          {state.busy && <LoadingSkeleton lines={4} />}
          {!state.busy && state.analysis && <CompetitorCards analysis={state.analysis} />}
          {!state.busy && !state.analysis && state.interviewCompleted && (
            <section className="compact-card analysis-empty">
              <h4>Competitive Benchmarking Not Run Yet</h4>
              <p className="page-subtitle">
                Your interview is complete. Run the benchmarking report to see local competitors,
                their pricing, services, business models, discounts, reviews, and area market size.
              </p>
              <div className="analysis-empty-points">
                <div className="analysis-empty-point">
                  <span className="analysis-empty-dot">OK</span>
                  <span>Market Discovery interview completed</span>
                </div>
                <div className="analysis-empty-point">
                  <span className="analysis-empty-dot">1</span>
                  <span>Click <b>Run Competitive Benchmarking</b> above</span>
                </div>
                <div className="analysis-empty-point">
                  <span className="analysis-empty-dot">2</span>
                  <span>Review competitor profiles and ask follow-up questions in the assistant</span>
                </div>
              </div>
            </section>
          )}
          {state.interviewCompleted ? (
            <NextStepCta to="/positioning" label="Next: Positioning" disabled={!state.analysis} />
          ) : null}
        </div>
        {state.analysis && (
          <aside
            className={`compact-card analysis-assistant ${assistantSizeClass}`}
            style={assistantMaxHeight ? { maxHeight: `${assistantMaxHeight}px` } : undefined}
          >
            <div className="analysis-assistant-head">
              <h4>Analysis Assistant</h4>
              <span className="assistant-live">Live</span>
              <p className="page-subtitle">
                Ask follow-up questions. New context here is used when you rerun analysis.
              </p>
            </div>
            <div ref={assistantLogRef} className={`analysis-assistant-log ${assistantSizeClass}`}>
              <div className="chat-row bot">
                <div className="chat-avatar">AI</div>
                <div className="chat-bubble bot">
                  <div className="chat-label">Assistant</div>
                  <p>
                    Welcome. I can help you interpret the competitor data, identify market gaps,
                    and suggest how to position against local competition. Choose a sample question or type your own.
                  </p>
                </div>
              </div>
              {state.analysisAssistantMessages.map((m, idx) => (
                <div key={`${m.role}-${idx}`} className={m.role === "assistant" ? "chat-row bot" : "chat-row user"}>
                  {m.role === "assistant" && <div className="chat-avatar">AI</div>}
                  <div className={`chat-bubble ${m.role === "assistant" ? "bot" : "user"}`}>
                    <div className="chat-label">
                      {m.role === "assistant" ? `Assistant (${m.source || "ai"})` : "You"}
                    </div>
                    {m.role === "assistant" ? (
                      <StructuredMessage text={m.content} />
                    ) : (
                      <p>{m.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {state.analysisAssistantBusy && (
                <div className="chat-row bot">
                  <div className="chat-avatar">AI</div>
                  <div className="chat-bubble bot">
                    <div className="chat-label">Assistant</div>
                    <p className="assistant-typing">Thinking...</p>
                  </div>
                </div>
              )}
            </div>
            <div className="chat-composer analysis-assistant-composer">
              <label htmlFor="analysis-assistant-input">Ask about this analysis</label>
              <div className="assistant-sample-wrap">
                {suggestions.map((q, idx) => (
                  <button
                    key={`sample-q-${idx}`}
                    type="button"
                    className="assistant-sample-btn"
                    disabled={state.analysisAssistantBusy}
                    onClick={() => {
                      setSuggestions((prev) => prev.filter((x) => x !== q));
                      actions.askAnalysisAssistant(q);
                    }}
                    title={q}
                  >
                    {q}
                  </button>
                ))}
              </div>
              <textarea
                id="analysis-assistant-input"
                rows={3}
                placeholder="Example: Which competitor should I worry about most? What pricing gap can I exploit? How do I win in this market?"
                value={state.analysisAssistantInput}
                onChange={(e) => set.setAnalysisAssistantInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (!state.analysisAssistantBusy && state.analysisAssistantInput.trim()) {
                      sendAssistantMessage();
                    }
                  }
                }}
              />
              <div className="wizard-nav">
                <button
                  type="button"
                  className="btn"
                  onClick={sendAssistantMessage}
                  disabled={state.analysisAssistantBusy || !state.analysisAssistantInput.trim()}
                >
                  {state.analysisAssistantBusy ? "Asking..." : "Ask Assistant"}
                </button>
              </div>
              <p className="assistant-hint">Press Enter to send. Shift + Enter for a new line.</p>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
