function Bone({ w = "100%", h = 14, radius = 6, style = {} }) {
  return (
    <div
      className="sk-bone"
      style={{ width: w, height: h, borderRadius: radius, ...style }}
    />
  );
}

/* ── Generic fallback ─────────────────────────────────────────── */
function GenericSkeleton({ message }) {
  return (
    <div className="sk-wrap">
      <div className="sk-header">
        <div className="sk-spinner" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
        <div>
          <span className="sk-message">{message}</span>
          <span className="sk-hint">This may take up to 30 seconds</span>
        </div>
      </div>
      <div className="sk-rows">
        {[90, 75, 60, 82, 50].map((w, i) => (
          <Bone key={i} w={`${w}%`} h={13} style={{ animationDelay: `${i * 0.08}s` }} />
        ))}
      </div>
    </div>
  );
}

/* ── Analysis skeleton — competitor cards grid ────────────────── */
function AnalysisSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-section-head">
        <Bone w="200px" h={18} />
        <Bone w="120px" h={12} />
      </div>
      <div className="sk-grid-3">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="sk-card" style={{ animationDelay: `${i * 0.07}s` }}>
            <div className="sk-card-top">
              <Bone w={36} h={36} radius={10} />
              <div className="sk-card-top-text">
                <Bone w="70%" h={14} />
                <Bone w="45%" h={10} />
              </div>
            </div>
            <Bone w="100%" h={8} />
            <Bone w="80%" h={8} />
            <Bone w="90%" h={8} />
            <div className="sk-tag-row">
              <Bone w={56} h={22} radius={20} />
              <Bone w={72} h={22} radius={20} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Positioning skeleton ─────────────────────────────────────── */
function PositioningSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-big-card">
        <Bone w="140px" h={10} />
        <Bone w="100%" h={22} style={{ marginTop: 12 }} />
        <Bone w="85%" h={22} />
        <Bone w="60%" h={22} />
        <div style={{ marginTop: 20 }}>
          <Bone w="90px" h={10} />
          <Bone w="100%" h={14} style={{ marginTop: 8 }} />
          <Bone w="75%" h={14} />
        </div>
        <div className="sk-tag-row" style={{ marginTop: 20 }}>
          {[80, 100, 65, 90].map((w, i) => (
            <Bone key={i} w={w} h={28} radius={6} />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Personas skeleton — cards ────────────────────────────────── */
function PersonasSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-grid-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="sk-card sk-persona-card" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="sk-persona-head">
              <Bone w={52} h={52} radius={999} />
              <div style={{ flex: 1 }}>
                <Bone w="60%" h={16} />
                <Bone w="45%" h={11} style={{ marginTop: 6 }} />
              </div>
            </div>
            <Bone w="100%" h={10} style={{ marginTop: 16 }} />
            <Bone w="90%" h={10} />
            <Bone w="70%" h={10} />
            <div className="sk-tag-row" style={{ marginTop: 14 }}>
              <Bone w={60} h={22} radius={20} />
              <Bone w={80} h={22} radius={20} />
              <Bone w={50} h={22} radius={20} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Research skeleton — insight sections ─────────────────────── */
function ResearchSkeleton() {
  return (
    <div className="sk-wrap">
      {[0, 1].map((col) => (
        <div key={col} className="sk-big-card" style={{ animationDelay: `${col * 0.12}s` }}>
          <Bone w="120px" h={10} />
          <Bone w="100%" h={16} style={{ marginTop: 12 }} />
          <Bone w="88%" h={16} />
          <Bone w="70%" h={16} />
          <div style={{ marginTop: 16 }}>
            {[0, 1, 2].map((r) => (
              <div key={r} className="sk-list-row">
                <Bone w={6} h={6} radius={999} />
                <Bone w={`${75 - r * 10}%`} h={12} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Roadmap skeleton — timeline ──────────────────────────────── */
function RoadmapSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-timeline">
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="sk-timeline-row" style={{ animationDelay: `${i * 0.06}s` }}>
            <div className="sk-timeline-dot-col">
              <Bone w={10} h={10} radius={999} />
              {i < 4 && <div className="sk-timeline-line" />}
            </div>
            <div className="sk-timeline-content">
              <Bone w="60px" h={10} />
              <Bone w={`${70 + (i % 3) * 8}%`} h={14} style={{ marginTop: 6 }} />
              <Bone w="80%" h={11} style={{ marginTop: 5 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Content skeleton — asset cards ──────────────────────────── */
function ContentSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-grid-2">
        {[0, 1].map((i) => (
          <div key={i} className="sk-card" style={{ animationDelay: `${i * 0.1}s` }}>
            <Bone w="100%" h={160} radius={10} />
            <Bone w="80%" h={14} style={{ marginTop: 14 }} />
            <Bone w="60%" h={11} style={{ marginTop: 6 }} />
            <div className="sk-tag-row" style={{ marginTop: 12 }}>
              <Bone w={70} h={24} radius={20} />
              <Bone w={90} h={24} radius={20} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Questionnaire skeleton ───────────────────────────────────── */
function QuestionnaireSkeleton() {
  return (
    <div className="sk-wrap">
      <div className="sk-chat-skeleton">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`sk-chat-row ${i % 2 === 0 ? "left" : "right"}`}
            style={{ animationDelay: `${i * 0.1}s` }}>
            <Bone w={`${45 + (i % 3) * 15}%`} h={40} radius={12} />
          </div>
        ))}
        <div className="sk-chat-input">
          <Bone w="100%" h={44} radius={10} />
        </div>
      </div>
    </div>
  );
}

/* ── Public API ───────────────────────────────────────────────── */
const VARIANTS = {
  analysis:      AnalysisSkeleton,
  positioning:   PositioningSkeleton,
  personas:      PersonasSkeleton,
  research:      ResearchSkeleton,
  roadmap:       RoadmapSkeleton,
  content:       ContentSkeleton,
  questionnaire: QuestionnaireSkeleton,
};

export function LoadingSkeleton({
  variant,
  lines = 4,
  message = "AI is working on your data…",
}) {
  const Skeleton = variant ? VARIANTS[variant] : null;
  if (Skeleton) return <Skeleton />;
  return <GenericSkeleton message={message} lines={lines} />;
}
