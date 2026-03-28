import {
  CompetitorCards,
  ContentAssetCards,
  PersonaCards,
  PositioningCard,
  ResearchCards,
  RoadmapCards,
  StrategyCards,
} from "./CompactCards";

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
}) {
  const workflowSnapshot = selectedProjectSessionWorkflow?.snapshot || {};
  const workflowProgress = selectedProjectSessionWorkflow?.progress || {};
  const conversationAnalysis = workflowSnapshot.conversation_analysis;
  const recentSessions = (projectSessions || []).slice(0, 4);
  const timelineSteps = [
    { route: "/projects", label: "Business Profile" },
    { route: "/questionnaire", label: "Discovery" },
    { route: "/analysis", label: "Competitive Benchmarking" },
    { route: "/positioning", label: "Positioning" },
    { route: "/research", label: "Research" },
    { route: "/personas", label: "Personas" },
    { route: "/strategy", label: "Strategy" },
    { route: "/roadmap", label: "Roadmap" },
    { route: "/content", label: "Content" },
  ];
  const currentStepIndex = timelineSteps.findIndex(
    (step, index) =>
      !workflowProgress[step.route] &&
      timelineSteps.slice(0, index).every((prev) => workflowProgress[prev.route])
  );

  return (
    <>
      <div className="profile-workspace-grid">
        <section className="profile-form-card">
          <div className="profile-form-head">
            <div>
              <div className="session-overview-kicker">Business Setup</div>
              <h3>Business Profile</h3>
            </div>
            <p className="page-subtitle">
              Create a business workspace, add context, and choose the profile you want to continue with.
            </p>
          </div>

          <input
            placeholder="Business profile name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
          />
          <input
            placeholder="Business description"
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
          />
          <input
            placeholder="Business address / operating location"
            value={projectBusinessAddress}
            onChange={(e) => setProjectBusinessAddress(e.target.value)}
          />

          <div className="action-row">
            <button onClick={createProject} disabled={busy}>
              Create Business Profile
            </button>
            <button onClick={loadProjects} className="btn ghost" disabled={busy}>
              Refresh Profiles
            </button>
          </div>

          <div className="profile-select-wrap">
            <label className="profile-select-label">Active Workspace</label>
            <select
              value={activeProjectId}
              onChange={(e) => setActiveProjectId(e.target.value)}
            >
              <option value="">Select business profile</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (#{p.id})
                </option>
              ))}
            </select>
          </div>
        </section>

        <aside className="profile-summary-card">
          <div className="session-overview-kicker">Workspace Snapshot</div>
          <h4>{activeProject ? activeProject.name : "No active profile selected"}</h4>

          <div className="profile-summary-grid">
            <div className="profile-summary-tile">
              <span>Business ID</span>
              <strong>{activeProject ? `#${activeProject.id}` : "Not selected"}</strong>
            </div>
            <div className="profile-summary-tile">
              <span>Saved Sessions</span>
              <strong>{projectSessions?.length || 0}</strong>
            </div>
            <div className="profile-summary-tile wide">
              <span>Operating Location</span>
              <strong>{activeProject?.business_address || "Add location to improve local analysis and research."}</strong>
            </div>
            <div className="profile-summary-tile wide">
              <span>Profile Description</span>
              <strong>{activeProject?.description || "Describe the business so downstream analysis and positioning are more specific."}</strong>
            </div>
          </div>

          <div className="profile-summary-note">
            {activeProject
              ? "This workspace anchors discovery, analysis, positioning, research, personas, strategy, roadmap, and content generation."
              : "Select or create a business profile to unlock the full workflow and session history."}
          </div>
        </aside>
      </div>

      {activeProject && (
        <div style={{ marginTop: 18 }}>
          <h4>Session History</h4>
          {projectSessions?.length ? (
            <>
              <div className="session-picker-wrap">
                <div className="session-picker-grid">
                  {recentSessions.map((session) => {
                    const isActive = String(session.id) === String(selectedProjectSessionId);
                    return (
                      <button
                        key={session.id}
                        type="button"
                        className={`session-picker-card${isActive ? " active" : ""}`}
                        onClick={() => {
                          setSelectedProjectSessionId(String(session.id));
                          selectProjectSession(String(session.id));
                        }}
                      >
                        <div className="session-picker-head">
                          <strong>Session #{session.id}</strong>
                          <span className={`session-picker-badge ${session.status === "completed" ? "done" : "live"}`}>
                            {session.status}
                          </span>
                        </div>
                        <div className="session-picker-meta">
                          <span>{session.answered_count} answered</span>
                          <span>
                            {session.updated_at
                              ? new Date(session.updated_at).toLocaleDateString()
                              : "Recent"}
                          </span>
                        </div>
                        <p>
                          {session.latest_answered_question ||
                            session.current_question ||
                            "No responses captured yet."}
                        </p>
                      </button>
                    );
                  })}
                </div>

                <div className="profile-select-wrap">
                  <label className="profile-select-label">All Sessions</label>
                  <select
                    value={selectedProjectSessionId}
                    onChange={(e) => {
                      setSelectedProjectSessionId(e.target.value);
                      selectProjectSession(e.target.value);
                    }}
                  >
                    {projectSessions.map((session) => (
                      <option key={session.id} value={session.id}>
                        Session #{session.id} | {session.status} | {session.answered_count} answered
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {selectedProjectSessionDetail && (
                <div className="session-overview-card">
                  <div className="session-overview-head">
                    <div>
                      <div className="session-overview-kicker">Selected Session</div>
                      <h4>
                        Session #{selectedProjectSessionDetail.id}
                        <span className="session-status-badge">
                          {selectedProjectSessionDetail.status}
                        </span>
                      </h4>
                    </div>
                    <div className="session-overview-meta">
                      <div>
                        <span>Created</span>
                        <strong>
                          {selectedProjectSessionDetail.created_at
                            ? new Date(selectedProjectSessionDetail.created_at).toLocaleString()
                            : "N/A"}
                        </strong>
                      </div>
                      <div>
                        <span>Updated</span>
                        <strong>
                          {selectedProjectSessionDetail.updated_at
                            ? new Date(selectedProjectSessionDetail.updated_at).toLocaleString()
                            : "N/A"}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="session-timeline">
                    {timelineSteps.map((step, index) => {
                      const isDone = Boolean(workflowProgress[step.route]);
                      const isCurrent =
                        !isDone &&
                        (currentStepIndex === index ||
                          (currentStepIndex === -1 && index === timelineSteps.length - 1));
                      return (
                        <div
                          key={step.route}
                          className={`session-timeline-step${
                            isDone ? " done" : isCurrent ? " current" : ""
                          }`}
                        >
                          <div className="session-timeline-node">
                            {isDone ? "Done" : isCurrent ? "Now" : ""}
                          </div>
                          <div className="session-timeline-label">{step.label}</div>
                        </div>
                      );
                    })}
                  </div>

                  {selectedProjectSessionDetail.status !== "completed" ? (
                    <p className="session-overview-note">
                      This session is still in progress. The page shows only the outputs generated so far.
                    </p>
                  ) : null}

                  {conversationAnalysis ? (
                    <div className="session-analysis-block">
                      <h4>Conversation Analysis</h4>
                      <p>{conversationAnalysis.summary || "Discovery summary available."}</p>
                      {!!conversationAnalysis.business_location && (
                        <p>
                          <b>Business Location:</b> {conversationAnalysis.business_location}
                        </p>
                      )}
                      {!!(conversationAnalysis.important_points || []).length && (
                        <div>
                          <b>Important Points</b>
                          <ul>
                            {conversationAnalysis.important_points.map((point, idx) => (
                              <li key={`point-${idx}`}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : null}

                  {workflowSnapshot.analysis ? (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 2</span>
                        <h4>Competitive Benchmarking</h4>
                      </div>
                      <CompetitorCards analysis={workflowSnapshot.analysis.report} />
                    </div>
                  ) : null}

                  {workflowSnapshot.positioning ? (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 3</span>
                        <h4>Positioning Statement</h4>
                      </div>
                      <PositioningCard positioning={workflowSnapshot.positioning} />
                    </div>
                  ) : null}

                  {workflowSnapshot.research ? (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 4</span>
                        <h4>Research</h4>
                      </div>
                      <ResearchCards research={workflowSnapshot.research.report} />
                    </div>
                  ) : null}

                  {!!workflowSnapshot.personas?.length && (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 5</span>
                        <h4>Personas</h4>
                      </div>
                      <PersonaCards personas={workflowSnapshot.personas} />
                    </div>
                  )}

                  {workflowSnapshot.strategy ? (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 6</span>
                        <h4>Strategy</h4>
                      </div>
                      <StrategyCards strategy={workflowSnapshot.strategy.strategy} />
                    </div>
                  ) : null}

                  {workflowSnapshot.roadmap ? (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 7</span>
                        <h4>Roadmap</h4>
                      </div>
                      <RoadmapCards roadmap={workflowSnapshot.roadmap.roadmap} />
                    </div>
                  ) : null}

                  {!!workflowSnapshot.content_assets?.length && (
                    <div className="session-artifact-block">
                      <div className="session-step-heading">
                        <span className="session-step-index">Step 8</span>
                        <h4>Content Studio</h4>
                      </div>
                      <ContentAssetCards assets={workflowSnapshot.content_assets} />
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <p>No sessions yet for this business profile.</p>
          )}
        </div>
      )}
    </>
  );
}
