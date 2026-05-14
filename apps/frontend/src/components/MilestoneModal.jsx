import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

const MILESTONES = {
  analysis: {
    icon: "🔍",
    title: "Competitive Analysis Complete",
    subtitle: "You now know exactly where you stand in your local market.",
    highlights: [
      "Competitor strengths & weaknesses mapped",
      "Market gaps identified",
      "Your differentiation angles surfaced",
    ],
    cta: "Build Your Positioning →",
    ctaPath: "/positioning",
  },
  personas: {
    icon: "👥",
    title: "Buyer Personas Generated",
    subtitle: "Your most valuable customer segments are now clearly defined.",
    highlights: [
      "Segment demographics & psychographics",
      "Buying triggers & objections identified",
      "Channel preferences mapped per persona",
    ],
    cta: "Run Deep Research →",
    ctaPath: "/research",
  },
};

export default function MilestoneModal({ milestone, onDismiss }) {
  const navigate = useNavigate();
  const backdropRef = useRef(null);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onDismiss(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onDismiss]);

  const config = MILESTONES[milestone];
  if (!config) return null;

  const handleCta = () => {
    onDismiss();
    navigate(config.ctaPath);
  };

  return (
    <div
      className="ms-backdrop"
      ref={backdropRef}
      onClick={(e) => { if (e.target === backdropRef.current) onDismiss(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="ms-title"
    >
      <div className="ms-modal">
        <div className="ms-confetti" aria-hidden="true">
          {["#b91c1c", "#d97706", "#16a34a", "#2563eb", "#7c3aed"].map((c, i) => (
            <span key={i} className="ms-confetti-dot" style={{ background: c, animationDelay: `${i * 80}ms` }} />
          ))}
        </div>

        <div className="ms-icon">{config.icon}</div>
        <h2 className="ms-title" id="ms-title">{config.title}</h2>
        <p className="ms-subtitle">{config.subtitle}</p>

        <ul className="ms-highlights">
          {config.highlights.map((h, i) => (
            <li key={i} className="ms-highlight-item">
              <span className="ms-check" aria-hidden="true">✓</span>
              {h}
            </li>
          ))}
        </ul>

        <div className="ms-actions">
          <button className="ms-cta" onClick={handleCta}>{config.cta}</button>
          <button className="ms-dismiss" onClick={onDismiss}>Stay here</button>
        </div>
      </div>
    </div>
  );
}
