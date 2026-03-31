import { useState } from "react";

const THREAT_BADGE = {
  high: { label: "High Threat", cls: "threat-high" },
  medium: { label: "Med Threat", cls: "threat-medium" },
  low: { label: "Low Threat", cls: "threat-low" },
};

const DENSITY_LABEL = { low: "Low Competition", medium: "Moderate Competition", high: "High Competition" };

function StarRating({ rating }) {
  if (rating == null) return <span className="no-data">No rating</span>;
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span className="star-rating">
      {"★".repeat(full)}
      {half ? "½" : ""}
      {"☆".repeat(Math.max(0, 5 - full - (half ? 1 : 0)))}
      <span className="star-num">{rating.toFixed(1)}</span>
    </span>
  );
}

const THREAT_COLORS = { high: "#ef4444", medium: "#f59e0b", low: "#22c55e" };

function hashJitter(str, range) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) & 0xffff;
  return ((h % 100) / 100 - 0.5) * range;
}

const X_COLS = ["Free", "$", "$$", "$$$", "$$$$"];

function PriceRatingChart({ competitors }) {
  const [hovered, setHovered] = useState(null);

  // Only plot competitors with both price level and rating
  const plotted = competitors.filter((c) => c.price_level != null && c.rating != null);
  if (plotted.length === 0) return null;

  const W = 580, H = 300;
  const PAD = { top: 24, right: 20, bottom: 52, left: 52 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  // 5 columns: 0=Free, 1=$, 2=$$, 3=$$$, 4=$$$$
  const colX = (colIdx) => PAD.left + (colIdx / (X_COLS.length - 1)) * plotW;
  const getCol = (c) => Math.min(c.price_level, 4);
  const yScale = (r) => PAD.top + plotH - ((r - 1) / 4) * plotH;

  return (
    <section className="compact-card benchmarking-chart">
      <h5>Price vs Quality Map</h5>
      <p className="chart-subtitle">Where each competitor sits on price level vs customer rating — hover a dot for details</p>
      <div className="chart-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} className="price-rating-svg" aria-label="Price vs Rating scatter chart">
          {/* Horizontal grid */}
          {[1, 2, 3, 4, 5].map((r) => (
            <line key={`yg${r}`} x1={PAD.left} y1={yScale(r)} x2={W - PAD.right} y2={yScale(r)}
              stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" />
          ))}
          {/* Vertical column guides */}
          {X_COLS.map((_, i) => (
            <line key={`xg${i}`} x1={colX(i)} y1={PAD.top} x2={colX(i)} y2={H - PAD.bottom}
              stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" />
          ))}
          {/* Axes */}
          <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} stroke="#cbd5e1" strokeWidth="1.5" />
          <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} stroke="#cbd5e1" strokeWidth="1.5" />
          {/* Y labels */}
          {[1, 2, 3, 4, 5].map((r) => (
            <text key={`yl${r}`} x={PAD.left - 8} y={yScale(r) + 4} textAnchor="end" fontSize="11" fill="#64748b">★{r}</text>
          ))}
          {/* X labels */}
          {X_COLS.map((lbl, i) => (
            <text key={`xl${i}`} x={colX(i)} y={H - PAD.bottom + 18} textAnchor="middle"
              fontSize="11" fill="#64748b">{lbl}</text>
          ))}
          {/* Axis titles */}
          <text x={W / 2} y={H - 6} textAnchor="middle" fontSize="12" fill="#475569" fontWeight="500">Price Level</text>
          <text transform={`translate(13,${H / 2}) rotate(-90)`} textAnchor="middle" fontSize="12" fill="#475569" fontWeight="500">Rating</text>
          {/* Dots */}
          {plotted.map((c, idx) => {
            const col = getCol(c);
            const cx = colX(col) + hashJitter(c.name, 22);
            const cy = yScale(c.rating) + hashJitter(c.name + "y", 12);
            const color = THREAT_COLORS[c.competitive_threat_level] || "#94a3b8";
            const active = hovered === idx;
            return (
              <g key={idx} onMouseEnter={() => setHovered(idx)} onMouseLeave={() => setHovered(null)} style={{ cursor: "pointer" }}>
                <circle cx={cx} cy={cy} r={active ? 13 : 9}
                  fill={color} fillOpacity="0.88"
                  stroke={active ? "#1e293b" : "#fff"} strokeWidth={active ? 2 : 1.5} />
                {active && (
                  <text x={cx} y={cy - 18} textAnchor="middle" fontSize="11" fill="#1e293b" fontWeight="600"
                    style={{ pointerEvents: "none" }}>
                    {c.name.length > 22 ? c.name.slice(0, 20) + "…" : c.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {hovered !== null && plotted[hovered] && (
          <div className="chart-tooltip">
            <strong>{plotted[hovered].name}</strong>
            <span>Rating: ★ {plotted[hovered].rating?.toFixed(1)}</span>
            <span>Price: {plotted[hovered].price_label || "N/A"}</span>
            <span className={`tooltip-threat tooltip-threat-${plotted[hovered].competitive_threat_level}`}>
              {(plotted[hovered].competitive_threat_level || "unknown").charAt(0).toUpperCase() +
                (plotted[hovered].competitive_threat_level || "unknown").slice(1)} Threat
            </span>
            {plotted[hovered].review_count != null && (
              <span>{plotted[hovered].review_count.toLocaleString()} reviews</span>
            )}
          </div>
        )}
      </div>

      <div className="chart-legend">
        {Object.entries(THREAT_COLORS).map(([level, color]) => (
          <span key={level} className="legend-item">
            <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
              <circle cx="6" cy="6" r="5" fill={color} fillOpacity="0.88" stroke="#fff" strokeWidth="1" />
            </svg>
            {level.charAt(0).toUpperCase() + level.slice(1)} Threat
          </span>
        ))}
      </div>
    </section>
  );
}

function HoursGapAnalysis({ data }) {
  if (!data) return null;
  const { opportunity_windows = [], coverage_notes, recommendation } = data;
  if (!opportunity_windows.length && !coverage_notes && !recommendation) return null;
  return (
    <section className="compact-card hours-gap-card">
      <h5>Hours &amp; Availability Gap</h5>
      <p className="chart-subtitle">When your competitors are closed — your door can be open</p>
      {coverage_notes && <p className="hours-coverage-note">{coverage_notes}</p>}
      {opportunity_windows.length > 0 && (
        <ul className="hours-gap-list">
          {opportunity_windows.map((w, i) => (
            <li key={i} className="hours-gap-item">
              <span className="gap-dot" />
              {w}
            </li>
          ))}
        </ul>
      )}
      {recommendation && (
        <div className="hours-recommendation">
          <span className="rec-label">Recommendation</span>
          <span className="rec-text">{recommendation}</span>
        </div>
      )}
    </section>
  );
}

const SWOT_CONFIG = [
  { key: "strengths",     label: "Strengths",     letter: "S", cls: "swot-s" },
  { key: "weaknesses",    label: "Weaknesses",    letter: "W", cls: "swot-w" },
  { key: "opportunities", label: "Opportunities", letter: "O", cls: "swot-o" },
  { key: "threats",       label: "Threats",       letter: "T", cls: "swot-t" },
];

function SwotAnalysis({ data }) {
  if (!data) return null;
  const hasAny = SWOT_CONFIG.some(({ key }) => (data[key] || []).length > 0);
  if (!hasAny) return null;
  return (
    <section className="compact-card swot-card">
      <h5>SWOT Analysis</h5>
      <p className="chart-subtitle">Your business vs the local market — based on your interview and competitor data</p>
      <div className="swot-grid">
        {SWOT_CONFIG.map(({ key, label, letter, cls }) => (
          <div key={key} className={`swot-quadrant ${cls}`}>
            <div className="swot-quadrant-head">
              <span className="swot-letter">{letter}</span>
              <span className="swot-label">{label}</span>
            </div>
            <ul className="swot-list">
              {(data[key] || []).map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

export function CompetitorCards({ analysis }) {
  if (!analysis) return null;

  const competitors = analysis.competitors || [];
  const market = analysis.market_overview || {};
  const avgPriceLabel = market.avg_price_level > 0 ? ["", "$", "$$", "$$$", "$$$$"][Math.round(market.avg_price_level)] : "N/A";
  const densityLabel = DENSITY_LABEL[market.market_density] || market.market_density || "N/A";
  const densityColorCls = { low: "density-low", medium: "density-medium", high: "density-high" }[market.market_density] || "";
  const topThreat = competitors.find((c) => c.competitive_threat_level === "high") || null;

  return (
    <div className="cb-results">
      {/* Market Snapshot */}
      <section className="compact-card benchmarking-snapshot">
        <h4>Local Market Snapshot</h4>
        <p className="page-subtitle">{analysis.business_location || "Your area"}</p>
        <div className="snapshot-grid">
          <div className="snapshot-stat">
            <span className="snapshot-val">{market.total_competitors_found ?? 0}</span>
            <span className="snapshot-key">Competitors Found</span>
          </div>
          <div className="snapshot-stat">
            <span className={`snapshot-val ${densityColorCls}`}>{densityLabel}</span>
            <span className="snapshot-key">Market Density</span>
          </div>
          <div className="snapshot-stat">
            <span className="snapshot-val">{market.avg_rating != null ? `★ ${market.avg_rating}` : "N/A"}</span>
            <span className="snapshot-key">Avg. Rating</span>
          </div>
          <div className="snapshot-stat">
            <span className="snapshot-val">{avgPriceLabel}</span>
            <span className="snapshot-key">Avg. Price Level</span>
          </div>
        </div>
        {market.market_size_notes && (
          <p className="snapshot-note">{market.market_size_notes}</p>
        )}
      </section>

      {/* Price vs Rating Chart */}
      {competitors.length > 0 && <PriceRatingChart competitors={competitors} />}

      {/* Hours Gap Analysis */}
      <HoursGapAnalysis data={analysis.hours_gap_analysis} />

      {/* SWOT Analysis */}
      <SwotAnalysis data={analysis.swot_analysis} />

      {/* Opportunity Gaps + Win Strategies */}
      {(market.opportunity_gaps?.length > 0 || market.win_strategies?.length > 0) && (
        <div className="benchmarking-insights-row">
          {market.opportunity_gaps?.length > 0 && (
            <section className="compact-card benchmarking-gaps">
              <h5>Opportunity Gaps</h5>
              <ul className="insight-list">
                {market.opportunity_gaps.map((g, i) => (
                  <li key={`gap-${i}`}>{g}</li>
                ))}
              </ul>
            </section>
          )}
          {market.win_strategies?.length > 0 && (
            <section className="compact-card benchmarking-strategies">
              <h5>Competitive Edge</h5>
              <ul className="insight-list">
                {market.win_strategies.map((s, i) => (
                  <li key={`win-${i}`}>{s}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      {/* Competitor Cards */}
      {competitors.length > 0 ? (
        <>
          <div className="cb-comp-header">
            <div>
              <p className="cb-comp-kicker">Competitor Intelligence</p>
              <p className="cb-comp-sub">
                {competitors.length} local competitor{competitors.length !== 1 ? "s" : ""} analysed · sorted by threat level
              </p>
            </div>
            {topThreat && (
              <div className="cb-top-threat">
                <span className="cb-top-threat-label">Highest Threat</span>
                <span className="cb-top-threat-name">{topThreat.name}</span>
              </div>
            )}
          </div>
          <div className="competitor-grid">
            {competitors.map((c, idx) => {
              const threat = THREAT_BADGE[c.competitive_threat_level] || THREAT_BADGE.medium;
              return (
                <article key={`comp-${idx}`} className={`compact-card competitor-card threat-card-${c.competitive_threat_level || "medium"}`}>
                  {/* Header */}
                  <div className="competitor-head">
                    <div className="competitor-title-row">
                      <h4 className="competitor-name">{c.name}</h4>
                      <span className={`threat-badge ${threat.cls}`}>{threat.label}</span>
                    </div>
                    <div className="competitor-meta-row">
                      <StarRating rating={c.rating} />
                      {c.review_count != null && (
                        <span className="review-count">({c.review_count.toLocaleString()} reviews)</span>
                      )}
                      <span className="price-badge">{c.price_label || "N/A"}</span>
                    </div>
                  </div>

                  {/* Contact & location */}
                  <div className="competitor-contact">
                    {c.address && <p className="contact-row">📍 {c.address}</p>}
                    {c.phone && <p className="contact-row">📞 {c.phone}</p>}
                    {c.website && (
                      <p className="contact-row">
                        🌐{" "}
                        <a href={c.website.startsWith("http") ? c.website : `https://${c.website}`} target="_blank" rel="noreferrer">
                          {c.website.replace(/^https?:\/\//, "").split("/")[0]}
                        </a>
                      </p>
                    )}
                    {c.hours?.length > 0 && (
                      <details className="hours-details">
                        <summary>Opening Hours</summary>
                        <ul className="hours-list">
                          {c.hours.map((h, hi) => <li key={hi}>{h}</li>)}
                        </ul>
                      </details>
                    )}
                  </div>

                  {/* AI Insights — collapsed by default */}
                  <details className="competitor-insights-details">
                    <summary className="competitor-insights-summary">
                      <span>View Details</span>
                      <svg className="comp-insights-chevron" width="13" height="13" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" strokeWidth="2.5"
                        strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                    </summary>
                    <div className="competitor-insights">
                      {c.business_model && (
                        <div className="insight-row">
                          <span className="insight-label">Business Model</span>
                          <span className="insight-value">{c.business_model}</span>
                        </div>
                      )}
                      {c.pricing_notes && (
                        <div className="insight-row insight-row-full">
                          <span className="insight-label">Pricing</span>
                          <span className="insight-value">{c.pricing_notes}</span>
                        </div>
                      )}
                      {c.services_offered?.length > 0 && (
                        <div className="insight-row">
                          <span className="insight-label">Services</span>
                          <span className="insight-value">{c.services_offered.join(" · ")}</span>
                        </div>
                      )}
                      {c.special_services?.length > 0 && (
                        <div className="insight-row">
                          <span className="insight-label">Special</span>
                          <span className="insight-value">{c.special_services.join(" · ")}</span>
                        </div>
                      )}
                      {c.estimated_discounts?.length > 0 && (
                        <div className="insight-row">
                          <span className="insight-label">Discounts</span>
                          <span className="insight-value">{c.estimated_discounts.join(" · ")}</span>
                        </div>
                      )}
                      {c.how_they_compete && (
                        <div className="insight-row insight-row-full">
                          <span className="insight-label">Strategy</span>
                          <span className="insight-value">{c.how_they_compete}</span>
                        </div>
                      )}
                      {c.review_summary && (
                        <div className="insight-row insight-row-full">
                          <span className="insight-label">Customer Sentiment</span>
                          <span className="insight-value">{c.review_summary}</span>
                        </div>
                      )}
                    </div>
                  </details>

                  {/* Review snippets */}
                  {c.review_snippets?.length > 0 && (
                    <details className="review-snippets-details">
                      <summary>Customer Reviews ({c.review_snippets.length})</summary>
                      <div className="review-snippets">
                        {c.review_snippets.map((r, ri) => (
                          <blockquote key={ri} className="review-snippet">"{r}"</blockquote>
                        ))}
                      </div>
                    </details>
                  )}

                  {c.google_maps_url && (
                    <a href={c.google_maps_url} target="_blank" rel="noreferrer" className="maps-link-btn">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                      </svg>
                      View on Google Maps
                    </a>
                  )}
                </article>
              );
            })}
          </div>
        </>
      ) : (
        <section className="compact-card benchmarking-empty">
          <p>No competitors found in the area. Try increasing the search radius or checking the business address.</p>
        </section>
      )}
    </div>
  );
}

function PersonaAvatar({ name }) {
  const initials = (name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
  const colors = ["#c72832", "#2563eb", "#059669", "#7c3aed", "#d97706"];
  const color = colors[(name?.charCodeAt(0) || 0) % colors.length];
  return (
    <div className="persona-avatar" style={{ background: color }}>
      {initials}
    </div>
  );
}

export function PersonaCards({ personas = [] }) {
  return (
    <div className="persona-grid">
      {personas.map((p) => {
        const profile = p.profile || p;
        const basic = profile.basic_profile || {};
        const psycho = profile.psychographic_profile || {};
        const behavior = profile.behavioral_profile || {};
        const engage = profile.engagement_strategy || {};
        const channels = Array.isArray(engage.preferred_channels) ? engage.preferred_channels : [];
        const topics = Array.isArray(engage.resonant_content_topics) ? engage.resonant_content_topics : [];
        const name = p.name || profile.name || "Persona";

        return (
          <article key={p.id || name} className="compact-card persona-card">
            {/* Header */}
            <div className="persona-head">
              <PersonaAvatar name={name} />
              <div className="persona-head-info">
                <h4 className="persona-name">{name}</h4>
                <div className="persona-meta-tags">
                  {basic.occupation && <span className="persona-tag">{basic.occupation}</span>}
                  {basic.age && <span className="persona-tag">{basic.age}</span>}
                  {basic.income && <span className="persona-tag">{basic.income}</span>}
                </div>
                {basic.location && (
                  <p className="persona-location">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
                      style={{ display: "inline", marginRight: 3, verticalAlign: "middle", flexShrink: 0 }}>
                      <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                    {basic.location}
                  </p>
                )}
              </div>
            </div>

            {/* Key message — hero callout immediately below header */}
            {engage.key_messages_that_convert && (
              <div className="persona-key-message">
                <span className="persona-key-label">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }}>
                    <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74z" />
                  </svg>
                  Message That Converts
                </span>
                <span className="persona-key-text">&ldquo;{engage.key_messages_that_convert}&rdquo;</span>
              </div>
            )}

            {/* Psychographic */}
            <div className="persona-section">
              <div className="persona-section-title">Goals & Motivations</div>
              <p className="persona-section-text">{psycho.goals_and_motivations || "N/A"}</p>
            </div>
            <div className="persona-section persona-pain">
              <div className="persona-section-title">Pain Points</div>
              <p className="persona-section-text">{psycho.pain_points_and_frustrations || "N/A"}</p>
            </div>

            {/* Channels */}
            {channels.length > 0 && (
              <div className="persona-section">
                <div className="persona-section-title">Preferred Channels</div>
                <div className="persona-channel-tags">
                  {channels.map((ch, i) => <span key={i} className="persona-channel-tag">{ch}</span>)}
                </div>
              </div>
            )}

            {/* Content topics */}
            {topics.length > 0 && (
              <div className="persona-section">
                <div className="persona-section-title">Resonant Content</div>
                <div className="persona-channel-tags">
                  {topics.map((t, i) => <span key={i} className="persona-topic-tag">{t}</span>)}
                </div>
              </div>
            )}

            {/* Behavioral (secondary detail) */}
            {psycho.values_and_priorities && (
              <div className="persona-section">
                <div className="persona-section-title">Values & Priorities</div>
                <p className="persona-section-text">{psycho.values_and_priorities}</p>
              </div>
            )}
            {behavior.decision_making_process && (
              <div className="persona-section">
                <div className="persona-section-title">How They Decide</div>
                <p className="persona-section-text">{behavior.decision_making_process}</p>
              </div>
            )}
            {behavior.buying_triggers_and_barriers && (
              <div className="persona-section">
                <div className="persona-section-title">Triggers & Barriers</div>
                <p className="persona-section-text">{behavior.buying_triggers_and_barriers}</p>
              </div>
            )}

            {/* Best time */}
            {engage.best_times_to_reach && (
              <p className="persona-best-time">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  style={{ display: "inline", marginRight: 5, verticalAlign: "middle", flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                Best time to reach: {engage.best_times_to_reach}
              </p>
            )}
          </article>
        );
      })}
    </div>
  );
}

export function AnalysisCards({ analysis }) {
  if (!analysis) return null;
  const normalizeUrl = (raw) => {
    let val = String(raw || "").trim();
    if (!val) return "";
    const mdMatch = val.match(/\((https?:\/\/[^)]+)\)/i);
    if (mdMatch?.[1]) val = mdMatch[1].trim();
    val = val.replace(/[),.;]+$/, "");
    if (val.startsWith("http://") || val.startsWith("https://") || val.startsWith("internal://")) {
      return val;
    }
    if (/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(\/.*)?$/.test(val)) {
      return `https://${val}`;
    }
    return "";
  };
  const isWebUrl = (url) => url.startsWith("http://") || url.startsWith("https://");
  const buildSearchUrl = (title) =>
    title ? `https://www.google.com/search?q=${encodeURIComponent(String(title).trim())}` : "";
  const asArray = (value) =>
    Array.isArray(value) ? value : value && typeof value === "object" ? [value] : [];
  const humanizeKey = (key) =>
    String(key || "")
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/\b\w/g, (m) => m.toUpperCase());
  const formatCurrency = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(n);
  };
  const formatPercent = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
  };
  const formatNumberIfNumeric = (value) => {
    if (typeof value === "number" && Number.isFinite(value)) {
      return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    const raw = String(value ?? "").trim();
    if (/^-?\d+(\.\d+)?$/.test(raw)) {
      const n = Number(raw);
      return Number.isInteger(n) ? n.toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return raw;
  };
  const text = (value) => {
    if (value === null || value === undefined) return "";
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      return formatNumberIfNumeric(value);
    }
    if (Array.isArray(value)) return value.map(text).filter(Boolean).join(" | ");
    if (typeof value === "object") {
      if (Array.isArray(value.action_items)) return text(value.action_items);
      const vals = Object.values(value).map(text).filter(Boolean);
      return vals.join(" | ");
    }
    return "";
  };
  const itemToReadable = (value) => {
    if (value === null || value === undefined) return "";
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      return formatNumberIfNumeric(value);
    }
    if (Array.isArray(value)) {
      return value.map(itemToReadable).filter(Boolean).join(" | ");
    }
    if (typeof value === "object") {
      if (Array.isArray(value.action_items)) {
        return itemToReadable(value.action_items);
      }
      const pairs = Object.entries(value)
        .map(([k, v]) => {
          const rendered = itemToReadable(v);
          if (!rendered) return "";
          return `${humanizeKey(k)}: ${rendered}`;
        })
        .filter(Boolean);
      return pairs.join(" | ");
    }
    return "";
  };
  const list = (value) =>
    asArray(value)
      .flatMap((x) => (x && typeof x === "object" && Array.isArray(x.action_items) ? x.action_items : [x]))
      .map((x) => itemToReadable(x).trim())
      .filter(Boolean);

  const block = analysis.segment_attractiveness_analysis || {};
  const executive = analysis.executive_brief || {};
  const deep = analysis.deep_market_analysis || {};
  const market = analysis.market_sizing || {};
  const economics = analysis.unit_economics || {};
  const competition = analysis.competitive_landscape || {};
  const pricing = analysis.pricing_power_analysis || {};
  const retention = analysis.retention_risk_analysis || {};
  const segments = asArray(block.segments);
  const channels = asArray(analysis.channel_mix_efficiency);
  const scenarios = asArray(analysis.growth_scenarios_90_day);
  const priorities = asArray(analysis.prioritization_matrix);
  const risks = asArray(analysis.strategic_risk_register);
  const actions = list(analysis.executive_actions);
  const sources = asArray(analysis.sources);
  const sourceTransparency = analysis.source_transparency || {};

  const section = (title, items = []) => {
    const filtered = items.filter(Boolean);
    if (!filtered.length) return null;
    return (
      <section className="analysis-section" key={title}>
        <h5>{title}</h5>
        <div className="analysis-rows">
          {filtered.map((item, idx) => {
            const value = String(item);
            const splitIdx = value.indexOf(":");
            const hasLabel = splitIdx > 0 && splitIdx < 40;
            const label = hasLabel ? value.slice(0, splitIdx).trim() : "";
            const body = hasLabel ? value.slice(splitIdx + 1).trim() : value;
            return (
              <div key={`${title}-${idx}`} className="analysis-row">
                {hasLabel ? <span className="analysis-row-label">{label}</span> : null}
                <span className="analysis-row-value">{body}</span>
              </div>
            );
          })}
        </div>
      </section>
    );
  };

  return (
    <article className="compact-card analysis-report-box">
      <div className="analysis-report-head">
        <h4>Competitive Benchmarking Report</h4>
        <div className="meta-row">
          <span>Primary Segment: {block.recommended_primary_segment || "N/A"}</span>
          <span>Location: {block.business_address || "N/A"}</span>
          <span>Source: {analysis.analysis_source === "ai" ? "AI" : "Fallback"}</span>
        </div>
        {analysis.analysis_source !== "ai" && analysis.fallback_reason ? (
          <p className="page-subtitle">Fallback reason: {analysis.fallback_reason}</p>
        ) : null}
      </div>

      {(executive.market_outlook || list(executive.core_drivers).length || list(executive.opportunities).length) && (
        <section className="analysis-section">
          <h5>Executive Summary</h5>
          <div className="analysis-group-wrap">
            {!!text(executive.market_outlook) && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Market Outlook</div>
                <p className="analysis-group-text">{text(executive.market_outlook)}</p>
              </div>
            )}
            {!!list(executive.core_drivers).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Core Drivers</div>
                <ul className="analysis-group-list">
                  {list(executive.core_drivers).map((item, idx) => (
                    <li key={`driver-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {!!list(executive.opportunities).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Top Opportunities</div>
                <ul className="analysis-group-list">
                  {list(executive.opportunities).map((item, idx) => (
                    <li key={`opp-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}
      {(list(deep.market_size_and_growth).length ||
        list(deep.core_market_drivers).length ||
        list(deep.industry_trends).length ||
        list(deep.opportunities).length ||
        deep.overall_outlook) && (
        <section className="analysis-section">
          <h5>Deep Market Analysis</h5>
          <div className="analysis-group-wrap">
            {!!list(deep.market_size_and_growth).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Market Size & Growth</div>
                <ul className="analysis-group-list">
                  {list(deep.market_size_and_growth).map((item, idx) => (
                    <li key={`d-size-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {!!list(deep.core_market_drivers).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Drivers</div>
                <ul className="analysis-group-list">
                  {list(deep.core_market_drivers).map((item, idx) => (
                    <li key={`d-driver-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {!!list(deep.industry_trends).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Industry Trends</div>
                <ul className="analysis-group-list">
                  {list(deep.industry_trends).map((item, idx) => (
                    <li key={`d-trend-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {!!list(deep.opportunities).length && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Opportunities</div>
                <ul className="analysis-group-list">
                  {list(deep.opportunities).map((item, idx) => (
                    <li key={`d-opp-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {!!text(deep.overall_outlook) && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Overall Outlook</div>
                <p className="analysis-group-text">{text(deep.overall_outlook)}</p>
              </div>
            )}
          </div>
        </section>
      )}
      {section("Market Size & Growth", [
        market.tam_estimate_usd
          ? `Total Addressable Market (TAM, USD/year): ${formatCurrency(market.tam_estimate_usd)}`
          : "",
        market.sam_estimate_usd
          ? `Serviceable Addressable Market (SAM, USD/year): ${formatCurrency(market.sam_estimate_usd)}`
          : "",
        market.som_estimate_usd
          ? `Serviceable Obtainable Market (SOM, USD/year): ${formatCurrency(market.som_estimate_usd)}`
          : "",
        market.growth_rate_pct
          ? `Estimated Market Growth Rate (Annual): ${formatPercent(market.growth_rate_pct)}`
          : "",
        market.growth_estimate ? `Growth Estimate: ${text(market.growth_estimate)}` : "",
        market.investment_return ? `Estimated Investment Return: ${text(market.investment_return)}` : "",
        market.geography_assumption
          ? `Assumed Geography Scope: ${text(market.geography_assumption)}`
          : "",
        market.confidence ? `Confidence Level: ${text(market.confidence)}` : "",
      ])}
      {section("Unit Economics", [
        economics.estimated_cac_usd ? `CAC: ${economics.estimated_cac_usd}` : "",
        economics.estimated_ltv_usd ? `LTV: ${economics.estimated_ltv_usd}` : "",
        economics.ltv_cac_ratio ? `LTV/CAC: ${economics.ltv_cac_ratio}` : "",
        economics.estimated_payback_months ? `Payback Months: ${economics.estimated_payback_months}` : "",
      ])}
      {section("Competitive and Pricing", [
        competition.competitive_intensity_score
          ? `Competitive Intensity: ${competition.competitive_intensity_score}`
          : "",
        pricing.pricing_power_score ? `Pricing Power: ${pricing.pricing_power_score}` : "",
        pricing.elasticity_risk ? `Elasticity Risk: ${pricing.elasticity_risk}` : "",
        retention.churn_risk_score ? `Retention Risk: ${retention.churn_risk_score}` : "",
      ])}
      {segments.length > 0 ? (
        <section className="analysis-section">
          <h5>Segment Notes</h5>
          <div className="analysis-rows">
            {segments.map((s, idx) => (
              <div key={`segment-${idx}`} className="analysis-row">
                <span className="analysis-row-label">{text(s.segment_name) || `Segment ${idx + 1}`}</span>
                <span className="analysis-row-value">{text(s.notes) || "No notes"}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {section(
        "Channel Efficiency",
        channels.slice(0, 6).map((c, idx) => {
          const channel = text(c?.channel) || `Channel ${idx + 1}`;
          const score = text(c?.efficiency_score) || "N/A";
          const cac = text(c?.est_cac_usd) || "N/A";
          return `${channel}: Score ${score}, CAC ${cac}`;
        })
      )}
      {section(
        "90-Day Scenarios",
        scenarios.map((s, idx) => {
          const scenario = text(s?.scenario) || `Scenario ${idx + 1}`;
          const lift = text(s?.expected_pipeline_lift_pct) || "N/A";
          return `${scenario}: ${lift}% expected lift`;
        })
      )}
      {section(
        "Top Priorities",
        priorities.slice(0, 6).map((p, idx) => {
          const pr = text(p?.priority) || `P${idx + 1}`;
          const initiative = text(p?.initiative) || "N/A";
          const impact = text(p?.impact) || "N/A";
          const effort = text(p?.effort) || "N/A";
          return `${pr}: ${initiative} (${impact}/${effort})`;
        })
      )}
      {section(
        "Strategic Risks",
        risks.slice(0, 6).map((r) => `${text(r?.severity) || "N/A"}: ${text(r?.risk) || "N/A"}`)
      )}
      {section("Executive Actions", actions)}

      {(sourceTransparency.external_sources_used !== undefined ||
        sourceTransparency.verification_level ||
        sourceTransparency.note) && (
        <section className="analysis-section">
          <h5>Source Transparency</h5>
          <div className="analysis-rows">
            <div className="analysis-row">
              <span className="analysis-row-label">External Sources Used</span>
              <span className="analysis-row-value">
                {sourceTransparency.external_sources_used ? "Yes" : "No"}
              </span>
            </div>
            <div className="analysis-row">
              <span className="analysis-row-label">Verification Level</span>
              <span className="analysis-row-value">{text(sourceTransparency.verification_level) || "N/A"}</span>
            </div>
            {text(sourceTransparency.note) ? (
              <div className="analysis-row">
                <span className="analysis-row-label">Note</span>
                <span className="analysis-row-value">{text(sourceTransparency.note)}</span>
              </div>
            ) : null}
          </div>
        </section>
      )}

      {sources.length > 0 && (
        <section className="analysis-section">
          <h5>References</h5>
          <div className="analysis-rows">
            {sources.slice(0, 12).map((s, idx) => {
              const title = typeof s === "string" ? `Source ${idx + 1}` : s.title || `Source ${idx + 1}`;
              const rawUrl = typeof s === "string" ? s : s.url || s.source_url || s.link || s.href || "";
              const url = normalizeUrl(rawUrl);
              const searchUrl = buildSearchUrl(title);
              const publisher = typeof s === "object" && s ? s.publisher : "";
              const publishedAt = typeof s === "object" && s ? s.published_at : "";
              return (
                <div key={`source-${idx}`} className="analysis-row">
                  <span className="analysis-row-label">{title}</span>
                  <span className="analysis-row-value">
                    {isWebUrl(url) ? (
                      <a href={url} target="_blank" rel="noreferrer">
                        Open Source
                      </a>
                    ) : (
                      <a href={searchUrl} target="_blank" rel="noreferrer">
                        Search Source
                      </a>
                    )}
                    {publisher ? ` | ${publisher}` : ""}
                    {publishedAt ? ` | ${publishedAt}` : ""}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </article>
  );
}

export function PositioningCard({ positioning, isLatest = false }) {
  if (!positioning) return null;
  const { positioning_statement, tagline, target_segment, key_differentiators, proof_points, rationale } = positioning;
  return (
    <div className={`positioning-card-wrap${isLatest ? " positioning-card-latest" : ""}`}>
      {/* Tagline */}
      {tagline && (
        <div className="positioning-tagline">
          &ldquo;{tagline}&rdquo;
        </div>
      )}

      {/* Statement */}
      <article className="compact-card positioning-statement-card">
        <div className="positioning-statement-label">Positioning Statement</div>
        <p className="positioning-statement-text">{positioning_statement || "N/A"}</p>
        {target_segment && (
          <div className="positioning-segment-row">
            <span className="positioning-segment-label">Target Segment</span>
            <span className="positioning-segment-value">{target_segment}</span>
          </div>
        )}
      </article>

      {/* Differentiators + Proof Points side by side */}
      <div className="positioning-two-col">
        {(key_differentiators || []).length > 0 && (
          <article className="compact-card positioning-diff-card">
            <h5>Key Differentiators</h5>
            <ul className="positioning-list">
              {key_differentiators.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </article>
        )}
        {(proof_points || []).length > 0 && (
          <article className="compact-card positioning-proof-card">
            <h5>Proof Points</h5>
            <ul className="positioning-list">
              {proof_points.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </article>
        )}
      </div>

      {/* Rationale */}
      {rationale && (
        <details className="positioning-rationale-details">
          <summary className="positioning-rationale-summary">Why this positioning?</summary>
          <p className="positioning-rationale">{rationale}</p>
        </details>
      )}
    </div>
  );
}

export function ResearchCards({ research }) {
  if (!research) return null;
  const customerInsights = research.target_customer_insights || [];
  const competitorInsights = research.competitor_insights || [];
  const sources = research.sources || [];

  return (
    <div className="rc-wrap">
      {/* Summary hero */}
      {research.research_summary && (
        <div className="rc-summary">
          <div className="rc-summary-icon" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
            </svg>
          </div>
          <p className="rc-summary-text">{research.research_summary}</p>
        </div>
      )}

      {/* Two-column insights */}
      <div className="rc-insights-grid">
        {/* Customer Insights */}
        {customerInsights.length > 0 && (
          <div className="rc-insights-col">
            <div className="rc-col-head">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              <span className="rc-col-title">Customer Insights</span>
              <span className="rc-col-count">{customerInsights.length}</span>
            </div>
            <div className="rc-insight-list">
              {customerInsights.map((x, i) => (
                <div key={i} className="rc-insight-item rc-insight-customer">
                  <span className="rc-insight-theme">{x.theme}</span>
                  <p className="rc-insight-text">{x.insight}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Competitor Insights */}
        {competitorInsights.length > 0 && (
          <div className="rc-insights-col">
            <div className="rc-col-head">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              <span className="rc-col-title">Competitor Insights</span>
              <span className="rc-col-count">{competitorInsights.length}</span>
            </div>
            <div className="rc-insight-list">
              {competitorInsights.map((x, i) => (
                <div key={i} className="rc-insight-item rc-insight-competitor">
                  <span className="rc-insight-theme">{x.theme}</span>
                  <p className="rc-insight-text">{x.insight}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="rc-sources">
          <p className="rc-sources-label">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              style={{ display: "inline", marginRight: 5, verticalAlign: "middle" }}>
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
            Sources Analyzed
          </p>
          <div className="rc-sources-list">
            {sources.map((s, i) => (
              <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                className="rc-source-item">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
                </svg>
                {s.title || s.url}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function StrategyCards({ strategy }) {
  if (!strategy) return null;
  const channels = strategy.prioritized_channels || [];
  const keyMessages = strategy.key_messages || [];
  const primary = channels[0];
  const secondary = channels.slice(1);

  return (
    <div className="sc-wrap">
      {/* Primary channel — hero card */}
      {primary && (
        <div className="sc-primary">
          <div className="sc-primary-head">
            <span className="sc-rank-badge sc-rank-primary">Primary Channel</span>
            <h3 className="sc-primary-name">{primary.channel}</h3>
          </div>
          <p className="sc-primary-why">{primary.why}</p>
          {(primary.weekly_actions || []).length > 0 && (
            <div className="sc-actions-wrap">
              <p className="sc-actions-label">Weekly Actions</p>
              <ul className="sc-actions-list sc-actions-primary">
                {primary.weekly_actions.map((a, i) => (
                  <li key={i} className="sc-action-item">{a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Secondary channels grid */}
      {secondary.length > 0 && (
        <div className="sc-secondary-grid">
          {secondary.map((c, idx) => (
            <div key={`${c.channel}-${idx}`} className="sc-channel-card">
              <div className="sc-channel-head">
                <span className="sc-rank-badge">#{c.priority || idx + 2}</span>
                <h4 className="sc-channel-name">{c.channel}</h4>
              </div>
              <p className="sc-channel-why">{c.why}</p>
              {(c.weekly_actions || []).length > 0 && (
                <ul className="sc-actions-list">
                  {c.weekly_actions.map((a, i) => (
                    <li key={i} className="sc-action-item">{a}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Key messages */}
      {keyMessages.length > 0 && (
        <div className="sc-messages">
          <p className="sc-messages-title">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"
              style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }}>
              <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74z" />
            </svg>
            Key Messages
          </p>
          <div className="sc-messages-list">
            {keyMessages.map((m, i) => (
              <div key={i} className="sc-message-item">
                <span className="sc-message-q">&ldquo;</span>
                <p className="sc-message-text">{m}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function RoadmapCards({ roadmap }) {
  if (!roadmap) return null;
  const weeks = roadmap.weekly_plan || [];
  const milestones = roadmap.milestones || [];

  // Group weeks by phase
  const phaseOrder = [];
  const phaseMap = {};
  weeks.forEach((w) => {
    const key = w.phase || `Month ${Math.ceil((w.week || 1) / 4)}`;
    if (!phaseMap[key]) { phaseMap[key] = []; phaseOrder.push(key); }
    phaseMap[key].push(w);
  });

  const PHASE_COLORS = ["#c72832", "#0f766e", "#7c3aed"];

  return (
    <div className="rm-wrap">
      {/* Milestone tracker */}
      {milestones.length > 0 && (
        <div className="rm-milestones">
          <p className="rm-milestones-title">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
              style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }}>
              <polyline points="9 11 12 14 22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            Key Milestones
          </p>
          <div className="rm-milestones-track">
            {milestones.map((m, i) => (
              <div key={i} className="rm-milestone">
                <div className="rm-milestone-dot" />
                {i < milestones.length - 1 && <div className="rm-milestone-line" />}
                <div className="rm-milestone-body">
                  <span className="rm-milestone-day">Day {m.day}</span>
                  <p className="rm-milestone-goal">{m.goal}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phase sections */}
      {phaseOrder.map((phaseName, pi) => (
        <div key={phaseName} className="rm-phase">
          <div className="rm-phase-header" style={{ borderLeftColor: PHASE_COLORS[pi % PHASE_COLORS.length] }}>
            <span className="rm-phase-num" style={{ background: PHASE_COLORS[pi % PHASE_COLORS.length] }}>
              {pi + 1}
            </span>
            <h4 className="rm-phase-name">{phaseName}</h4>
            <span className="rm-phase-weeks-count">{phaseMap[phaseName].length} weeks</span>
          </div>
          <div className="rm-weeks-grid">
            {phaseMap[phaseName].map((w) => (
              <div key={w.week} className="rm-week-card">
                <div className="rm-week-head">
                  <span className="rm-week-label">Week {w.week}</span>
                  {w.kpi && <span className="rm-week-kpi">{w.kpi}</span>}
                </div>
                <p className="rm-week-objective">{w.objective}</p>
                {(w.daily_actions || []).length > 0 && (
                  <ul className="rm-week-actions">
                    {w.daily_actions.slice(0, 3).map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text || "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button className={`ca-copy-btn${copied ? " ca-copied" : ""}`} onClick={handleCopy}>
      {copied ? (
        <>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

const VISUAL_TYPES = new Set(["logo", "poster", "banner", "social_visual", "social_media_visual"]);
const TYPE_LABELS = {
  social_post: "Social Media Post", instagram_caption: "Instagram Caption",
  google_business_post: "Google Business Post", ad_copy: "Ad Copy",
  sms_campaign: "SMS Campaign", email_newsletter: "Email Newsletter",
  blog_post_intro: "Blog Post Intro", landing_page_copy: "Landing Page Copy",
  press_release: "Press Release", logo: "Logo Concept",
  poster: "Poster / Banner", social_visual: "Social Media Visual",
};

function CopyField({ label, text }) {
  return (
    <div className="ca-field">
      <div className="ca-field-head">
        <span className="ca-field-label">{label}</span>
        <CopyButton text={text} />
      </div>
      <p className="ca-field-text">{text}</p>
    </div>
  );
}

function HashtagList({ tags = [] }) {
  if (!tags.length) return null;
  return (
    <div className="ca-hashtags">
      {tags.map((t, i) => (
        <span key={i} className="ca-hashtag">{t.startsWith("#") ? t : `#${t}`}</span>
      ))}
    </div>
  );
}

function TextAssetCard({ a, idx }) {
  const meta = a.metadata || {};
  const type = a.asset_type || "";

  // Build full-card copy text
  const allText = Object.values(meta)
    .filter((v) => typeof v === "string")
    .join("\n\n");

  // Email newsletter
  if (type === "email_newsletter") {
    const sections = meta.sections || [];
    return (
      <article className="ca-asset-card">
        <div className="ca-asset-head">
          <span className="ca-asset-type">{TYPE_LABELS[type] || type}</span>
          <CopyButton text={allText} />
        </div>
        <div className="ca-asset-body">
          {meta.subject && <CopyField label="Subject Line" text={meta.subject} />}
          {meta.preview_text && <CopyField label="Preview Text" text={meta.preview_text} />}
          {sections.map((s, i) => (
            <div key={i} className="ca-email-section">
              {s.heading && <p className="ca-email-section-heading">{s.heading}</p>}
              {s.body && <p className="ca-field-text">{s.body}</p>}
            </div>
          ))}
          {meta.cta && <CopyField label="CTA" text={meta.cta} />}
          {meta.ps_line && <CopyField label="P.S." text={meta.ps_line} />}
        </div>
      </article>
    );
  }

  // Ad copy
  if (type === "ad_copy") {
    return (
      <article className="ca-asset-card">
        <div className="ca-asset-head">
          <span className="ca-asset-type">{TYPE_LABELS[type] || type}</span>
          <CopyButton text={allText} />
        </div>
        <div className="ca-asset-body">
          <div className="ca-ad-headlines">
            {[meta.headline_1, meta.headline_2, meta.headline_3].filter(Boolean).map((h, i) => (
              <div key={i} className="ca-ad-headline-row">
                <span className="ca-ad-h-num">H{i + 1}</span>
                <span className="ca-ad-h-text">{h}</span>
                <CopyButton text={h} />
              </div>
            ))}
          </div>
          {[meta.description_1, meta.description_2].filter(Boolean).map((d, i) => (
            <CopyField key={i} label={`Description ${i + 1}`} text={d} />
          ))}
          {meta.cta && <CopyField label="CTA" text={meta.cta} />}
          {meta.platform_notes && <p className="ca-field-text ca-muted">{meta.platform_notes}</p>}
        </div>
      </article>
    );
  }

  // Blog post
  if (type === "blog_post_intro") {
    const outline = meta.outline || [];
    const keywords = meta.keywords || [];
    return (
      <article className="ca-asset-card">
        <div className="ca-asset-head">
          <span className="ca-asset-type">{TYPE_LABELS[type] || type}</span>
          <CopyButton text={allText} />
        </div>
        <div className="ca-asset-body">
          {meta.title && <CopyField label="Title" text={meta.title} />}
          {meta.meta_description && <CopyField label="Meta Description" text={meta.meta_description} />}
          {meta.intro && <CopyField label="Intro" text={meta.intro} />}
          {outline.length > 0 && (
            <div className="ca-field">
              <span className="ca-field-label">Outline</span>
              <ol className="ca-outline-list">
                {outline.map((item, i) => <li key={i}>{item}</li>)}
              </ol>
            </div>
          )}
          {keywords.length > 0 && (
            <div className="ca-hashtags" style={{ marginTop: 8 }}>
              {keywords.map((k, i) => <span key={i} className="ca-hashtag">{k}</span>)}
            </div>
          )}
        </div>
      </article>
    );
  }

  // Landing page copy
  if (type === "landing_page_copy") {
    const sections = meta.sections || [];
    const trust = meta.trust_signals || [];
    return (
      <article className="ca-asset-card">
        <div className="ca-asset-head">
          <span className="ca-asset-type">{TYPE_LABELS[type] || type}</span>
          <CopyButton text={allText} />
        </div>
        <div className="ca-asset-body">
          {meta.headline && <CopyField label="Headline" text={meta.headline} />}
          {meta.subheadline && <CopyField label="Subheadline" text={meta.subheadline} />}
          {sections.map((s, i) => (
            <div key={i} className="ca-email-section">
              {s.heading && <p className="ca-email-section-heading">{s.heading}</p>}
              {s.body && <p className="ca-field-text">{s.body}</p>}
            </div>
          ))}
          {meta.cta && <CopyField label="CTA" text={meta.cta} />}
          {trust.length > 0 && (
            <div className="ca-field">
              <span className="ca-field-label">Trust Signals</span>
              <ul className="ca-trust-list">
                {trust.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </div>
      </article>
    );
  }

  // Social / Instagram / generic text
  const caption = meta.caption || meta.body || meta.message || meta.intro || meta.lead_paragraph || "";
  const hook = meta.hook || meta.subject || meta.headline || meta.title || "";
  const hashtags = meta.hashtags || [];
  const imagePrompt = meta.image_prompt || "";

  return (
    <article className="ca-asset-card">
      <div className="ca-asset-head">
        <span className="ca-asset-type">{TYPE_LABELS[type] || type}</span>
        <CopyButton text={[hook, caption, meta.cta].filter(Boolean).join("\n\n")} />
      </div>
      <div className="ca-asset-body">
        {hook && <CopyField label="Hook / Headline" text={hook} />}
        {caption && <CopyField label="Caption / Body" text={caption} />}
        {meta.cta && <CopyField label="CTA" text={meta.cta} />}
        {hashtags.length > 0 && <HashtagList tags={hashtags} />}
        {imagePrompt && (
          <div className="ca-image-prompt">
            <span className="ca-field-label">Suggested Visual</span>
            <p className="ca-field-text ca-muted">{imagePrompt}</p>
          </div>
        )}
      </div>
    </article>
  );
}

function downloadBase64Image(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  a.click();
}

function VisualAssetCard({ a, idx }) {
  const meta = a.metadata || {};
  const brief = meta.design_brief || {};
  const type = a.asset_type || "";
  const palette = brief.color_palette || [];
  const imageData = meta.image_data || null;
  const dalleError = meta.dalle_error || null;
  const label = TYPE_LABELS[type] || type;

  return (
    <article className="vc-card">
      {/* Image stage */}
      <div className="vc-stage">
        {imageData ? (
          <>
            <img src={imageData} alt={`${label} visual`} className="vc-image" />
            <div className="vc-stage-overlay">
              <span className="vc-badge">{label}</span>
              <button
                className="vc-dl-btn"
                onClick={() => downloadBase64Image(imageData, `${type}-${a.id || idx}.png`)}
                title="Download PNG"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
              </button>
            </div>
          </>
        ) : (
          <div className="vc-no-image">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="3" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            <span className="vc-badge" style={{ position: "static", marginTop: 12 }}>{label}</span>
            <p className="vc-no-image-text">Image not generated</p>
            {dalleError && <p className="vc-no-image-err">{dalleError}</p>}
          </div>
        )}
      </div>

      {/* Design Brief — collapsed by default */}
      <details className="ca-brief-details">
        <summary className="ca-brief-summary">Design Brief</summary>
        <div className="ca-asset-body">
          {brief.concept && <CopyField label="Concept" text={brief.concept} />}
          {brief.style && <CopyField label="Style" text={brief.style} />}
          {brief.mood && <CopyField label="Mood" text={brief.mood} />}
          {brief.typography && <CopyField label="Typography" text={brief.typography} />}
          {palette.length > 0 && (
            <div className="ca-field">
              <span className="ca-field-label">Colour Palette</span>
              <div className="ca-palette">
                {palette.map((hex, i) => (
                  <div key={i} className="ca-swatch-wrap">
                    <div className="ca-swatch" style={{ background: hex }} title={hex} />
                    <span className="ca-swatch-hex">{hex}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {brief.usage_notes && <CopyField label="Usage Notes" text={brief.usage_notes} />}
          {meta.dalle_prompt && (
            <details className="ca-dalle-details">
              <summary className="ca-dalle-summary">View DALL-E Prompt</summary>
              <p className="ca-field-text ca-muted">{meta.dalle_prompt}</p>
            </details>
          )}
        </div>
      </details>
    </article>
  );
}

export function ContentAssetCards({ assets = [] }) {
  if (!assets.length) return null;
  return (
    <div className="ca-wrap">
      {assets.map((a, idx) =>
        VISUAL_TYPES.has(a.asset_type)
          ? <VisualAssetCard key={a.id || idx} a={a} idx={idx} />
          : <TextAssetCard key={a.id || idx} a={a} idx={idx} />
      )}
    </div>
  );
}
