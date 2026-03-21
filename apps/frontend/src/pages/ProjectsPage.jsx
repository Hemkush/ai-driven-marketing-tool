import ProjectPanel from "../components/ProjectPanel";
import { EmptyState, NextStepCta } from "../components/UiBlocks";
import { useNavigate } from "react-router-dom";

export default function ProjectsPage({ workflow }) {
  const navigate = useNavigate();
  const { state, set, actions } = workflow;

  const createAndContinue = async () => {
    const outcome = await actions.createProject();
    if (outcome?.ok) {
      navigate("/questionnaire");
    }
  };

  return (
    <div>
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
      />
      {!state.activeProjectId && (
        <EmptyState
          glyph="[]"
          title="No Active Business Profile Yet"
          description="Create or select a business profile to unlock the questionnaire and strategy workflow."
        />
      )}
      <NextStepCta
        to="/questionnaire"
        label="Next: Market Discovery Interview"
        disabled={!state.activeProjectId}
      />
    </div>
  );
}
