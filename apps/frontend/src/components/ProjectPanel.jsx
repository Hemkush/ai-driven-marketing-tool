import { useState } from "react";
import {
  CompetitorCards,
  ContentAssetCards,
  PersonaCards,
  PositioningCard,
  ResearchCards,
  RoadmapCards,
  StrategyCards,
} from "./CompactCards";

// ── Workflow steps (matches AppShell order) ───────────────────────
const TIMELINE_STEPS = [
  { route: "/projects",      label: "Profile",      n: "01" },
  { route: "/questionnaire", label: "Discovery",    n: "02" },
  { route: "/analysis",      label: "Benchmarking", n: "03" },
  { route: "/positioning",   label: "Positioning",  n: "04" },
  { route: "/personas",      label: "Personas",     n: "05" },
  { route: "/research",      label: "Research",     n: "06" },
  { route: "/strategy",      label: "Strategy",     n: "07" },
  { route: "/roadmap",       label: "Roadmap",      n: "08" },
  { route: "/content",       label: "Content",      n: "09" },
];

function projectInitials(name = "") {
  return (
    name
      .split(" ")
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase() || "")
      .join("") || "BP"
  );
}

// ── Small reusable pieces ─────────────────────────────────────────

function FormField({ label, children }) {
  return (
    <div className="pp-field">
      <label className="pp-label">{label}</label>
      {children}
    </div>
  );
}

function WorkspaceRow({ project, isActive, onSelect }) {
  return (
    <button
      type="button"
      className={`pp-workspace-row${isActive ? " active" : ""}`}
      onClick={() => onSelect(String(project.id))}
    >
      <div className="pp-workspace-avatar">{projectInitials(project.name)}</div>
      <div className="pp-workspace-info">
        <div className="pp-workspace-name">{project.name}</div>
        <div className="pp-workspace-meta">
          {project.business_address || "No location set"}
        </div>
      </div>
      {isActive ? (
        <span className="pp-workspace-active-badge">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Active
        </span>
      ) : (
        <span className="pp-workspace-select-hint">Select</span>
      )}
    </button>
  );
}

function SessionCard({ session, isActive, onClick }) {
  const isDone = session.status === "completed";
  const date = session.updated_at
    ? new Date(session.updated_at).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric",
      })
    : "Recent";
  return (
    <button
      type="button"
      className={`pp-session-card${isActive ? " active" : ""}`}
      onClick={onClick}
    >
      <div className="pp-session-card-head">
        <span className={`pp-session-badge ${isDone ? "done" : "live"}`}>
          {isDone ? (
            <>
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Completed
            </>
          ) : (
            <><span className="pp-badge-dot" />In Progress</>
          )}
        </span>
        <span className="pp-session-date">{date}</span>
      </div>
      <div className="pp-session-card-answered">
        <span className="pp-session-answered-n">{session.answered_count}</span>
        <span className="pp-session-answered-l">questions answered</span>
      </div>
      <p className="pp-session-card-q">
        {session.latest_answered_question || session.current_question || "No responses captured yet."}
      </p>
    </button>
  );
}

