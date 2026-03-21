import { NavLink, useLocation } from "react-router-dom";

const links = [
  ["Business Profile", "/projects"],
  ["Marketing Discovery", "/questionnaire"],
  ["Analysis", "/analysis"],
  ["Positioning", "/positioning"],
  ["Research", "/research"],
  ["Personas", "/personas"],
  ["Strategy", "/strategy"],
  ["Roadmap", "/roadmap"],
  ["Content Studio", "/content"],
];

const stepDescriptions = {
  "/projects":
    "Set up the small or mid-size business profile and select the active workspace for strategy generation.",
  "/questionnaire":
    "Run the marketing discovery interview to capture business, customer, and growth context.",
  "/analysis":
    "Review segment attractiveness insights across market size, competition, fit, and profitability.",
  "/positioning":
    "Generate and refine a positioning statement aligned with your strongest target segment.",
  "/research":
    "Explore deeper target-customer and competitor research to validate strategic decisions.",
  "/personas":
    "Review generated buyer personas with profile, behavior, and engagement strategy details.",
  "/strategy":
    "Get prioritized channel recommendations based on personas, goals, and practical constraints.",
  "/roadmap":
    "Translate strategy into a focused 90-day execution roadmap with milestones and ownership.",
  "/content":
    "Generate campaign-ready assets and reusable marketing content for execution.",
};

export default function AppShell({ me, onLogout, progress = {}, children }) {
  const location = useLocation();
  const activeStep =
    links.find(([, to]) => location.pathname === to)?.[0] || "Business Profile";
  const activeStepDescription =
    stepDescriptions[location.pathname] || stepDescriptions["/projects"];

  return (
    <div className="site-shell">
      <header className="site-utility">
        <div className="site-utility-title">MARKETPILOT</div>
        <div className="site-utility-actions">
          <span className="site-user">Signed in: {me?.email}</span>
          <button className="btn ghost site-logout" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="site-nav">
        <div className="site-brand">AI DRIVEN MARKETING WORKFLOW</div>
        <div className="site-nav-list">
          {links.map(([label, to]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                isActive ? "site-nav-link site-nav-link-active" : "site-nav-link"
              }
            >
              <span>{label}</span>
              <span className={progress[to] ? "site-check on" : "site-check"}>
                {progress[to] ? "Done" : "Pending"}
              </span>
            </NavLink>
          ))}
        </div>
      </nav>

      <section className="site-hero">
        <div className="site-hero-overlay">
          <h1>{activeStep}</h1>
          <p>{activeStepDescription}</p>
        </div>
      </section>

      <main className="main-panel">
        <section className="content-panel">{children}</section>
      </main>
    </div>
  );
}
