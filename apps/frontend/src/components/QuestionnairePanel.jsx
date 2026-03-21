import { useEffect, useMemo, useState } from "react";
import QuestionRow from "./QuestionRow";

const QUESTIONS_PER_BATCH = 3;

export default function QuestionnairePanel({
  startQuestionnaireSession,
  loadQuestionnaireSession,
  generateNextQuestions,
  busy,
  activeProjectId,
  sessionId,
  responses,
  acceptSuggested,
  rejectSuggested,
  saveAnswersBulk,
}) {
  const answeredCount = responses.filter((r) => (r.answer_text || "").trim()).length;
  const suggestedCount = responses.filter((r) => r.source === "agent_suggested").length;
  const [batchStep, setBatchStep] = useState(0);
  const [draftAnswers, setDraftAnswers] = useState({});

  useEffect(() => {
    setBatchStep(0);
  }, [sessionId]);

  useEffect(() => {
    setDraftAnswers((prev) => {
      const next = { ...prev };
      for (const r of responses) {
        if (!(r.id in next)) {
          next[r.id] = r.answer_text || "";
        }
      }
      for (const key of Object.keys(next)) {
        if (!responses.find((r) => String(r.id) === String(key))) {
          delete next[key];
        }
      }
      return next;
    });
  }, [responses]);

  const orderedResponses = useMemo(
    () =>
      responses
        .filter((r) => r.source !== "agent_rejected")
        .slice()
        .sort((a, b) => a.sequence_no - b.sequence_no),
    [responses]
  );

  const totalBatches = Math.max(1, Math.ceil(orderedResponses.length / QUESTIONS_PER_BATCH));
  const safeBatchStep = Math.min(batchStep, totalBatches - 1);
  const start = safeBatchStep * QUESTIONS_PER_BATCH;
  const visibleResponses = orderedResponses.slice(start, start + QUESTIONS_PER_BATCH);
  const isFirstStep = safeBatchStep === 0;
  const isLastStep = safeBatchStep >= totalBatches - 1;

  const goPrev = () => {
    if (isFirstStep) return;
    setBatchStep((prev) => Math.max(0, prev - 1));
  };

  const goNext = () => {
    if (isLastStep) return;
    setBatchStep((prev) => Math.min(totalBatches - 1, prev + 1));
  };

  const onDraftChange = (responseId, value) => {
    setDraftAnswers((prev) => ({ ...prev, [responseId]: value }));
  };

  const saveCurrentBatch = async () => {
    const entries = visibleResponses
      .map((r) => ({
        responseId: r.id,
        answerText: String(draftAnswers[r.id] ?? "").trim(),
      }))
      .filter((x) => x.answerText);
    if (!entries.length) return;
    await saveAnswersBulk(entries);
  };

  return (
    <>
      <section className="compact-card">
        <h3>Step 1 - Questionnaire Wizard</h3>
        <div className="action-row">
          <button onClick={startQuestionnaireSession} disabled={busy || !activeProjectId}>
            Start Session
          </button>
          <button onClick={loadQuestionnaireSession} disabled={busy || !sessionId}>
            Refresh Session
          </button>
          <button onClick={generateNextQuestions} disabled={busy || !sessionId}>
            Generate AI Follow-up Questions
          </button>
        </div>
        <div className="stat-grid">
          <div className="stat-item">
            <span className="stat-label">Session</span>
            <span className="stat-value">{sessionId || "-"}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Qs</span>
            <span className="stat-value">{responses.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Answered</span>
            <span className="stat-value">{answeredCount}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Suggested</span>
            <span className="stat-value">{suggestedCount}</span>
          </div>
        </div>
      </section>

      {responses.length > 0 && (
        <section className="compact-card wizard-wrap">
          <div className="wizard-head">
            <div>
              <h4>Questionnaire Questions</h4>
            </div>
          </div>

          <div className="card-grid wizard-questions">
            {visibleResponses.map((r) => (
              <QuestionRow
                key={r.id}
                response={r}
                draft={draftAnswers[r.id] ?? ""}
                onDraftChange={onDraftChange}
                onAccept={acceptSuggested}
                onReject={rejectSuggested}
                busy={busy}
              />
            ))}
          </div>

          <div className="wizard-nav">
            <button onClick={saveCurrentBatch} disabled={busy}>
              Save Answers
            </button>
            <button className="btn ghost" onClick={goPrev} disabled={busy || isFirstStep}>
              Prev
            </button>
            <button onClick={goNext} disabled={busy || isLastStep}>
              Next
            </button>
          </div>
        </section>
      )}
    </>
  );
}
