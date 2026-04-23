import { useNavigate } from "react-router-dom";
import { NextStepCta } from "../components/UiBlocks";
import { ContentAssetCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustBadge } from "../components/TrustBadge";
import { AiChip } from "../components/AiChip";
import { FeedbackThumbs } from "../components/FeedbackThumbs";

const ASSET_CATEGORIES = [
  {
    label: "Text Content",
    types: [
      { value: "social_post",          label: "Social Media Post",      icon: "M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" },
      { value: "instagram_caption",    label: "Instagram Caption",      icon: "M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zm1.5-4.87h.01M7.88 2.22A2 2 0 0 0 6 4.1V20a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.1a2 2 0 0 0-1.88-1.88Z" },
      { value: "google_business_post", label: "Google Business Post",   icon: "M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0zM12 10m-3 0a3 3 0 1 0 6 0 3 3 0 0 0-6 0" },
      { value: "ad_copy",              label: "Ad Copy (Google/Meta)",  icon: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13.8 12H3" },
      { value: "sms_campaign",         label: "SMS Campaign",           icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" },
    ],
  },
  {
    label: "Structured Content",
    types: [
      { value: "email_newsletter",  label: "Email Newsletter",   icon: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6" },
      { value: "blog_post_intro",   label: "Blog Post Intro",    icon: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" },
      { value: "landing_page_copy", label: "Landing Page Copy",  icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" },
      { value: "press_release",     label: "Press Release",      icon: "M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10l6 6v10a2 2 0 0 1-2 2zM17 21v-8H7v8M7 3v5h8" },
    ],
  },
  {
    label: "Visual Assets",
    badge: "AI-Generated Image + Design Brief",
    types: [
      { value: "logo",          label: "Logo Concept",         icon: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" },
      { value: "poster",        label: "Poster / Banner",      icon: "M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" },
      { value: "social_visual", label: "Social Media Visual",  icon: "M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" },
    ],
  },
];

const TONES = [
  { value: "professional", label: "Professional", desc: "Formal & authoritative" },
  { value: "friendly",     label: "Friendly",     desc: "Warm & conversational" },
  { value: "urgent",       label: "Urgent",       desc: "Action-oriented" },
  { value: "playful",      label: "Playful",      desc: "Fun & energetic" },
  { value: "bold",         label: "Bold",         desc: "Direct & striking" },
];

export default function ContentPage({ workflow }) {
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const hasAssets = state.contentAssets?.length > 0;
  const hasRoadmap = !!state.roadmap;

  const selectedCategory = ASSET_CATEGORIES.find((c) =>
    c.types.some((t) => t.value === state.assetType)
  );
  const isVisual = selectedCategory?.label === "Visual Assets";

  const firstAsset = state.contentAssets?.[0];

  return (
    <div className="csp-page">
      {/* Gate error */}
      {state.gateError?.agent === "content_studio" && (
        <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: "8px", padding: "14px 16px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", color: "#9a3412", fontWeight: 500 }}>
            ⚠ {state.gateError.message}
          </p>
          <button className="btn ghost" style={{ marginTop: "10px" }} onClick={() => navigate("/questionnaire")}>
            Back to Questionnaire →
          </button>
        </div>
      )}

      {/* Header */}
      <div className="csp-header">
        <div className="csp-header-text">
          <h3 className="csp-title">Content Studio</h3>
          <p className="csp-desc">
            Generate on-brand content for any channel. Visual assets include an AI-generated image
            plus a full design brief. All content is written using your positioning, personas, and strategy.
          </p>
        </div>
        {hasAssets && (
          <button className="btn ghost" onClick={actions.loadContentAssets}
            disabled={state.busy || !state.activeProjectId}>
            Load Saved Assets
          </button>
        )}
      </div>

      {/* Generator form */}
      <div className="csp-form-card">
        <p className="csp-form-title">Generate a Content Asset</p>

        {/* Category + type picker */}
        {ASSET_CATEGORIES.map((cat) => (
          <div key={cat.label} className="csp-field csp-category-group">
            <div className="csp-category-label">
              {cat.label}
              {cat.badge && <span className="csp-category-badge">{cat.badge}</span>}
            </div>
            <div className="csp-type-chips">
              {cat.types.map((t) => (
                <button
                  key={t.value}
                  className={`csp-type-chip${state.assetType === t.value ? " active" : ""}`}
                  onClick={() => set.setAssetType(state.assetType === t.value ? "" : t.value)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d={t.icon} />
                  </svg>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        ))}

        {/* Tone selector */}
        <div className="csp-field">
          <label className="csp-label">Brand Tone</label>
          <div className="csp-tone-row">
            {TONES.map((t) => (
              <button
                key={t.value}
                className={`csp-tone-btn${state.assetTone === t.value ? " active" : ""}`}
                onClick={() => set.setAssetTone(t.value)}
                title={t.desc}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Context */}
        <div className="csp-field">
          <label className="csp-label">
            {isVisual ? "Visual Direction & Context" : "Additional Context or Focus"}
          </label>
          <textarea
            className="csp-textarea"
            placeholder={
              isVisual
                ? "e.g. Use deep navy and gold tones, modern sans-serif, convey premium quality…"
                : "e.g. Promote our summer special, target weekend clients, warm and local tone…"
            }
            value={state.assetPrompt}
            onChange={(e) => set.setAssetPrompt(e.target.value)}
            rows={3}
          />
        </div>

        {/* Variants — right below context */}
        <div className="csp-field">
          <label className="csp-label">Variants</label>
          <div className="csp-variants-row">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                className={`csp-variant-btn${state.numVariants === n ? " active" : ""}`}
                onClick={() => set.setNumVariants(n)}
              >
                {n}
              </button>
            ))}
          </div>
          {isVisual && (
            <p className="csp-variants-note">Each variant = 1 image + design brief</p>
          )}
        </div>

        {isVisual && (
          <div className="csp-visual-notice">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            DALL-E 3 generates the image; a detailed design brief is always included as a reference.
            Image URLs expire after 1 hour — save them promptly.
          </div>
        )}

        <div className="csp-form-actions">
          <button
            className="btn"
            onClick={actions.generateContent}
            disabled={state.busy || !state.activeProjectId || !state.assetType}
          >
            {state.busy ? "Generating…" : isVisual ? "Generate Visual →" : "Generate Content →"}
          </button>
          {!hasAssets && (
            <button className="btn ghost" onClick={actions.loadContentAssets}
              disabled={state.busy || !state.activeProjectId}>
              Load Saved Assets
            </button>
          )}
        </div>

        {!hasRoadmap && (
          <p className="csp-form-hint">
            Tip: Complete your Roadmap first — the AI uses it to write content that fits your execution plan.
          </p>
        )}
      </div>

      {/* Loading */}
      {state.busy && (
        <LoadingSkeleton lines={4} message={
          isVisual
            ? "Generating image and design brief — this takes ~20 seconds…"
            : "Generating your content assets…"
        } />
      )}

      {/* Assets — grouped by type */}
      {!state.busy && hasAssets && (
        <div className="csp-assets">
          <div className="csp-assets-meta">
            <span className="csp-assets-count">
              {state.contentAssets.length} asset{state.contentAssets.length !== 1 ? "s" : ""}
            </span>
            <AiChip />
            <TrustBadge score={firstAsset?.quality_score} />
            <span className="csp-assets-hint">Ready to copy, download, or schedule</span>
            <button className="csp-clear-all-btn" onClick={actions.clearAllAssets}>
              Clear all
            </button>
          </div>
          <div style={{ marginTop: "8px" }}>
            <FeedbackThumbs projectId={state.activeProjectId} agent="content_studio" qualityScore={firstAsset?.quality_score} />
          </div>
          {(() => {
            // Group assets by type, preserving generation order (newest first)
            const groups = [];
            const seen = new Map();
            state.contentAssets.forEach((a) => {
              const t = a.asset_type || "other";
              if (!seen.has(t)) { seen.set(t, []); groups.push(t); }
              seen.get(t).push(a);
            });
            return groups.map((type) => {
              const items = seen.get(type);
              const label = ASSET_CATEGORIES.flatMap((c) => c.types)
                .find((t) => t.value === type)?.label || type.replace(/_/g, " ");
              return (
                <div key={type} className="csp-type-group">
                  <div className="csp-type-group-head">
                    <span className="csp-type-group-label">{label}</span>
                    <span className="csp-type-group-count">
                      {items.length} variant{items.length !== 1 ? "s" : ""}
                    </span>
                    <button
                      className="csp-type-group-clear"
                      onClick={() => actions.clearAssetsByType(type)}
                      title={`Remove all ${label} assets`}
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5"
                        strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Clear
                    </button>
                  </div>
                  <ContentAssetCards assets={items} />
                </div>
              );
            });
          })()}
        </div>
      )}

      {/* Empty */}
      {!state.busy && !hasAssets && (
        <div className="csp-empty">
          <div className="csp-empty-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <h3 className="csp-empty-title">No Content Assets Yet</h3>
          <p className="csp-empty-sub">
            Choose a content type above and click Generate to create your first asset.
          </p>
        </div>
      )}

      <NextStepCta to="/projects" label="Back to Projects" disabled={false} />
    </div>
  );
}
