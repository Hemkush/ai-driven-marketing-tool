import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import AppShell from "./components/AppShell";
import ToastStack from "./components/ToastStack";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
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
  const { state, actions } = workflow;
  const navigate = useNavigate();
  const location = useLocation();
  const sessionProgress = state.selectedProjectSessionWorkflow?.progress || {};
  const progress = {
    "/projects": Boolean(state.activeProjectId),
    "/questionnaire": sessionProgress["/questionnaire"] ?? Boolean(state.interviewCompleted),
    "/analysis": sessionProgress["/analysis"] ?? Boolean(state.analysis),
    "/positioning": sessionProgress["/positioning"] ?? Boolean(state.positioning),
    "/personas": sessionProgress["/personas"] ?? Boolean(state.personas.length),
    "/research": sessionProgress["/research"] ?? Boolean(state.research),
    "/strategy": sessionProgress["/strategy"] ?? Boolean(state.strategy),
    "/roadmap": sessionProgress["/roadmap"] ?? Boolean(state.roadmap),
    "/content": sessionProgress["/content"] ?? Boolean(state.contentAssets.length),
  };

  useEffect(() => {
    // Redirect unauthenticated users away from protected app routes
    if (!state.me && location.pathname !== "/" && location.pathname !== "/login") {
      navigate("/", { replace: true });
    }
  }, [state.me, location.pathname, navigate]);

  if (!state.me) {
    if (location.pathname === "/login") {
      return <LoginPage workflow={workflow} />;
    }
    return <LandingPage workflow={workflow} />;
  }

  return (
    <AppShell me={state.me} onLogout={actions.logout} progress={progress} busy={state.busy}>
      <ToastStack toasts={state.toasts} onDismiss={actions.dismissToast} />
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/login" element={<Navigate to="/projects" replace />} />
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

    </AppShell>
  );
}
