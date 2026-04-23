function pretty(value) {
  return JSON.stringify(value, null, 2);
}

export default function PipelinePanel({
  runAnalysis,
  busy,
  activeProjectId,
  analysis,
  generatePositioning,
  positioningFeedback,
  setPositioningFeedback,
  refinePositioning,
  positioning,
  runResearch,
  research,
  generatePersonas,
  personas,
  generateRoadmap,
  roadmap,
  assetType,
  setAssetType,
  assetPrompt,
  setAssetPrompt,
  numVariants,
  setNumVariants,
  generateContent,
  loadContentAssets,
  contentAssets,
}) {
  return (
    <>
      <h3>Step 2 - Analysis</h3>
      <button onClick={runAnalysis} disabled={busy || !activeProjectId}>
        Run Analysis
      </button>
      {analysis && <pre>{pretty(analysis)}</pre>}

      <h3>Step 3 - Positioning</h3>
      <button onClick={generatePositioning} disabled={busy || !activeProjectId}>
        Generate Positioning
      </button>
      <br />
      <textarea
        placeholder="Owner feedback for refinement"
        value={positioningFeedback}
        onChange={(e) => setPositioningFeedback(e.target.value)}
        rows={3}
        style={{ width: "100%", maxWidth: 700, marginTop: 8 }}
      />
      <br />
      <button onClick={refinePositioning} disabled={busy || !positioningFeedback.trim()}>
        Refine Positioning
      </button>
      {positioning && <pre>{pretty(positioning)}</pre>}

      <h3>Step 4 - Research</h3>
      <button onClick={runResearch} disabled={busy || !activeProjectId}>
        Run Research
      </button>
      {research && <pre>{pretty(research)}</pre>}

      <h3>Step 5 - Personas</h3>
      <button onClick={generatePersonas} disabled={busy || !activeProjectId}>
        Generate Personas
      </button>
      {personas.length > 0 && <pre>{pretty(personas)}</pre>}

      <h3>Step 6 - Roadmap</h3>
      <button onClick={generateRoadmap} disabled={busy || !activeProjectId}>
        Generate Roadmap
      </button>
      {roadmap && <pre>{pretty(roadmap)}</pre>}

      <h3>Step 8 - Content Studio</h3>
      <input
        placeholder="Asset type (social_post, logo, ad_copy...)"
        value={assetType}
        onChange={(e) => setAssetType(e.target.value)}
      />
      <br />
      <textarea
        placeholder="Asset prompt"
        value={assetPrompt}
        onChange={(e) => setAssetPrompt(e.target.value)}
        rows={3}
        style={{ width: "100%", maxWidth: 700 }}
      />
      <br />
      <input
        type="number"
        min={1}
        max={5}
        value={numVariants}
        onChange={(e) => setNumVariants(Number(e.target.value))}
      />
      <br />
      <button onClick={generateContent} disabled={busy || !activeProjectId}>
        Generate Content Assets
      </button>
      <button onClick={loadContentAssets} style={{ marginLeft: 8 }} disabled={busy || !activeProjectId}>
        Load Stored Assets
      </button>
      {contentAssets.length > 0 && <pre>{pretty(contentAssets)}</pre>}
    </>
  );
}