function SessionTimeline({ workflowProgress }) {
  const doneCount = TIMELINE_STEPS.filter((s) => workflowProgress[s.route]).length;
  return (
    <div className="pp-timeline-wrap">
      <div className="pp-timeline-header">
        <span className="pp-timeline-title">Workflow Progress</span>
        <span className="pp-timeline-count">{doneCount} of {TIMELINE_STEPS.length} complete</span>
      </div>
      <div className="pp-timeline">
        {TIMELINE_STEPS.map((step, i) => {
          const isDone = Boolean(workflowProgress[step.route]);
          const prevDone = i === 0 || Boolean(workflowProgress[TIMELINE_STEPS[i - 1].route]);
          const isCurrent = !isDone && prevDone;
          return (
            <div
              key={step.route}
              className={`pp-timeline-step${isDone ? " done" : ""}${isCurrent ? " current" : ""}`}
              title={step.label}
            >
              <div className="pp-timeline-node">
                {isDone ? (
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <span className="pp-timeline-n">{step.n}</span>
                )}
              </div>
              <span className="pp-timeline-label">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ArtifactBlock({ stepN, title, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="pp-artifact">
      <button type="button" className="pp-artifact-head" onClick={() => setOpen((o) => !o)}>
        <div className="pp-artifact-head-left">
          <span className="pp-artifact-n">Step {stepN}</span>
          <span className="pp-artifact-title">{title}</span>
        </div>
        <svg
          className={`pp-artifact-chevron${open ? " open" : ""}`}
          width="15" height="15" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && <div className="pp-artifact-body">{children}</div>}
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────

export default function ProjectPanel({
  projectName,
  setProjectName,
  projectDescription,
  setProjectDescription,
  projectBusinessAddress,
  setProjectBusinessAddress,
  createProject,
  loadProjects,
  busy,
  activeProjectId,
  setActiveProjectId,
  projects,
  activeProject,
  projectSessions,
  selectedProjectSessionId,
  setSelectedProjectSessionId,
  selectProjectSession,
  selectedProjectSessionDetail,
  selectedProjectSessionWorkflow,
  onStartWorkflow,
}) {
  const workflowSnapshot = selectedProjectSessionWorkflow?.snapshot || {};
  const workflowProgress = selectedProjectSessionWorkflow?.progress || {};
  const conversationAnalysis = workflowSnapshot.conversation_analysis;
  const recentSessions = (projectSessions || []).slice(0, 4);
  const stepsComplete = Object.values(workflowProgress).filter(Boolean).length;

  return (
    <>
      {/* ── Top grid ──────────────────────────────────────────── */}
      <div className="pp-grid">

        {/* ── Left: form + workspace list ─────────────────────── */}
        <div className="pp-form-col">

          {/* Create form */}
          <div className="pp-card">
            <div className="pp-card-kicker">New Workspace</div>
            <h3 className="pp-card-title">Set up a Business Profile</h3>
            <p className="pp-card-sub">
              Name your business, describe what it does, and add its location.
              MarketPilot will use this to find real local competitors and build your strategy.
            </p>

            <div className="pp-fields">
              <FormField label="Business Name">
                <input
                  className="pp-input"
                  placeholder="e.g. The Bloom Room"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </FormField>
              <div className="pp-fields-row">
                <FormField label="Operating Location">
                  <input
                    className="pp-input"
                    placeholder="e.g. College Park, MD 20740"
                    value={projectBusinessAddress}
                    onChange={(e) => setProjectBusinessAddress(e.target.value)}
                  />
                </FormField>
              </div>
              <FormField label="Business Description">
                <input
                  className="pp-input"
                  placeholder="What the business does, who it serves"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                />
              </FormField>
            </div>

            <div className="pp-form-actions">
              <button className="pp-btn-primary" onClick={createProject} disabled={busy}>
                {busy ? (
                  <><span className="pp-spinner" />Creating…</>
                ) : (
                  "Create & Start Workflow →"
                )}
              </button>
              <button className="pp-btn-ghost" onClick={loadProjects} disabled={busy}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
                </svg>
                Refresh
              </button>
            </div>
          </div>

          {/* Workspace list */}
          <div className="pp-card pp-workspaces-card">
            <div className="pp-workspaces-list-head">
              <div>
                <div className="pp-card-kicker">Your Workspaces</div>
                <h4 className="pp-workspaces-count">
                  {projects.length > 0
                    ? `${projects.length} business profile${projects.length !== 1 ? "s" : ""}`
                    : "No profiles yet"}
                </h4>
              </div>
            </div>

            {projects.length > 0 ? (
              <div className="pp-workspace-list">
                {projects.map((p) => (
                  <WorkspaceRow
                    key={p.id}
                    project={p}
                    isActive={String(p.id) === String(activeProjectId)}
                    onSelect={setActiveProjectId}
                  />
                ))}
              </div>
            ) : (
              <div className="pp-workspaces-empty">
                <p>Create your first business profile using the form above to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* ── Right: active workspace snapshot ────────────────── */}
        <aside className="pp-snapshot-col">
          {activeProject ? (
            <div className="pp-snapshot-card">
              <div className="pp-card-kicker pp-snapshot-kicker">Active Workspace</div>
              <div className="pp-snapshot-avatar">{projectInitials(activeProject.name)}</div>
              <h3 className="pp-snapshot-name">{activeProject.name}</h3>

              {activeProject.business_address ? (
                <div className="pp-snapshot-location">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  {activeProject.business_address}
                </div>
              ) : (
                <div className="pp-snapshot-location pp-snapshot-location-missing">
                  No location set — add one to enable competitor scanning
                </div>
              )}

              <div className="pp-snapshot-stats">
                <div className="pp-snapshot-stat">
                  <span className="pp-snapshot-stat-val">{projectSessions?.length || 0}</span>
                  <span className="pp-snapshot-stat-label">Sessions</span>
                </div>
                <div className="pp-snapshot-stat">
                  <span className="pp-snapshot-stat-val">{stepsComplete}</span>
                  <span className="pp-snapshot-stat-label">Steps Done</span>
                </div>
                <div className="pp-snapshot-stat">
                  <span className="pp-snapshot-stat-val">
                    {stepsComplete === 0 ? "—" : `${Math.round((stepsComplete / 9) * 100)}%`}
                  </span>
                  <span className="pp-snapshot-stat-label">Complete</span>
                </div>
              </div>

              {activeProject.description && (
                <p className="pp-snapshot-desc">{activeProject.description}</p>
              )}

              <div className="pp-snapshot-divider" />

              <button className="pp-snapshot-cta" onClick={onStartWorkflow}>
                {stepsComplete > 0 ? "Continue Strategy Workflow →" : "Begin Strategy Workflow →"}
              </button>

              <p className="pp-snapshot-note">
                Covers discovery, competitor analysis, positioning, personas, strategy, roadmap, and content.
              </p>
            </div>
          ) : (
            <div className="pp-snapshot-card pp-snapshot-empty">
              <div className="pp-snapshot-empty-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                  <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
              </div>
              <h4 className="pp-snapshot-empty-title">No workspace active</h4>
              <p className="pp-snapshot-empty-desc">
                Create a business profile on the left, or select one from your workspace list — then your full 9-step strategy workflow unlocks here.
              </p>
              <div className="pp-snapshot-steps-preview">
                {["Discovery", "Analysis", "Positioning", "Personas", "Strategy", "Roadmap"].map((s) => (
                  <span key={s} className="pp-snapshot-step-chip">{s}</span>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* ── Session history ────────────────────────────────────── */}
      {activeProject && (
        <div className="pp-sessions-section">
          <div className="pp-sessions-header">
            <div>
              <div className="pp-card-kicker">Session History</div>
              <h3 className="pp-sessions-title">
                {projectSessions?.length
                  ? `${projectSessions.length} session${projectSessions.length !== 1 ? "s" : ""} · ${activeProject.name}`
                  : `No sessions yet · ${activeProject.name}`}
              </h3>
            </div>
            <button className="pp-btn-ghost pp-new-session-btn" onClick={onStartWorkflow}>
              + New Session
            </button>
          </div>

          {projectSessions?.length ? (
            <>
              <div className="pp-session-grid">
                {recentSessions.map((session) => (
                  <SessionCard
                    key={session.id}
                    session={session}
                    isActive={String(session.id) === String(selectedProjectSessionId)}
                    onClick={() => {
                      setSelectedProjectSessionId(String(session.id));
                      selectProjectSession(String(session.id));
                    }}
                  />
                ))}
              </div>

              {projectSessions.length > 4 && (
                <div className="pp-all-sessions">
                  <label className="pp-label">All Sessions</label>
                  <select
                    className="pp-select"
                    value={selectedProjectSessionId}
                    onChange={(e) => {
                      setSelectedProjectSessionId(e.target.value);
                      selectProjectSession(e.target.value);
                    }}
                  >
                    {projectSessions.map((s) => (
                      <option key={s.id} value={s.id}>
                        Session #{s.id} · {s.status} · {s.answered_count} answered
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {selectedProjectSessionDetail && (
                <div className="pp-session-detail">
                  <div className="pp-session-detail-head">
                    <div>
                      <div className="pp-card-kicker">Session Detail</div>
                      <h4 className="pp-session-detail-title">
                        Session #{selectedProjectSessionDetail.id}
                        <span className={`pp-session-badge ${selectedProjectSessionDetail.status === "completed" ? "done" : "live"}`}>
                          {selectedProjectSessionDetail.status === "completed" ? (
                            <>
                              <svg width="9" height="9" viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                              Completed
                            </>
                          ) : (
                            <><span className="pp-badge-dot" />In Progress</>
                          )}
                        </span>
                      </h4>
                    </div>
                    <div className="pp-session-detail-meta">
                      <div className="pp-session-meta-item">
                        <span>Created</span>
                        <strong>
                          {selectedProjectSessionDetail.created_at
                            ? new Date(selectedProjectSessionDetail.created_at).toLocaleString()
                            : "N/A"}
                        </strong>
                      </div>
                      <div className="pp-session-meta-item">
                        <span>Last Updated</span>
                        <strong>
                          {selectedProjectSessionDetail.updated_at
                            ? new Date(selectedProjectSessionDetail.updated_at).toLocaleString()
                            : "N/A"}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <SessionTimeline workflowProgress={workflowProgress} />

                  {selectedProjectSessionDetail.status !== "completed" && (
                    <div className="pp-session-in-progress">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      This session is in progress — outputs below reflect completed steps only.
                    </div>
                  )}

                  {conversationAnalysis && (
                    <div className="pp-analysis-summary">
                      <div className="pp-card-kicker">Discovery Summary</div>
                      <p className="pp-analysis-text">
                        {conversationAnalysis.summary || "Discovery summary available."}
                      </p>
                      {!!conversationAnalysis.business_location && (
                        <div className="pp-analysis-row">
                          <span>Location</span>
                          <strong>{conversationAnalysis.business_location}</strong>
                        </div>
                      )}
                      {!!(conversationAnalysis.important_points || []).length && (
                        <ul className="pp-analysis-points">
                          {conversationAnalysis.important_points.map((pt, i) => (
                            <li key={i}>{pt}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  <div className="pp-artifacts">
                    {workflowSnapshot.analysis && (
                      <ArtifactBlock stepN="03" title="Competitive Benchmarking">
                        <CompetitorCards analysis={workflowSnapshot.analysis.report} />
                      </ArtifactBlock>
                    )}
                    {workflowSnapshot.positioning && (
                      <ArtifactBlock stepN="04" title="Positioning Statement">
                        <PositioningCard positioning={workflowSnapshot.positioning} />
                      </ArtifactBlock>
                    )}
                    {!!workflowSnapshot.personas?.length && (
                      <ArtifactBlock stepN="05" title="Buyer Personas">
                        <PersonaCards personas={workflowSnapshot.personas} />
                      </ArtifactBlock>
                    )}
                    {workflowSnapshot.research && (
                      <ArtifactBlock stepN="06" title="Research Report">
                        <ResearchCards research={workflowSnapshot.research.report} />
                      </ArtifactBlock>
                    )}
                    {workflowSnapshot.strategy && (
                      <ArtifactBlock stepN="07" title="Channel Strategy">
                        <StrategyCards strategy={workflowSnapshot.strategy.strategy} />
                      </ArtifactBlock>
                    )}
                    {workflowSnapshot.roadmap && (
                      <ArtifactBlock stepN="08" title="90-Day Roadmap">
                        <RoadmapCards roadmap={workflowSnapshot.roadmap.roadmap} />
                      </ArtifactBlock>
                    )}
                    {!!workflowSnapshot.content_assets?.length && (
                      <ArtifactBlock stepN="09" title="Content Studio">
                        <ContentAssetCards assets={workflowSnapshot.content_assets} />
                      </ArtifactBlock>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="pp-sessions-empty">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
              <p>No sessions yet for this workspace.</p>
              <button className="pp-btn-primary" style={{ marginTop: 12 }} onClick={onStartWorkflow}>
                Start Marketing Discovery →
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
