/* Blurred "coming soon" preview shown behind gate states on pipeline pages */

function GhostCard({ lines = 3, title = "", wide = false }) {
  return (
    <div className="gp-card" style={{ gridColumn: wide ? "1 / -1" : undefined }}>
      {title && <div className="gp-card-title">{title}</div>}
      <div className="gp-lines">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="gp-line" style={{ width: i === lines - 1 ? "62%" : "100%" }} />
        ))}
      </div>
    </div>
  );
}

function GhostBadge({ label }) {
  return <div className="gp-badge">{label}</div>;
}

export function GhostPreviewPositioning() {
  return (
    <div className="gp-wrap gp-wrap-positioning">
      <div className="gp-tagline-block">
        <div className="gp-tagline-line" style={{ width: "75%" }} />
        <div className="gp-tagline-line gp-tagline-sub" style={{ width: "52%" }} />
      </div>
      <GhostCard title="Positioning Statement" lines={4} />
      <div className="gp-badges-row">
        <GhostBadge label="Primary Segment" />
        <GhostBadge label="Key Differentiator" />
        <GhostBadge label="Value Prop" />
      </div>
    </div>
  );
}

export function GhostPreviewPersonas() {
  return (
    <div className="gp-wrap gp-wrap-personas">
      {["Persona 1", "Persona 2", "Persona 3"].map((name) => (
        <div key={name} className="gp-persona-card">
          <div className="gp-persona-head">
            <div className="gp-avatar" />
            <div className="gp-persona-meta">
              <div className="gp-line" style={{ width: "60%", height: "14px" }} />
              <div className="gp-line" style={{ width: "40%", height: "11px", marginTop: "6px" }} />
            </div>
          </div>
          <div className="gp-lines" style={{ padding: "12px 16px" }}>
            <div className="gp-line" style={{ width: "100%" }} />
            <div className="gp-line" style={{ width: "85%" }} />
            <div className="gp-line" style={{ width: "65%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function GhostPreviewResearch() {
  return (
    <div className="gp-wrap gp-wrap-research">
      <GhostCard title="Market Insights" lines={4} wide />
      <GhostCard title="Buying Journey — Persona 1" lines={3} />
      <GhostCard title="Buying Journey — Persona 2" lines={3} />
      <GhostCard title="Quick Wins" lines={4} />
      <GhostCard title="Competitive Gaps" lines={3} />
    </div>
  );
}

export function GhostPreviewRoadmap() {
  return (
    <div className="gp-wrap gp-wrap-roadmap">
      {["Month 1 — Quick Wins", "Month 2 — Build Momentum", "Month 3 — Scale & Compound"].map((label, i) => (
        <div key={i} className="gp-roadmap-month">
          <div className="gp-roadmap-month-label">{label}</div>
          <div className="gp-lines">
            <div className="gp-line" style={{ width: "100%" }} />
            <div className="gp-line" style={{ width: "82%" }} />
            <div className="gp-line" style={{ width: "68%" }} />
            <div className="gp-line" style={{ width: "90%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
