export default function QuestionRow({
  response,
  draft,
  onDraftChange,
  onAccept,
  onReject,
  busy,
}) {
  const isMcq = response.question_type === "mcq";
  const mcqOptions = response.question_options || [];
  const isSuggested = response.source === "agent_suggested";
  const isAccepted = response.source === "agent_accepted";
  const isRejected = response.source === "agent_rejected";
  const isManual = response.source === "system" || response.source === "system_seeded";
  const chipClass = isRejected
    ? "chip rejected"
    : isAccepted
    ? "chip accepted"
    : isSuggested
    ? "chip suggested"
    : isManual
    ? "chip manual"
    : "chip";

  return (
    <article className={`question-card ${isRejected ? "rejected" : ""}`}>
      <div className="question-head">
        <span>
          <b>Q{response.sequence_no}.</b> {response.question_text}
        </span>
        <span className={chipClass}>{response.source.replace("_", " ")}</span>
      </div>
      {isMcq ? (
        <select
          value={draft}
          onChange={(e) => onDraftChange(response.id, e.target.value)}
          style={{ width: "100%", marginTop: 8 }}
        >
          <option value="">Select one option</option>
          {mcqOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : (
        <textarea
          value={draft}
          onChange={(e) => onDraftChange(response.id, e.target.value)}
          rows={2}
          style={{ width: "100%", marginTop: 8 }}
          placeholder="Type answer"
        />
      )}
      <div className="action-row" style={{ marginTop: 6 }}>
        {isSuggested && (
          <>
            <button onClick={() => onAccept(response.id)} className="btn ghost" disabled={busy}>
              Accept
            </button>
            <button onClick={() => onReject(response.id)} className="btn ghost" disabled={busy}>
              Reject
            </button>
          </>
        )}
        {isAccepted && <span className="chip accepted">accepted</span>}
      </div>
    </article>
  );
}
