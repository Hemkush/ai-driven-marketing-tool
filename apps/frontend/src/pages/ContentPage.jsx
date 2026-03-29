import { NextStepCta } from "../components/UiBlocks";
import { ContentAssetCards } from "../components/CompactCards";
import { LoadingSkeleton } from "../components/LoadingSkeleton";

const ASSET_TYPES = [
  { label: "Social Media Post",           icon: "M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" },
  { label: "Instagram Caption",           icon: "M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zm1.5-4.87h.01M7.88 2.22A2 2 0 0 0 6 4.1V20a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.1a2 2 0 0 0-1.88-1.88Z" },
  { label: "Google Business Post",        icon: "M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z M12 10m-3 0a3 3 0 1 0 6 0 3 3 0 0 0-6 0" },
  { label: "Email Newsletter",            icon: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6" },
  { label: "Blog Post Intro",             icon: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7 M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" },
  { label: "Landing Page Copy",           icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8" },
  { label: "SMS / Text Campaign",         icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" },
  { label: "Ad Copy (Google / Meta)",     icon: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4 M10 17l5-5-5-5 M13.8 12H3" },
];

export default function ContentPage({ workflow }) {
  const { state, set, actions } = workflow;
  const hasAssets = state.contentAssets?.length > 0;
  const hasRoadmap = !!state.roadmap;

  return (
    <div className="csp-page">
      {/* Page header */}
      <div className="csp-header">
        <div className="csp-header-text">
          <h3 className="csp-title">Content Studio</h3>
          <p className="csp-desc">
            Generate on-brand content assets for any channel — social posts, emails, ads, blog intros, and more.
            Each asset is written using your positioning, personas, and roadmap as context.
          </p>
        </div>
        {hasAssets && (
          <button
            className="btn ghost"
            onClick={actions.loadContentAssets}
            disabled={state.busy || !state.activeProjectId}
          >
            Load Saved Assets
          </button>
        )}
      </div>

      {/* Content generator form */}
      <div className="csp-form-card">
        <p className="csp-form-title">Generate a Content Asset</p>

        {/* Asset type chip grid */}
        <div className="csp-field">
          <label className="csp-label">Asset Type</label>
          <div className="csp-type-chips">
            {ASSET_TYPES.map((t) => (
              <button
                key={t.label}
                className={`csp-type-chip${state.assetType === t.label ? " active" : ""}`}
                onClick={() => set.setAssetType(state.assetType === t.label ? "" : t.label)}
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

        {/* Context + variants row */}
        <div className="csp-form-row">
          <div className="csp-field csp-field-grow">
            <label className="csp-label">Additional Context or Focus</label>
            <textarea
              className="csp-textarea"
              placeholder="e.g. Promote our summer special, target weekend clients, tone should be warm and local…"
              value={state.assetPrompt}
              onChange={(e) => set.setAssetPrompt(e.target.value)}
              rows={3}
            />
          </div>
          <div className="csp-field csp-field-shrink">
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
          </div>
        </div>
        <div className="csp-form-actions">
          <button
            className="btn"
            onClick={actions.generateContent}
            disabled={state.busy || !state.activeProjectId || !state.assetType}
          >
            {state.busy ? "Generating…" : "Generate Content →"}
          </button>
          {!hasAssets && (
            <button
              className="btn ghost"
              onClick={actions.loadContentAssets}
              disabled={state.busy || !state.activeProjectId}
            >
              Load Saved Assets
            </button>
          )}
        </div>
        {!hasRoadmap && (
          <p className="csp-form-hint">
            Tip: Complete your Roadmap first — the AI uses it to write assets that fit your execution plan.
          </p>
        )}
      </div>

      {/* Loading */}
      {state.busy && (
        <LoadingSkeleton lines={4} message="Generating your content assets…" />
      )}

      {/* Assets */}
      {!state.busy && hasAssets && (
        <div className="csp-assets">
          <div className="csp-assets-meta">
            <span className="csp-assets-count">
              {state.contentAssets.length} asset{state.contentAssets.length !== 1 ? "s" : ""}
            </span>
            <span className="csp-assets-hint">Ready to copy and schedule</span>
          </div>
          <ContentAssetCards assets={state.contentAssets} />
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
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <h3 className="csp-empty-title">No Content Assets Yet</h3>
          <p className="csp-empty-sub">
            Choose an asset type above and click Generate Content to create your first asset.
          </p>
        </div>
      )}

      <NextStepCta to="/projects" label="Back to Projects" disabled={false} />
    </div>
  );
}
