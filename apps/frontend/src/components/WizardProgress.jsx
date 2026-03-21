export default function WizardProgress({ steps, stepIndex }) {
  return (
    <>
      <h3>Wizard Progress</h3>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {steps.map((s, idx) => (
          <span
            key={s}
            style={{
              padding: "6px 10px",
              borderRadius: 999,
              border: "1px solid #ccc",
              background: idx <= stepIndex ? "#d8f6df" : "#f2f2f2",
              fontSize: 12,
            }}
          >
            {idx + 1}. {s}
          </span>
        ))}
      </div>
    </>
  );
}
