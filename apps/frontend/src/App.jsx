import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import AppShell from "./components/AppShell";
import ErrorBoundary from "./components/ErrorBoundary";
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
import VerifyEmailPage from "./pages/VerifyEmailPage";
import { useMvpWorkflow } from "./state/useMvpWorkflow";
import MilestoneModal from "./components/MilestoneModal";
import CommandPalette from "./components/CommandPalette";

export default function App() {
  const workflow = useMvpWorkflow();
  const { state, actions } = workflow;
  const navigate = useNavigate();
  const location = useLocation();
  const sessionProgress = state.selectedProjectSessionWorkflow?.progress || {};
  const progress = {
    "/projects": Boolean(state.activeProjectId),
    "/questionnaire": Boolean(sessionProgress["/questionnaire"]) || Boolean(state.interviewCompleted),
    "/analysis": Boolean(sessionProgress["/analysis"]) || Boolean(state.analysis),
    "/positioning": Boolean(sessionProgress["/positioning"]) || Boolean(state.positioning),
    "/personas": Boolean(sessionProgress["/personas"]) || Boolean(state.personas.length),
    "/research": Boolean(sessionProgress["/research"]) || Boolean(state.research),
    "/roadmap": Boolean(sessionProgress["/roadmap"]) || Boolean(state.roadmap),
    "/content": Boolean(sessionProgress["/content"]) || Boolean(state.contentAssets.length),
  };

  useEffect(() => {
    // Redirect unauthenticated users away from protected app routes
    const publicPaths = ["/", "/login", "/verify-email"];
    if (!state.me && !publicPaths.includes(location.pathname)) {
      navigate("/", { replace: true });
    }
  }, [state.me, location.pathname, navigate]);

  if (!state.me) {
    if (location.pathname === "/login") return <LoginPage workflow={workflow} />;
    if (location.pathname === "/verify-email") return <VerifyEmailPage />;
    return <LandingPage workflow={workflow} />;
  }

  return (
    <AppShell me={state.me} onLogout={actions.logout} progress={progress} busy={state.busy} projectName={state.activeProject?.name || ""}>
      <ToastStack toasts={state.toasts} onDismiss={actions.dismissToast} />
      {state.milestone && (
        <MilestoneModal milestone={state.milestone} onDismiss={actions.dismissMilestone} />
      )}
      <CommandPalette />
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/login" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={
          <ErrorBoundary pageName="Business Profile">
            <ProjectsPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/questionnaire" element={
          <ErrorBoundary pageName="Marketing Discovery">
            <QuestionnairePage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/analysis" element={
          <ErrorBoundary pageName="Competitive Benchmarking">
            <AnalysisPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/positioning" element={
          <ErrorBoundary pageName="Positioning">
            <PositioningPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/research" element={
          <ErrorBoundary pageName="Research">
            <ResearchPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/personas" element={
          <ErrorBoundary pageName="Personas">
            <PersonasPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/roadmap" element={
          <ErrorBoundary pageName="Roadmap">
            <RoadmapPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="/content" element={
          <ErrorBoundary pageName="Content Studio">
            <ContentPage workflow={workflow} />
          </ErrorBoundary>
        } />
        <Route path="*" element={<Navigate to="/projects" replace />} />
      </Routes>

    </AppShell>
  );
}
