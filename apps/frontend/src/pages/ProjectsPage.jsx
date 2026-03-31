import { useEffect } from "react";
import ProjectPanel from "../components/ProjectPanel";
import { useNavigate } from "react-router-dom";

export default function ProjectsPage({ workflow }) {
  const navigate = useNavigate();
  const { state, set, actions } = workflow;

  // Refresh session list every time the page is visited so answered_count
  // reflects work done in the interview since the project was last selected.
  useEffect(() => {
    if (state.activeProjectId) {
      actions.loadProjectSessions(String(state.activeProjectId));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createAndContinue = async () => {
    const outcome = await actions.createProject();
    if (outcome?.ok) navigate("/questionnaire");
  };

  return (
    <ProjectPanel
      projectName={state.projectName}
      setProjectName={set.setProjectName}
      projectDescription={state.projectDescription}
      setProjectDescription={set.setProjectDescription}
      projectBusinessAddress={state.projectBusinessAddress}
      setProjectBusinessAddress={set.setProjectBusinessAddress}
      createProject={createAndContinue}
      loadProjects={actions.loadProjects}
      busy={state.busy}
      activeProjectId={state.activeProjectId}
      setActiveProjectId={set.setActiveProjectId}
      projects={state.projects}
      activeProject={state.activeProject}
      projectSessions={state.projectSessions}
      selectedProjectSessionId={state.selectedProjectSessionId}
      setSelectedProjectSessionId={set.setSelectedProjectSessionId}
      selectProjectSession={actions.selectProjectSession}
      selectedProjectSessionDetail={state.selectedProjectSessionDetail}
      selectedProjectSessionWorkflow={state.selectedProjectSessionWorkflow}
      onStartWorkflow={() => {
        actions.resetForNewSession();
        navigate("/questionnaire");
      }}
    />
  );
}
