import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import AppShell from "./components/AppShell";
import AuthPanel from "./components/AuthPanel";
import ToastStack from "./components/ToastStack";
import AnalysisPage from "./pages/AnalysisPage";
import ContentPage from "./pages/ContentPage";
import PersonasPage from "./pages/PersonasPage";
import PositioningPage from "./pages/PositioningPage";
import ProjectsPage from "./pages/ProjectsPage";
import QuestionnairePage from "./pages/QuestionnairePage";
import ResearchPage from "./pages/ResearchPage";
import RoadmapPage from "./pages/RoadmapPage";
import StrategyPage from "./pages/StrategyPage";
import { useMvpWorkflow } from "./state/useMvpWorkflow";

export default function App() {
  const workflow = useMvpWorkflow();
  const { state, set, actions } = workflow;
  const navigate = useNavigate();
  const location = useLocation();
  const progress = {
    "/projects": Boolean(state.activeProjectId),
    "/questionnaire": Boolean(state.interviewCompleted),
    "/analysis": Boolean(state.analysis),
    "/positioning": Boolean(state.positioning),
    "/research": Boolean(state.research),
    "/personas": Boolean(state.personas.length),
    "/strategy": Boolean(state.strategy),
    "/roadmap": Boolean(state.roadmap),
    "/content": Boolean(state.contentAssets.length),
  };

  useEffect(() => {
    if (!state.me && location.pathname !== "/") {
      navigate("/", { replace: true });
    }
  }, [state.me, location.pathname, navigate]);

  if (!state.me) {
    return (
      <AuthPanel
        companyName={state.companyName}
        setCompanyName={set.setCompanyName}
        email={state.email}
        setEmail={set.setEmail}
        password={state.password}
        setPassword={set.setPassword}
        register={actions.register}
        login={actions.login}
        busy={state.busy}
        msg={state.msg}
      />
    );
  }

  return (
    <AppShell me={state.me} onLogout={actions.logout} progress={progress}>
      <ToastStack toasts={state.toasts} onDismiss={actions.dismissToast} />
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage workflow={workflow} />} />
        <Route path="/questionnaire" element={<QuestionnairePage workflow={workflow} />} />
        <Route path="/analysis" element={<AnalysisPage workflow={workflow} />} />
        <Route path="/positioning" element={<PositioningPage workflow={workflow} />} />
        <Route path="/research" element={<ResearchPage workflow={workflow} />} />
        <Route path="/personas" element={<PersonasPage workflow={workflow} />} />
        <Route path="/strategy" element={<StrategyPage workflow={workflow} />} />
        <Route path="/roadmap" element={<RoadmapPage workflow={workflow} />} />
        <Route path="/content" element={<ContentPage workflow={workflow} />} />
        <Route path="*" element={<Navigate to="/projects" replace />} />
      </Routes>

      {state.msg && <p style={{ marginTop: 16 }}>{state.msg}</p>}
      {state.busy && <p>Processing...</p>}
    </AppShell>
  );
}
