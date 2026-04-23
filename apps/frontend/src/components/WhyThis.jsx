import { useState } from "react";

export function WhyThis({ reasoning }) {
  const [open, setOpen] = useState(false);
  if (!reasoning) return null;

  return (
    <div style={{ marginTop: "8px" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          fontSize: "12px",
          color: "var(--text-secondary)",
          fontWeight: 500,
        }}
        aria-expanded={open}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transform: open ? "rotate(90deg)" : "none",
            transition: "transform 0.15s ease",
          }}
          aria-hidden="true"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
        Why this?
      </button>
      {open && (
        <p
          style={{
            margin: "6px 0 0 16px",
            fontSize: "12px",
            color: "var(--text-secondary)",
            lineHeight: 1.55,
            borderLeft: "2px solid var(--border)",
            paddingLeft: "10px",
          }}
        >
          {reasoning}
        </p>
      )}
    </div>
  );
}
