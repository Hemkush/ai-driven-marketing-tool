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
      <h5>🕐 Hours Gap Analysis</h5>
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
  { key: "strengths",    label: "Strengths",    emoji: "💪", cls: "swot-s" },
  { key: "weaknesses",   label: "Weaknesses",   emoji: "⚠️",  cls: "swot-w" },
  { key: "opportunities",label: "Opportunities",emoji: "🚀", cls: "swot-o" },
  { key: "threats",      label: "Threats",      emoji: "🔥", cls: "swot-t" },
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
        {SWOT_CONFIG.map(({ key, label, emoji, cls }) => (
          <div key={key} className={`swot-quadrant ${cls}`}>
            <div className="swot-quadrant-head">
              <span className="swot-emoji">{emoji}</span>
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
  const avgPriceLabel = ["Free", "$", "$$", "$$$", "$$$$"][Math.round(market.avg_price_level)] || "N/A";
  const densityLabel = DENSITY_LABEL[market.market_density] || market.market_density || "N/A";

  return (
    <div className="benchmarking-root">
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
            <span className="snapshot-val">{densityLabel}</span>
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
              <h5>How to Win</h5>
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

                {/* AI Insights */}
                <div className="competitor-insights">
                  {c.business_model && (
                    <div className="insight-row">
                      <span className="insight-label">Business Model</span>
                      <span className="insight-value">{c.business_model}</span>
                    </div>
                  )}
                  {c.pricing_notes && (
                    <div className="insight-row">
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
                      <span className="insight-label">Special Services</span>
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
                    <div className="insight-row">
                      <span className="insight-label">Strategy</span>
                      <span className="insight-value">{c.how_they_compete}</span>
                    </div>
                  )}
                  {c.review_summary && (
                    <div className="insight-row">
                      <span className="insight-label">Customer Sentiment</span>
                      <span className="insight-value">{c.review_summary}</span>
                    </div>
                  )}
                </div>

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
                  <a href={c.google_maps_url} target="_blank" rel="noreferrer" className="maps-link">
                    View on Google Maps →
                  </a>
                )}
              </article>
            );
          })}
        </div>
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
                {basic.location && <p className="persona-location">📍 {basic.location}</p>}
              </div>
            </div>

            {/* Psychographic */}
            <div className="persona-section">
              <div className="persona-section-title">Goals & Motivations</div>
              <p className="persona-section-text">{psycho.goals_and_motivations || "N/A"}</p>
            </div>
            <div className="persona-section persona-pain">
              <div className="persona-section-title">Pain Points</div>
              <p className="persona-section-text">{psycho.pain_points_and_frustrations || "N/A"}</p>
            </div>
            {psycho.values_and_priorities && (
              <div className="persona-section">
                <div className="persona-section-title">Values & Priorities</div>
                <p className="persona-section-text">{psycho.values_and_priorities}</p>
              </div>
            )}

            {/* Behavioral */}
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

            {/* Key message */}
            {engage.key_messages_that_convert && (
              <div className="persona-key-message">
                <span className="persona-key-label">Key Message</span>
                <span className="persona-key-text">&ldquo;{engage.key_messages_that_convert}&rdquo;</span>
              </div>
            )}

            {/* Best time */}
            {engage.best_times_to_reach && (
              <p className="persona-best-time">🕐 Best time to reach: {engage.best_times_to_reach}</p>
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
        <p className="positioning-rationale">{rationale}</p>
      )}
    </div>
  );
}

export function ResearchCards({ research }) {
  if (!research) return null;
  return (
    <div className="card-grid">
      <article className="compact-card">
        <h4>Research Summary</h4>
        <p>{research.research_summary || "N/A"}</p>
      </article>
      <article className="compact-card">
        <h4>Customer Insights</h4>
        {(research.target_customer_insights || []).map((x, idx) => (
          <p key={idx}>
            <b>{x.theme}:</b> {x.insight}
          </p>
        ))}
      </article>
      <article className="compact-card">
        <h4>Competitor Insights</h4>
        {(research.competitor_insights || []).map((x, idx) => (
          <p key={idx}>
            <b>{x.theme}:</b> {x.insight}
          </p>
        ))}
      </article>
      <article className="compact-card">
        <h4>Sources</h4>
        {(research.sources || []).map((s, idx) => (
          <p key={idx}>
            <b>{s.title}</b> - {s.url}
          </p>
        ))}
      </article>
    </div>
  );
}

export function StrategyCards({ strategy }) {
  if (!strategy) return null;
  return (
    <div className="card-grid">
      {(strategy.prioritized_channels || []).map((c, idx) => (
        <article className="compact-card" key={`${c.channel}-${idx}`}>
          <h4>
            #{c.priority || idx + 1} {c.channel}
          </h4>
          <p>{c.why}</p>
          <p>
            <b>Actions:</b> {(c.weekly_actions || []).join(" | ") || "N/A"}
          </p>
        </article>
      ))}
      <article className="compact-card">
        <h4>Key Messages</h4>
        <p>{(strategy.key_messages || []).join(" | ") || "N/A"}</p>
      </article>
    </div>
  );
}

export function RoadmapCards({ roadmap }) {
  if (!roadmap) return null;
  const weeks = roadmap.weekly_plan || [];
  return (
    <div className="card-grid">
      <article className="compact-card">
        <h4>Milestones</h4>
        {(roadmap.milestones || []).map((m, idx) => (
          <p key={idx}>
            <b>Day {m.day}:</b> {m.goal}
          </p>
        ))}
      </article>
      {weeks.slice(0, 6).map((w) => (
        <article className="compact-card" key={w.week}>
          <h4>
            Week {w.week} - {w.phase}
          </h4>
          <p>{w.objective}</p>
          <p>
            <b>Owner:</b> {w.owner} | <b>KPI:</b> {w.kpi}
          </p>
        </article>
      ))}
    </div>
  );
}

export function ContentAssetCards({ assets = [] }) {
  return (
    <div className="card-grid">
      {assets.map((a) => (
        <article className="compact-card" key={a.id || a.storage_uri}>
          <h4>{a.asset_type}</h4>
          <div className="meta-row">
            <span>Status: {a.status || "ready"}</span>
          </div>
          <p>
            <b>Storage:</b> {a.storage_uri}
          </p>
          <p>
            <b>Title:</b> {a.metadata?.title || a.metadata?.headline || "N/A"}
          </p>
          <p>
            <b>Preview:</b>{" "}
            {a.metadata?.caption ||
              a.metadata?.description ||
              a.metadata?.body ||
              a.metadata?.cta ||
              "No preview"}
          </p>
        </article>
      ))}
    </div>
  );
}
