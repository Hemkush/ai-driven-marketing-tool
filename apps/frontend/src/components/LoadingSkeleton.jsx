export function LoadingSkeleton({ lines = 4, message = "AI is working on your data…" }) {
  return (
    <div className="ls-wrap">
      {/* Spinner + message */}
      <div className="ls-header">
        <div className="ls-spinner" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
        <div className="ls-message-col">
          <span className="ls-message">{message}</span>
          <span className="ls-hint">This may take up to 30 seconds</span>
        </div>
      </div>

      {/* Shimmer skeleton rows */}
      <div className="ls-rows">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="ls-row"
            style={{ width: `${85 - (i % 3) * 12}%`, animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>

      {/* Shimmer cards */}
      <div className="ls-cards">
        {[1, 2].map((n) => (
          <div key={n} className="ls-card">
            <div className="ls-card-head" />
            <div className="ls-card-line" style={{ width: "70%" }} />
            <div className="ls-card-line" style={{ width: "50%" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
