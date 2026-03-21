import { useNavigate } from "react-router-dom";

export function PageHero({ title, subtitle }) {
  return (
    <div className="page-hero">
      <h2>{title}</h2>
      {subtitle && <p className="page-subtitle">{subtitle}</p>}
    </div>
  );
}

export function ActionRow({ children }) {
  return <div className="action-row">{children}</div>;
}

export function EmptyState({ title, description, glyph = "*" }) {
  return (
    <section className="empty-state">
      <div className="empty-glyph">{glyph}</div>
      <h4>{title}</h4>
      <p>{description}</p>
    </section>
  );
}

export function NextStepCta({ to, label, disabled = false }) {
  const navigate = useNavigate();
  return (
    <div className="next-step-wrap">
      <button className="btn next-step" onClick={() => navigate(to)} disabled={disabled}>
        {label}
      </button>
    </div>
  );
}

export function JsonPanel({ title, data }) {
  return (
    <section className="json-panel">
      <div className="json-header">
        <h4>{title}</h4>
      </div>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
