import { useEffect, useMemo, useRef, useState } from "react";

const TOPICS = [
  { num: "01", label: "Your business — what you do and who you serve" },
  { num: "02", label: "Your ideal customers and buying triggers" },
  { num: "03", label: "Competitors and your market position" },
  { num: "04", label: "Budget, pricing, and growth targets" },
  { num: "05", label: "Marketing channels and execution plan" },
];

const DOT_COUNT = 8;

function TypingDots() {
  return (
    <div className="qp-typing" aria-label="AI is thinking">
      <span /><span /><span />
    </div>
  );
}

function AiAvatar() {
  return (
    <div className="qp-avatar" aria-hidden="true">
      {/* sparkle / star mark */}
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74z" />
      </svg>
    </div>
  );
}

function MessageBubble({ item }) {
  if (item.role === "assistant") {
    return (
      <div className="qp-row qp-row-bot">
        <AiAvatar />
        <div className="qp-bubble qp-bubble-bot">
          <p>{item.question_text}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="qp-row qp-row-user">
      <div className="qp-bubble qp-bubble-user">
        <p>{item.answer_text}</p>
      </div>
    </div>
  );
}

function toTitleCase(str) {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function QuestionnaireChatPanel({
  busy,
  activeProjectId,
  messages,
  sessionId,
  analysis,
  startChat,
  refreshChat,
  sendReply,
  finishChat,
  interviewCompleted = false,
}) {
  const [draft, setDraft] = useState("");
  const [confirmRestart, setConfirmRestart] = useState(false);
  const chatLogRef = useRef(null);

  const latestAssistant = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant") return messages[i];
    }
    return null;
  }, [messages]);

  const answeredCount = messages.filter((m) => m.role === "user").length;
  const filledDots = Math.min(answeredCount, DOT_COUNT);

  useEffect(() => {
    if (!chatLogRef.current) return;
    chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
  }, [messages.length, busy]);

  const onSend = async () => {
    const text = draft.trim();
    if (!text) return;
    await sendReply(text);
    setDraft("");
  };

  const doRestart = async () => {
    setConfirmRestart(false);
    await refreshChat();
    setDraft("");
  };

  /* ── Start screen ────────────────────────────────────────────────────── */
  if (!sessionId) {
    return (
      <div className="qp-start">
        <div className="qp-start-icon" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>

        <div className="qp-start-head">
          <h2 className="qp-start-title">Marketing Discovery Interview</h2>
          <span className="qp-start-badge">~10 min</span>
        </div>

        <p className="qp-start-sub">
          Before we build your marketing strategy, we need to deeply understand your business.
          The AI interviewer asks one question at a time and adapts based on your answers — no long forms, no guesswork.
        </p>

        <div className="qp-topics-wrap">
          <p className="qp-topics-label">What we'll cover</p>
          <ul className="qp-topics">
            {TOPICS.map((t) => (
              <li key={t.num} className="qp-topic-item">
                <span className="qp-topic-num">{t.num}</span>
                <span className="qp-topic-text">{t.label}</span>
              </li>
            ))}
          </ul>
        </div>

        <button
          className="btn qp-start-btn"
          onClick={startChat}
          disabled={busy || !activeProjectId}
        >
          {busy ? "Starting…" : "Begin Interview →"}
        </button>

        {!activeProjectId && (
          <p className="qp-start-warn">Select a business profile first to begin.</p>
        )}
      </div>
    );
  }

  /* ── Active interview ────────────────────────────────────────────────── */
  return (
    <div className="qp-root">
      {/* Progress strip */}
      <div className="qp-progress-strip">
        <div className="qp-progress-left">
          <span className="qp-progress-label">
            {answeredCount === 0
              ? "Waiting for your first answer"
              : `${answeredCount} question${answeredCount !== 1 ? "s" : ""} answered`}
          </span>
          <div className="qp-progress-dots" aria-hidden="true">
            {Array.from({ length: DOT_COUNT }).map((_, i) => (
              <span key={i} className={`qp-dot${i < filledDots ? " filled" : ""}`} />
            ))}
          </div>
        </div>

        <div className="qp-progress-right">
          {interviewCompleted ? (
            <div className="qp-completed-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Interview Complete
            </div>
          ) : confirmRestart ? (
            <div className="qp-restart-confirm">
              <span className="qp-restart-confirm-text">Clear conversation and restart?</span>
              <button className="btn ghost qp-confirm-btn" onClick={() => setConfirmRestart(false)}>
                Cancel
              </button>
              <button className="btn qp-confirm-btn qp-confirm-danger" onClick={doRestart}>
                Yes, Restart
              </button>
            </div>
          ) : (
            <>
              <button
                className="btn ghost qp-restart-btn"
                onClick={() => setConfirmRestart(true)}
                disabled={busy}
              >
                Restart
              </button>
              <button
                className="btn qp-finish-btn"
                onClick={() => finishChat(false)}
                disabled={busy || !sessionId}
              >
                Complete Interview →
              </button>
            </>
          )}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="qp-layout">
        {/* Left: Live Analysis */}
        <aside className="qp-analysis">
          <div className="qp-analysis-head">
            <p className="qp-analysis-kicker">Live Analysis</p>
            <p className="qp-analysis-sub">Updated after each answer</p>
          </div>

          {!analysis ? (
            <div className="qp-analysis-empty">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                className="qp-analysis-empty-icon">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4M12 8h.01" />
              </svg>
              <p>Answer the first question to unlock real-time business analysis and marketing insights.</p>
            </div>
          ) : (
            <>
              <p className="qp-analysis-summary">{analysis.summary}</p>

              <div className="qp-analysis-meta">
                <span className={`chip ${analysis.confidence === "high" ? "accepted" : analysis.confidence === "medium" ? "manual" : "rejected"}`}>
                  {analysis.confidence} confidence
                </span>
                {analysis.business_location && analysis.business_location !== "Not provided" && (
                  <span className="qp-analysis-loc">📍 {analysis.business_location}</span>
                )}
                {analysis.geographical_range && analysis.geographical_range !== "Not provided" && (
                  <span className="qp-analysis-loc qp-analysis-range">🗺 {analysis.geographical_range}</span>
                )}
              </div>

              {Object.keys(analysis.understanding || {}).length > 0 && (
                <div className="qp-section">
                  <p className="qp-section-label">Understanding</p>
                  <div className="qp-understanding-grid">
                    {Object.entries(analysis.understanding).map(([k, v]) => (
                      <div key={k} className="qp-u-row">
                        <span className="qp-u-key">{toTitleCase(k)}</span>
                        <span className={`chip ${v === "defined" ? "accepted" : v === "partial" ? "manual" : "rejected"}`}>
                          {v}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(analysis.important_points || []).length > 0 && (
                <div className="qp-section">
                  <p className="qp-section-label">Key Points</p>
                  <ul className="qp-insight-list">
                    {analysis.important_points.map((pt, i) => <li key={i}>{pt}</li>)}
                  </ul>
                </div>
              )}

              {(analysis.marketing_insights || []).length > 0 && (
                <div className="qp-section">
                  <p className="qp-section-label">Marketing Signals</p>
                  <ul className="qp-insight-list">
                    {analysis.marketing_insights.map((ins, i) => <li key={i}>{ins}</li>)}
                  </ul>
                </div>
              )}
            </>
          )}
        </aside>

        {/* Right: Chat */}
        <div className="qp-chat">
          <div className="qp-chat-head">
            <span className="qp-chat-title">Conversation</span>
            <span className="qp-chat-status">
              {busy
                ? "Analyzing your response…"
                : answeredCount > 0
                  ? `${answeredCount} response${answeredCount !== 1 ? "s" : ""} captured`
                  : "Waiting for your first answer"}
            </span>
          </div>

          <div ref={chatLogRef} className="qp-log">
            {messages.length === 0 && !busy && (
              <p className="qp-log-empty">Your interview conversation will appear here.</p>
            )}
            {messages.map((item, idx) => (
              <MessageBubble key={`${item.role}-${item.response_id ?? idx}-${idx}`} item={item} />
            ))}
            {/* Typing indicator — only after conversation has started */}
            {busy && messages.length > 0 && (
              <div className="qp-row qp-row-bot">
                <AiAvatar />
                <div className="qp-bubble qp-bubble-bot">
                  <TypingDots />
                </div>
              </div>
            )}
          </div>

          {/* Hint banner — pinned above composer, visible without scrolling */}
          {answeredCount >= 3 && !interviewCompleted && (
            <div className="qp-hint-banner">
              <div className="qp-hint-row qp-hint-ready">
                <span className="qp-hint-icon">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
                <span>
                  <strong>{answeredCount} questions answered</strong> — you can complete the interview now.
                  Click <strong>Complete Interview →</strong> in the top-right to move to the next step.
                </span>
              </div>
              <div className="qp-hint-row qp-hint-more">
                <span className="qp-hint-icon">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                </span>
                <span>
                  Keep answering for <strong>richer, more tailored</strong> results —
                  more context helps MarketPilot build a sharper strategy for your business.
                </span>
              </div>
            </div>
          )}

          {interviewCompleted ? (
            <div className="qp-composer-done">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Interview complete — head to Competitive Benchmarking to continue.
            </div>
          ) : (
            <div className="qp-composer">
              <textarea
                rows={3}
                placeholder={
                  latestAssistant
                    ? "Type your answer… (Enter to send · Shift+Enter for new line)"
                    : "Waiting for the AI to ask you a question…"
                }
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={busy || !latestAssistant}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (!busy && sessionId && draft.trim()) onSend();
                  }
                }}
              />
              <button
                className="btn qp-send-btn"
                onClick={onSend}
                disabled={busy || !sessionId || !draft.trim()}
              >
                {busy ? "Sending…" : "Send →"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
