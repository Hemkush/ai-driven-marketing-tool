import { useEffect, useRef } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Check, LogOut } from "lucide-react";

// ── Step map (4 phases matching the landing page workflow) ────────
const STEP_GROUPS = [
  {
    phase: "Set Up",
    steps: [
      { to: "/projects",     label: "Business Profile",        n: "01" },
      { to: "/questionnaire",label: "Marketing Discovery",     n: "02" },
    ],
  },
  {
    phase: "Analyse",
    steps: [
      { to: "/analysis", label: "Competitive Benchmarking", n: "03" },
    ],
  },
  {
    phase: "Strategise",
    steps: [
      { to: "/positioning", label: "Positioning", n: "04" },
      { to: "/personas",    label: "Personas",    n: "05" },
      { to: "/research",    label: "Research",    n: "06" },
    ],
  },
  {
    phase: "Execute",
    steps: [
      { to: "/roadmap",  label: "Roadmap",        n: "07" },
      { to: "/content",  label: "Content Studio", n: "08" },
    ],
  },
];

const STEP_DESC = {
  "/projects":      "Create and manage your business workspace.",
  "/questionnaire": "Run the AI-guided marketing discovery interview.",
  "/analysis":      "Benchmark local competitors using live Google data.",
  "/positioning":   "Generate a positioning statement for your strongest segment.",
  "/research":      "Deep-dive into target customers and the competitive landscape.",
  "/personas":      "Review AI-built buyer personas grounded in real market data.",
  "/roadmap":       "Turn your plan into a focused 90-day execution roadmap.",
  "/content":       "Generate campaign-ready assets for every channel.",
};

const TOTAL_STEPS = 8;

function userInitials(email = "") {
  return email.charAt(0).toUpperCase() || "?";
}

// ── Status icon components ────────────────────────────────────────
function CheckIcon() {
  return <Check size={12} strokeWidth={2.8} />;
}

export default function AppShell({ me, onLogout, progress = {}, busy = false, projectName = "", children }) {
  const location = useLocation();
  const currentPath = location.pathname;

  // Resolve active step metadata
  let activeLabel = "Business Profile";
  let activeDesc  = STEP_DESC["/projects"];
  let activeN     = "01";
  for (const group of STEP_GROUPS) {
    for (const step of group.steps) {
      if (step.to === currentPath) {
        activeLabel = step.label;
        activeDesc  = STEP_DESC[step.to] || "";
        activeN     = step.n;
      }
    }
  }

  const doneCount = Object.values(progress).filter(Boolean).length;
  const progressPct = Math.round((doneCount / TOTAL_STEPS) * 100);

  // Track newly-completed steps for unlock animation (DOM-only, no state)
  const prevProgressRef = useRef({});
  const unlockTimers = useRef([]);

  useEffect(() => {
    const prev = prevProgressRef.current;
    const justDone = [];
    for (const [path, isDone] of Object.entries(progress)) {
      if (isDone && !prev[path]) justDone.push(path);
    }
    prevProgressRef.current = { ...progress };

    if (justDone.length === 0) return;
    justDone.forEach((path) => {
      const el = document.querySelector(`[data-step="${CSS.escape(path)}"]`);
      if (!el) return;
      el.classList.add("newly-done");
      const t = setTimeout(() => el.classList.remove("newly-done"), 900);
      unlockTimers.current.push(t);
    });
    return () => {
      unlockTimers.current.forEach(clearTimeout);
      unlockTimers.current = [];
    };
  }, [progress]);

  useEffect(() => {
    document.title = `${activeLabel} — MarketPilot`;
  }, [activeLabel]);

  return (
    <div className="app-shell">

      {/* ── Top bar ──────────────────────────────────────────── */}
      <header className="app-topbar">
        <div className="app-topbar-brand">
          <span className="app-brand-mark" aria-hidden="true" />
          <span className="app-brand-name">MarketPilot</span>
          <span className="app-brand-divider" aria-hidden="true" />
          <span className="app-brand-tag">AI Marketing Platform</span>
        </div>
        <div className="app-topbar-right">
          <div className="app-user-pill">
            <div className="app-user-avatar">{userInitials(me?.email)}</div>
            <span className="app-user-email">
              {me?.full_name || me?.email}
            </span>
          </div>
          <button className="app-logout-btn" onClick={onLogout} title="Sign out" aria-label="Sign out">
            <LogOut size={14} strokeWidth={2} />
            <span>Sign out</span>
          </button>
        </div>

        {/* Global loading bar — visible on every page while busy */}
        {busy && (
          <div className="app-loading-bar" role="progressbar" aria-label="Processing">
            <div className="app-loading-bar-fill" />
          </div>
        )}
      </header>

      {/* ── Sidebar ──────────────────────────────────────────── */}
      <nav className="app-sidebar" aria-label="Workflow navigation">
        <div className="app-sidebar-progress-wrap">
          <div className="app-sidebar-progress-bar">
            <div
              className="app-sidebar-progress-fill"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="app-sidebar-progress-label">
            {doneCount} / {TOTAL_STEPS} steps complete
          </span>
        </div>

        {STEP_GROUPS.map((group) => (
          <div key={group.phase} className="app-sidebar-group">
            <div className="app-sidebar-group-label">{group.phase}</div>
            {group.steps.map((step) => {
              const isDone   = Boolean(progress[step.to]);
              const isActive = step.to === currentPath;
              return (
                <NavLink
                  key={step.to}
                  to={step.to}
                  data-step={step.to}
                  className={[
                    "app-sidebar-item",
                    isActive ? "active" : "",
                    isDone   ? "done"   : "",
                  ].filter(Boolean).join(" ")}
                >
                  <span className="app-sidebar-n">{step.n}</span>
                  <span className="app-sidebar-label">{step.label}</span>
                  <span className="app-sidebar-status" aria-hidden="true">
                    {isDone ? (
                      <span className="app-status-check"><CheckIcon /></span>
                    ) : isActive ? (
                      <span className="app-status-dot live" />
                    ) : (
                      <span className="app-status-dot" />
                    )}
                  </span>
                </NavLink>
              );
            })}
          </div>
        ))}

        {/* ── Stats widget ────────────────────────────────────── */}
        <div className="app-sidebar-stats">
          {projectName && (
            <div className="app-sidebar-stat-row">
              <span className="app-sidebar-stat-label">Project</span>
              <span className="app-sidebar-stat-value app-sidebar-stat-project">{projectName}</span>
            </div>
          )}
          <div className="app-sidebar-stat-row">
            <span className="app-sidebar-stat-label">Progress</span>
            <span className="app-sidebar-stat-value">{doneCount} / {TOTAL_STEPS}</span>
          </div>
          <div className="app-sidebar-kbd-hint">
            <kbd>⌘K</kbd>
            <span>quick navigate</span>
          </div>
        </div>
      </nav>

      {/* ── Main area ────────────────────────────────────────── */}
      <main className="app-main">
        {/* Slim page header replacing the old 200px hero */}
        <div className="app-page-header">
          <div className="app-page-step-badge">Step {activeN} of {TOTAL_STEPS}</div>
          <h1 className="app-page-title">{activeLabel}</h1>
          <p className="app-page-desc">{activeDesc}</p>
        </div>

        {/* Page content — keyed on pathname so CSS page-enter animation fires on every route change */}
        <div key={location.pathname} className="app-content">
          {children}
        </div>
      </main>

    </div>
  );
}
