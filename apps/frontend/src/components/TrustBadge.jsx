export function TrustBadge({ score }) {
  if (score == null) return null;

  const high = score >= 0.85;
  const label = high ? "High confidence" : "Good confidence";
  const color = high ? "var(--success)" : "#d97706";
  const bg = high ? "var(--success-bg)" : "#fef3c7";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "5px",
        fontSize: "11px",
        fontWeight: 600,
        color,
        background: bg,
        border: `1px solid ${color}`,
        borderRadius: "999px",
        padding: "2px 8px",
        letterSpacing: "0.01em",
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ fontSize: "8px" }}>{high ? "●" : "◑"}</span>
      {label}
    </span>
  );
}
