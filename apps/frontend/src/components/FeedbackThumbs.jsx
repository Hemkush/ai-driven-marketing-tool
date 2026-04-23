import { useState } from "react";
import { submitFeedback } from "../lib/mvpClient";

export function FeedbackThumbs({ projectId, agent, qualityScore }) {
  const [voted, setVoted] = useState(null);

  async function vote(polarity) {
    if (voted !== null) return;
    setVoted(polarity);
    try {
      await submitFeedback({ project_id: projectId, agent, quality_score: qualityScore, polarity });
    } catch {
      // fire-and-forget — don't surface feedback errors to user
    }
  }

  if (voted !== null) {
    return (
      <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
        Thanks for the feedback
      </span>
    );
  }

  const btnStyle = {
    background: "none",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    padding: "3px 8px",
    cursor: "pointer",
    fontSize: "13px",
    color: "var(--text-secondary)",
    lineHeight: 1,
  };

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
      <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Helpful?</span>
      <button style={btnStyle} onClick={() => vote(1)} aria-label="Thumbs up">👍</button>
      <button style={btnStyle} onClick={() => vote(-1)} aria-label="Thumbs down">👎</button>
    </span>
  );
}
