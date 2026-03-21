export function PersonaCards({ personas = [] }) {
  return (
    <div className="card-grid">
      {personas.map((p) => {
        const profile = p.profile || p;
        return (
          <article key={p.id || p.name} className="compact-card">
            <h4>{p.name || profile.name || "Persona"}</h4>
            <div className="meta-row">
              <span>{profile.basic_profile?.occupation || "N/A"}</span>
              <span>{profile.basic_profile?.location || "N/A"}</span>
              <span>{profile.basic_profile?.income || "N/A"}</span>
            </div>
            <p>
              <b>Goals:</b> {profile.psychographic_profile?.goals_and_motivations || "N/A"}
            </p>
            <p>
              <b>Pain Points:</b> {profile.psychographic_profile?.pain_points_and_frustrations || "N/A"}
            </p>
            <p>
              <b>Channels:</b>{" "}
              {(profile.engagement_strategy?.preferred_channels || []).join(", ") || "N/A"}
            </p>
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
        <h4>Marketing Analysis Report</h4>
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
            {!!executive.market_outlook && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Market Outlook</div>
                <p className="analysis-group-text">{executive.market_outlook}</p>
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
            {!!deep.overall_outlook && (
              <div className="analysis-group-block">
                <div className="analysis-group-title">Overall Outlook</div>
                <p className="analysis-group-text">{deep.overall_outlook}</p>
              </div>
            )}
          </div>
        </section>
      )}
      {section("Market Sizing", [
        market.tam_estimate_usd ? `TAM: ${market.tam_estimate_usd}` : "",
        market.sam_estimate_usd ? `SAM: ${market.sam_estimate_usd}` : "",
        market.som_estimate_usd ? `SOM: ${market.som_estimate_usd}` : "",
        market.geography_assumption ? `Geography: ${market.geography_assumption}` : "",
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
                <span className="analysis-row-label">{s.segment_name || `Segment ${idx + 1}`}</span>
                <span className="analysis-row-value">{s.notes || "No notes"}</span>
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
              <span className="analysis-row-value">{sourceTransparency.verification_level || "N/A"}</span>
            </div>
            {sourceTransparency.note ? (
              <div className="analysis-row">
                <span className="analysis-row-label">Note</span>
                <span className="analysis-row-value">{sourceTransparency.note}</span>
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

export function PositioningCard({ positioning }) {
  if (!positioning) return null;
  return (
    <div className="card-grid">
      <article className="compact-card">
        <h4>Positioning Statement</h4>
        <p>{positioning.positioning_statement || "N/A"}</p>
        <p>
          <b>Target Segment:</b> {positioning.target_segment || "N/A"}
        </p>
      </article>
      <article className="compact-card">
        <h4>Differentiators</h4>
        {(positioning.key_differentiators || []).map((d, idx) => (
          <p key={idx}>- {d}</p>
        ))}
      </article>
      <article className="compact-card">
        <h4>Proof Points</h4>
        {(positioning.proof_points || []).map((d, idx) => (
          <p key={idx}>- {d}</p>
        ))}
        <p>
          <b>Rationale:</b> {positioning.rationale || "N/A"}
        </p>
      </article>
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
