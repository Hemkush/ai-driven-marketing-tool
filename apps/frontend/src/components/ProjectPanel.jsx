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
}) {
  return (
    <>
      <h3>Business Profile</h3>
      <input
        placeholder="Business profile name"
        value={projectName}
        onChange={(e) => setProjectName(e.target.value)}
      />
      <br />
      <input
        placeholder="Business description"
        value={projectDescription}
        onChange={(e) => setProjectDescription(e.target.value)}
      />
      <br />
      <input
        placeholder="Business address / operating location"
        value={projectBusinessAddress}
        onChange={(e) => setProjectBusinessAddress(e.target.value)}
      />
      <br />
      <button onClick={createProject} disabled={busy}>
        Create Business Profile
      </button>
      <button onClick={loadProjects} style={{ marginLeft: 8 }} disabled={busy}>
        Refresh Profiles
      </button>
      <div style={{ marginTop: 8 }}>
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
      <p>
        Active profile: {activeProject ? `${activeProject.name} (#${activeProject.id})` : "None"}
      </p>
      {activeProject?.business_address && (
        <p>Location: {activeProject.business_address}</p>
      )}
    </>
  );
}
