import { useEffect, useMemo, useRef, useState } from "react";

function MessageBubble({ item }) {
  if (item.role === "assistant") {
    return (
      <div className="chat-row bot">
        <div className="chat-avatar">AI</div>
        <div className="chat-bubble bot">
          <div className="chat-label">Assistant</div>
          <p>{item.question_text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-row user">
      <div className="chat-bubble user">
        <div className="chat-label">You</div>
        <p>{item.answer_text}</p>
      </div>
    </div>
  );
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
}) {
  const [draft, setDraft] = useState("");
  const chatLogRef = useRef(null);

  const latestAssistant = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === "assistant") return messages[i];
    }
    return null;
  }, [messages]);

  const answeredCount = messages.filter((m) => m.role === "user").length;

  useEffect(() => {
    if (!chatLogRef.current) return;
    chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
  }, [messages.length]);

  const onSend = async () => {
    const text = draft.trim();
    if (!text) return;
    await sendReply(text);
    setDraft("");
  };

  const onRestart = async () => {
    if (!sessionId) return;
    const ok = window.confirm(
      "Restart interview? This will clear current conversation and live analysis for a new session."
    );
    if (!ok) return;
    await refreshChat();
    setDraft("");
  };

  return (
    <>
      <section className="compact-card">
        <div className="chat-toolbar">
          <div>
            <h3>Step 1 - Marketing Discovery Interview</h3>
            <p className="page-subtitle">
          The assistant asks one question at a time, analyzes your response, then asks the next
          question in order: business, customer, competitors, budget, cost, and plan.
            </p>
          </div>
          <div className="action-row chat-toolbar-actions">
            <button onClick={startChat} disabled={busy || !activeProjectId}>
              Start Interview
            </button>
            <button onClick={onRestart} disabled={busy || !sessionId}>
              Restart Interview
            </button>
          </div>
        </div>
      </section>

      {messages.length > 0 && (
        <section className={`chat-layout ${answeredCount > 0 ? "expanded" : "initial"}`}>
          <aside className="compact-card analysis-panel">
            <h4>Conversation Analysis</h4>
            {!analysis ? (
              <p className="page-subtitle">
                Submit an answer to see real-time business understanding and marketing insights.
              </p>
            ) : (
              <>
                <p className="page-subtitle">{analysis.summary}</p>
                <p className="page-subtitle" style={{ marginTop: 8 }}>
                  Confidence: <b>{analysis.confidence}</b> | Source:{" "}
                  <b>{analysis.analysis_source || "fallback"}</b>
                </p>
                <p className="page-subtitle" style={{ marginTop: 4 }}>
                  Business Location: <b>{analysis.business_location || "Not provided"}</b>
                </p>
                {analysis.generated_at && (
                  <p className="page-subtitle">Last updated: {new Date(analysis.generated_at).toLocaleString()}</p>
                )}
                {!!(analysis.important_points || []).length && (
                  <>
                    <h5>Important Points From Your Responses</h5>
                    <ul className="analysis-list">
                      {(analysis.important_points || []).map((point, idx) => (
                        <li key={`point-${idx}`}>{point}</li>
                      ))}
                    </ul>
                  </>
                )}
                <div className="analysis-grid">
                  {Object.entries(analysis.understanding || {}).map(([k, v]) => (
                    <div key={k} className="analysis-item">
                      <span className="stat-label">{k.replaceAll("_", " ")}</span>
                      <span className={`chip ${v === "defined" ? "accepted" : v === "partial" ? "manual" : "rejected"}`}>
                        {String(v)}
                      </span>
                    </div>
                  ))}
                </div>
                <h5>Panel Insights</h5>
                <ul className="analysis-list">
                  {(analysis.marketing_insights || []).map((insight, idx) => (
                    <li key={idx}>{insight}</li>
                  ))}
                </ul>
                {!!(analysis.insight_evidence || []).length && (
                  <>
                    <h5>Why This Insight?</h5>
                    <div className="evidence-stack">
                      {analysis.insight_evidence.map((item, idx) => (
                        <details key={`evidence-${idx}`} className="evidence-item">
                          <summary>Insight {idx + 1} evidence</summary>
                          {!!(item.evidence_items || []).length ? (
                            <div className="evidence-list">
                              {item.evidence_items.map((e, pIdx) => (
                                <div key={`e-${idx}-${pIdx}`} className="evidence-quote">
                                  <p className="evidence-question">Q: {e.question_text}</p>
                                  <p className="evidence-text">"{e.matched_quote}"</p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="page-subtitle">No direct evidence extracted yet.</p>
                          )}
                        </details>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </aside>

          <div className="compact-card chat-panel">
            <div className="chat-panel-head">
              <h4>Conversation</h4>
              <span className="chat-status">
                {busy
                  ? "Analyzing your latest response..."
                  : answeredCount > 0
                    ? `${answeredCount} response${answeredCount > 1 ? "s" : ""} captured`
                    : "No responses captured yet"}
              </span>
            </div>
            <div ref={chatLogRef} className={`chat-log ${answeredCount > 0 ? "expanded" : "initial"}`}>
              {messages.map((item, idx) => (
                <MessageBubble key={`${item.role}-${item.response_id}-${idx}`} item={item} />
              ))}
              {busy && latestAssistant && (
                <div className="chat-row bot">
                  <div className="chat-avatar">AI</div>
                  <div className="chat-bubble bot">
                    <div className="chat-label">Assistant</div>
                    <p className="assistant-typing">Thinking...</p>
                  </div>
                </div>
              )}
            </div>

            <div className="chat-composer">
              <label htmlFor="chat-reply">Your answer</label>
              <textarea
                id="chat-reply"
                rows={4}
                placeholder={
                  latestAssistant
                    ? "Type your answer to the latest question..."
                    : "Start interview to receive your first question."
                }
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={busy || !latestAssistant}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (!busy && sessionId && draft.trim()) {
                      onSend();
                    }
                  }
                }}
              />
              <div className="wizard-nav">
                <button onClick={onSend} disabled={busy || !sessionId || !draft.trim()}>
                  Send Answer
                </button>
                <button className="btn ghost" onClick={() => finishChat(false)} disabled={busy || !sessionId}>
                  Finish Interview
                </button>
              </div>
              <p className="assistant-hint">Press Enter to send. Shift + Enter for a new line.</p>
            </div>
          </div>
        </section>
      )}
    </>
  );
}
