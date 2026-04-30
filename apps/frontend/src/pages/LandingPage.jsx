import { useState, useEffect } from "react";

// ── Scroll reveal hook ───────────────────────────────────────────
function useScrollReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".lp-reveal");
    if (!els.length) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("lp-visible");
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

// ── Demo data: The Bloom Room, College Park MD 20740 ─────────────
const DEMO_COMPETITORS = [
  { name: "Petals & Stems", rating: 4.7, price: "$$", threat: "medium", reviews: 94 },
  { name: "Greenbelt Garden Center", rating: 4.2, price: "$", threat: "high", reviews: 167 },
  { name: "Fleur Boutique", rating: 4.9, price: "$$$", threat: "low", reviews: 41 },
];

// ── 4-Phase workflow (replaces 9-card feature dump) ──────────────
const HOW_PHASES = [
  {
    n: "01",
    title: "Set Up",
    subtitle: "Tell us about your business",
    desc: "Create your workspace in 2 minutes. Add your business name, location, and a brief description — that's all we need to begin.",
    steps: ["Business Profile", "Discovery Interview"],
    time: "~5 min",
  },
  {
    n: "02",
    title: "Analyse",
    subtitle: "We scan your real local market",
    desc: "AI pulls live competitor data from Google Places — ratings, pricing, business hours, real review text, and every gap in the market.",
    steps: ["Competitor Scan", "Positioning Statement"],
    time: "~8 min",
  },
  {
    n: "03",
    title: "Strategise",
    subtitle: "AI builds your complete strategy",
    desc: "Detailed buyer personas, deep market research, and a channel strategy — all grounded in your actual competitors and local customer language.",
    steps: ["Buyer Personas", "Deep Research", "Channel Strategy"],
    time: "~12 min",
  },
  {
    n: "04",
    title: "Execute",
    subtitle: "Go from strategy to action",
    desc: "A focused 90-day roadmap ordered by impact, plus ready-to-use content assets for every channel. Start executing from day one.",
    steps: ["90-Day Roadmap", "Content Studio"],
    time: "~5 min",
  },
];

// ── Testimonials ─────────────────────────────────────────────────
const TESTIMONIALS = [
  {
    quote: "The competitor scan showed me two gaps I've been missing for years. Within a week of following the roadmap I had three new bookings from channels I'd never tried. This thing pays for itself fast.",
    name: "Sarah M.",
    role: "Salon Owner",
    location: "College Park, MD",
    initial: "S",
    color: "#7c3aed",
  },
  {
    quote: "We now run MarketPilot for every new client onboarding. What used to take our team three days of research takes thirty minutes. The personas alone changed how we write creative briefs.",
    name: "David K.",
    role: "Marketing Agency Director",
    location: "Washington, DC",
    initial: "D",
    color: "#0369a1",
  },
  {
    quote: "The positioning statement it generated was sharper than what I'd been using for two years. It's real data, not generic marketing speak — and my clients notice the difference in every deck.",
    name: "James L.",
    role: "Business Consultant",
    location: "Bethesda, MD",
    initial: "J",
    color: "#065f46",
  },
];

// ── Audience data with SVG icons + taglines ──────────────────────
const AUDIENCES = [
  {
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="lp-audience-svg">
        <rect width="40" height="40" rx="10" fill="rgba(199,40,50,0.08)" />
        <path d="M8 32v-3a6 6 0 016-6h12a6 6 0 016 6v3" stroke="#c72832" strokeWidth="2" strokeLinecap="round" />
        <circle cx="20" cy="17" r="5" stroke="#c72832" strokeWidth="2" />
        <path d="M29 10l2 2-2 2M31 12h-4" stroke="#c72832" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    tagline: "Every chain has a marketing team. Now so do you.",
    title: "Small Business Owners",
    desc: "Get agency-quality marketing strategy without agency prices. Know your local market, own your positioning, execute with confidence.",
    bullets: [
      "See exactly who you're competing against — and what they're missing",
      "Find the positioning gap that makes customers choose you",
      "Build a 90-day plan you can execute without a marketing hire",
    ],
  },
  {
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="lp-audience-svg">
        <rect width="40" height="40" rx="10" fill="rgba(3,105,161,0.08)" />
        <rect x="8" y="14" width="24" height="16" rx="2" stroke="#0369a1" strokeWidth="2" />
        <path d="M14 14v-2a2 2 0 012-2h8a2 2 0 012 2v2" stroke="#0369a1" strokeWidth="2" />
        <path d="M20 22v-4M17 22h6" stroke="#0369a1" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    tagline: "Cut your competitor research from 3 days to 30 minutes.",
    title: "Marketing Agencies",
    desc: "Scale your strategy delivery. Generate complete, data-driven marketing blueprints for new clients in under an hour — every time.",
    bullets: [
      "Repeatable 9-step workflow for consistent client delivery",
      "Real Google data makes every recommendation defensible",
      "Personas and roadmaps your clients can action immediately",
    ],
  },
  {
    icon: (
      <svg viewBox="0 0 40 40" fill="none" className="lp-audience-svg">
        <rect width="40" height="40" rx="10" fill="rgba(6,95,70,0.08)" />
        <circle cx="20" cy="20" r="10" stroke="#065f46" strokeWidth="2" />
        <circle cx="20" cy="20" r="4" stroke="#065f46" strokeWidth="2" />
        <path d="M20 10V8M20 32v-2M10 20H8M32 20h-2" stroke="#065f46" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    tagline: "Back every recommendation with real local market data.",
    title: "Business Consultants",
    desc: "Deliver deeper insights in a fraction of the time. Combine live Google data with AI analysis to make every strategy recommendation bulletproof.",
    bullets: [
      "Real competitor data your clients can verify themselves",
      "Client-ready outputs at every step — no reformatting needed",
      "Full session history for tracking strategy evolution over time",
    ],
  },
];

// ── Auth Modal ───────────────────────────────────────────────────
function AuthModal({ workflow, onClose }) {
  const { state, set, actions } = workflow;
  const [createMode, setCreateMode] = useState(false);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (createMode) actions.register();
    else actions.login();
  };

  return (
    <div className="lp-modal-overlay" onClick={onClose}>
      <div className="lp-modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="lp-modal-close" onClick={onClose} aria-label="Close">×</button>

        <div className="lp-modal-brand">MarketPilot</div>

        <div className="lp-modal-tabs">
          <button className={`lp-modal-tab${!createMode ? " active" : ""}`} onClick={() => setCreateMode(false)}>
            Sign In
          </button>
          <button className={`lp-modal-tab${createMode ? " active" : ""}`} onClick={() => setCreateMode(true)}>
            Create Account
          </button>
        </div>

        <h2 className="lp-modal-title">{createMode ? "Create your workspace" : "Welcome back"}</h2>
        <p className="lp-modal-sub">
          {createMode
            ? "Start your first AI marketing strategy in minutes."
            : "Sign in to continue your marketing workflow."}
        </p>

        <form className="lp-modal-form" onSubmit={handleSubmit}>
          <label className="lp-modal-label">Email</label>
          <input className="lp-modal-input" type="email" placeholder="you@company.com"
            value={state.email} onChange={(e) => set.setEmail(e.target.value)} autoFocus />

          <label className="lp-modal-label">Password</label>
          <input className="lp-modal-input" type="password" placeholder="Your password"
            value={state.password} onChange={(e) => set.setPassword(e.target.value)} />

          {createMode && (
            <>
              <label className="lp-modal-label">Company / Organisation</label>
              <input className="lp-modal-input" placeholder="Company or organization name"
                value={state.companyName} onChange={(e) => set.setCompanyName(e.target.value)} />
            </>
          )}

          <button type="submit" className="lp-modal-btn" disabled={state.busy}>
            {state.busy ? "Please wait…" : createMode ? "Create Account →" : "Sign In →"}
          </button>
        </form>

        {state.msg && <p className="lp-modal-msg">{state.msg}</p>}

        <p className="lp-modal-footer-note">
          {createMode ? (
            <>Already have an account?{" "}
              <button className="lp-modal-switch" onClick={() => setCreateMode(false)}>Sign in</button>
            </>
          ) : (
            <>No account yet?{" "}
              <button className="lp-modal-switch" onClick={() => setCreateMode(true)}>Create one free</button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

// ── Mock UI cards ─────────────────────────────────────────────────
function CompetitorMock() {
  return (
    <div className="lp-mock-card">
      <div className="lp-mock-head">Competitive Benchmarking Report</div>
      <div className="lp-mock-market-row">
        <div className="lp-mock-market-item">
          <span className="lp-mock-market-n">3</span>
          <span className="lp-mock-market-l">Competitors Found</span>
        </div>
        <div className="lp-mock-market-item">
          <span className="lp-mock-market-n">4.6★</span>
          <span className="lp-mock-market-l">Market Avg Rating</span>
        </div>
        <div className="lp-mock-market-item">
          <span className="lp-mock-market-n">2</span>
          <span className="lp-mock-market-l">Gaps Found</span>
        </div>
      </div>
      {DEMO_COMPETITORS.map((c) => (
        <div key={c.name} className="lp-mock-comp-row">
          <div>
            <div className="lp-mock-comp-name">{c.name}</div>
            <div className="lp-mock-comp-meta">{c.reviews} reviews · {c.price}</div>
          </div>
          <div className="lp-mock-comp-right">
            <span className="lp-mock-rating">{c.rating}★</span>
            <span className={`lp-mock-threat lp-threat-${c.threat}`}>{c.threat}</span>
          </div>
        </div>
      ))}
      <div className="lp-mock-swot-mini">
        <div className="lp-mock-swot-item lp-swot-s">Strengths</div>
        <div className="lp-mock-swot-item lp-swot-w">Weaknesses</div>
        <div className="lp-mock-swot-item lp-swot-o">Opportunities</div>
        <div className="lp-mock-swot-item lp-swot-t">Threats</div>
      </div>
    </div>
  );
}

function PersonaMock() {
  return (
    <div className="lp-mock-card">
      <div className="lp-mock-head">Buyer Persona</div>
      <div className="lp-mock-persona-head">
        <div className="lp-mock-avatar">CC</div>
        <div>
          <div className="lp-mock-persona-name">Celebration Chloe</div>
          <div className="lp-mock-persona-meta">28 · Graduate Student, UMD · College Park, MD</div>
        </div>
      </div>
      <div className="lp-mock-section">
        <div className="lp-mock-label">Goal</div>
        <div className="lp-mock-value">Find a reliable florist for birthdays, anniversaries, and campus events she can count on.</div>
      </div>
      <div className="lp-mock-section lp-mock-pain-bg">
        <div className="lp-mock-label">Pain Point</div>
        <div className="lp-mock-value">Chain store flowers feel generic, arrive wilted, and have zero personal touch.</div>
      </div>
      <div className="lp-mock-section">
        <div className="lp-mock-label">How She Decides</div>
        <div className="lp-mock-value">Checks Instagram photos first, then reads Google reviews — books if 4.5+ and same-day is available.</div>
      </div>
      <div className="lp-mock-channels-row">
        {["Instagram", "Google Search", "UMD boards"].map((ch) => (
          <span key={ch} className="lp-mock-channel-pill">{ch}</span>
        ))}
      </div>
      <div className="lp-mock-key-msg">"Beautiful, fresh flowers — delivered to campus today."</div>
    </div>
  );
}

function PositioningMock() {
  return (
    <div className="lp-mock-card">
      <div className="lp-mock-head">Positioning Statement</div>
      <div className="lp-mock-tagline">"College Park's freshest flowers, delivered today."</div>
      <div className="lp-mock-stmt">
        For College Park residents and UMD campus community who want thoughtful, same-day floral
        arrangements, The Bloom Room delivers locally-sourced flowers with a personal touch —
        unlike chain stores that treat every order as a transaction.
      </div>
      <div className="lp-mock-two-col">
        <div>
          <div className="lp-mock-label">Key Differentiators</div>
          <ul className="lp-mock-list">
            <li>Same-day design &amp; delivery</li>
            <li>Locally sourced seasonal stems</li>
            <li>Personalised consultation</li>
            <li>UMD events specialist</li>
          </ul>
        </div>
        <div>
          <div className="lp-mock-label">Target Segment</div>
          <div className="lp-mock-value" style={{ marginTop: 8 }}>
            College Park residents, UMD students &amp; faculty celebrating milestones
          </div>
        </div>
      </div>
    </div>
  );
}

function RoadmapMock() {
  const milestones = [
    { week: "Week 1–2", action: "Set up Google Business Profile and request 10 reviews from happy customers", channel: "Google" },
    { week: "Week 3–4", action: "Launch Instagram with 3× per week arrangement posts and short Reels", channel: "Instagram" },
    { week: "Week 5–6", action: "Partner with UMD Events for campus flower delivery programme", channel: "Campus" },
    { week: "Week 7–8", action: "Run first Google Ads campaign targeting \"flower delivery College Park\"", channel: "Google Ads" },
  ];
  return (
    <div className="lp-mock-card">
      <div className="lp-mock-head">90-Day Roadmap</div>
      {milestones.map((m, i) => (
        <div key={i} className="lp-mock-milestone">
          <div className="lp-mock-milestone-week">{m.week}</div>
          <div className="lp-mock-milestone-action">{m.action}</div>
          <span className="lp-mock-milestone-channel">{m.channel}</span>
        </div>
      ))}
    </div>
  );
}

// ── Section components ───────────────────────────────────────────

function LpNav({ onOpenAuth }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className={`lp-nav${scrolled ? " lp-nav-solid" : ""}`}>
      <div className="lp-nav-inner">
        <div className="lp-nav-logo">MarketPilot</div>
        <div className="lp-nav-links">
          <a href="#how-it-works" className="lp-nav-link">How it works</a>
          <a href="#features" className="lp-nav-link">Features</a>
          <a href="#samples" className="lp-nav-link">See results</a>
          <a href="#audience" className="lp-nav-link">Who it's for</a>
        </div>
        <div className="lp-nav-actions">
          <button className="lp-nav-signin" onClick={onOpenAuth}>Sign In</button>
          <button className="lp-nav-cta" onClick={onOpenAuth}>Get Started →</button>
        </div>
      </div>
    </nav>
  );
}

function LpHero({ onOpenAuth }) {
  return (
    <section className="lp-hero">
      <div className="lp-hero-glow" />
      <div className="lp-container lp-hero-inner">
        <div className="lp-hero-content">
          <div className="lp-badge">AI Marketing Strategy · Powered by Real Google Data</div>
          <h1 className="lp-hero-h1">
            See exactly where you stand against every{" "}
            <span className="lp-hero-highlight">competitor in your area.</span>
          </h1>
          <p className="lp-hero-sub">
            MarketPilot scans Google Places for your real local competitors, builds your
            market positioning, creates data-driven buyer personas, and produces a
            90-day execution plan — all in a single 30-minute session.
          </p>
          <div className="lp-hero-actions">
            <button className="lp-btn-primary" onClick={onOpenAuth}>Analyse My Market Free →</button>
            <a href="#how-it-works" className="lp-btn-ghost">See a real example ↓</a>
          </div>
          <div className="lp-hero-trust">
            <span className="lp-hero-trust-dot" />
            <span>Trusted by salons, dental practices, restaurants, agencies &amp; consultants</span>
          </div>
        </div>

        <div className="lp-hero-preview">
          <div className="lp-preview-label">Live output — The Bloom Room, College Park MD 20740</div>
          <div className="lp-preview-frame">
            <div className="lp-preview-header">
              <div className="lp-preview-dots">
                <span className="lp-preview-dot lp-dot-red" />
                <span className="lp-preview-dot lp-dot-yellow" />
                <span className="lp-preview-dot lp-dot-green" />
              </div>
              <span className="lp-preview-title">Competitive Benchmarking — MarketPilot</span>
            </div>
            <div className="lp-preview-market">
              <div className="lp-preview-stat">
                <span className="lp-preview-stat-n">3</span>
                <span className="lp-preview-stat-l">Competitors Found</span>
              </div>
              <div className="lp-preview-stat">
                <span className="lp-preview-stat-n">4.6★</span>
                <span className="lp-preview-stat-l">Market Avg Rating</span>
              </div>
              <div className="lp-preview-stat">
                <span className="lp-preview-stat-n lp-stat-gap">2 Gaps</span>
                <span className="lp-preview-stat-l">Uncovered in Market</span>
              </div>
            </div>
            <div className="lp-preview-competitors">
              {DEMO_COMPETITORS.map((c) => (
                <div key={c.name} className="lp-preview-comp">
                  <div>
                    <div className="lp-preview-comp-name">{c.name}</div>
                    <div className="lp-preview-comp-meta">{c.reviews} reviews · {c.price}</div>
                  </div>
                  <div className="lp-preview-comp-right">
                    <span className="lp-preview-rating">{c.rating}★</span>
                    <span className={`lp-mock-threat lp-threat-${c.threat}`}>{c.threat}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="lp-preview-insight">
              <span className="lp-preview-insight-dot">●</span>
              <span>Gap identified: No competitor offers same-day delivery with online booking</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function LpTrustStrip() {
  const industries = [
    "Hair Salons", "Dental Practices", "Flower Shops", "Law Firms",
    "Restaurants", "Fitness Studios", "Retail Stores", "Marketing Agencies",
  ];
  return (
    <div className="lp-trust-strip">
      <div className="lp-container">
        <p className="lp-trust-label">Used across industries to find local competitive advantage</p>
        <div className="lp-trust-industries">
          {industries.map((ind, i) => (
            <span key={ind} className="lp-trust-industry">
              {ind}{i < industries.length - 1 && <span className="lp-trust-sep">·</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function LpStats() {
  const stats = [
    { value: "9-Step", label: "Proven Workflow" },
    { value: "30 Min", label: "Your First Strategy" },
    { value: "100%", label: "Real Google Data" },
    { value: "Free", label: "To Get Started" },
  ];
  return (
    <section className="lp-stats">
      <div className="lp-container">
        <div className="lp-stats-grid">
          {stats.map((s) => (
            <div key={s.label} className="lp-stat lp-reveal">
              <div className="lp-stat-value">{s.value}</div>
              <div className="lp-stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LpHowItWorks() {
  return (
    <section className="lp-how" id="how-it-works">
      <div className="lp-container">
        <div className="lp-section-kicker">The Workflow</div>
        <h2 className="lp-section-title">One session. Four phases. A complete marketing strategy.</h2>
        <p className="lp-section-sub">
          Each phase feeds the next. Real data at every step.
          Average time from signup to full strategy: <strong>30 minutes</strong>.
        </p>
        <div className="lp-phases-row">
          {HOW_PHASES.map((phase, i) => (
            <div key={phase.n} className="lp-phase-wrap lp-reveal" style={{ transitionDelay: `${i * 80}ms` }}>
              <div className="lp-phase-card">
                <div className="lp-phase-num">{phase.n}</div>
                <div className="lp-phase-title">{phase.title}</div>
                <div className="lp-phase-sub">{phase.subtitle}</div>
                <div className="lp-phase-desc">{phase.desc}</div>
                <div className="lp-phase-tags">
                  {phase.steps.map((s) => (
                    <span key={s} className="lp-phase-tag">{s}</span>
                  ))}
                </div>
                <div className="lp-phase-time">{phase.time}</div>
              </div>
              {i < HOW_PHASES.length - 1 && (
                <div className="lp-phase-arrow" aria-hidden="true">›</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LpFeatures() {
  const features = [
    {
      kicker: "Feature 01 — Competitive Intelligence",
      title: "Find every competitor — and every gap they're leaving open.",
      bullets: [
        "Discovers all competitors Google knows about in your exact area — not just the obvious ones",
        "Extracts real customer review language to reveal what buyers in your market actually care about",
        "Identifies hours your rivals aren't covering — usually your easiest and fastest quick win",
        "Price vs. rating chart shows exactly where you're positioned and where the opportunity sits",
      ],
      visual: <CompetitorMock />,
    },
    {
      kicker: "Feature 02 — Buyer Personas",
      title: "Personas built from real customer voices, not assumptions.",
      bullets: [
        "Every persona is grounded in real Google review text from your competitor category — not invented",
        "Written in the language your customers already use — ready to copy directly into ads and content",
        "Includes the precise marketing message most likely to convert each persona type",
        "Refine or regenerate at any stage as your understanding of the market deepens",
      ],
      visual: <PersonaMock />,
      flip: true,
    },
    {
      kicker: "Feature 03 — 90-Day Roadmap",
      title: "Stop planning. Start with specific actions that move the needle.",
      bullets: [
        "Breaks your channel strategy into specific weekly marketing actions — not vague goals or themes",
        "Every task has a clear channel, action description, timeline, and measurable outcome",
        "Ordered by impact, so you always begin with the action that generates results fastest",
        "Save multiple sessions per business — ideal for agencies tracking client strategy over time",
      ],
      visual: <RoadmapMock />,
    },
  ];

  return (
    <section className="lp-features" id="features">
      <div className="lp-container">
        {features.map((f, i) => (
          <div key={i} className={`lp-feature-row lp-reveal${f.flip ? " lp-feature-flip" : ""}`}>
            <div className="lp-feature-text">
              <div className="lp-section-kicker">{f.kicker}</div>
              <h3 className="lp-feature-title">{f.title}</h3>
              <ul className="lp-feature-bullets">
                {f.bullets.map((b, j) => <li key={j}>{b}</li>)}
              </ul>
            </div>
            <div className="lp-feature-visual">{f.visual}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function LpSamples() {
  const [active, setActive] = useState(0);
  const tabs = ["Competitor Analysis", "Positioning Statement", "Buyer Persona", "90-Day Roadmap"];
  const panels = [<CompetitorMock />, <PositioningMock />, <PersonaMock />, <RoadmapMock />];

  return (
    <section className="lp-samples" id="samples">
      <div className="lp-container">
        <div className="lp-section-kicker lp-kicker-light">Real Output Quality</div>
        <h2 className="lp-section-title lp-title-light">See exactly what you'll get.</h2>
        <p className="lp-section-sub lp-sub-light">
          Real outputs generated for a flower shop in College Park, MD 20740.
          Your results are built on your actual business, local competitors, and live Google data.
        </p>
        <div className="lp-samples-tabs">
          {tabs.map((t, i) => (
            <button key={t} className={`lp-sample-tab${active === i ? " active" : ""}`} onClick={() => setActive(i)}>
              {t}
            </button>
          ))}
        </div>
        <div className="lp-samples-panel">{panels[active]}</div>
      </div>
    </section>
  );
}

function LpTestimonials() {
  return (
    <section className="lp-testimonials lp-reveal">
      <div className="lp-container">
        <div className="lp-section-kicker">What people say</div>
        <h2 className="lp-section-title">Results people can feel from day one.</h2>
        <div className="lp-testimonials-grid">
          {TESTIMONIALS.map((t, i) => (
            <div key={i} className="lp-quote-card lp-reveal" style={{ transitionDelay: `${i * 100}ms` }}>
              <div className="lp-stars">★★★★★</div>
              <p className="lp-quote-text">{t.quote}</p>
              <div className="lp-quote-author">
                <div className="lp-quote-avatar" style={{ background: t.color }}>{t.initial}</div>
                <div>
                  <div className="lp-quote-name">{t.name}</div>
                  <div className="lp-quote-role">{t.role} · {t.location}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LpAudience() {
  return (
    <section className="lp-audience" id="audience">
      <div className="lp-container">
        <div className="lp-section-kicker">Who It's For</div>
        <h2 className="lp-section-title">Built for the people who make marketing decisions.</h2>
        <div className="lp-audience-grid">
          {AUDIENCES.map((a, i) => (
            <div key={a.title} className="lp-audience-card lp-reveal" style={{ transitionDelay: `${i * 100}ms` }}>
              <div className="lp-audience-icon-wrap">{a.icon}</div>
              <div className="lp-audience-tagline">{a.tagline}</div>
              <h3 className="lp-audience-title">{a.title}</h3>
              <p className="lp-audience-desc">{a.desc}</p>
              <ul className="lp-audience-bullets">
                {a.bullets.map((b) => <li key={b}>{b}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LpCta({ onOpenAuth }) {
  return (
    <section className="lp-cta lp-reveal">
      <div className="lp-container lp-cta-inner">
        <div className="lp-cta-eyebrow">Stop guessing. Start winning.</div>
        <h2 className="lp-cta-title">
          Your competitors are already<br />on Google. Are you ready?
        </h2>
        <p className="lp-cta-sub">
          Free to start · No credit card · No setup · First full strategy in 30 minutes
        </p>
        <button className="lp-btn-primary lp-btn-large" onClick={onOpenAuth}>
          Analyse My Market Free →
        </button>
      </div>
    </section>
  );
}

function LpFooter({ onOpenAuth }) {
  return (
    <footer className="lp-footer">
      <div className="lp-container">
        <div className="lp-footer-grid">
          <div className="lp-footer-brand">
            <div className="lp-footer-logo">MarketPilot</div>
            <p className="lp-footer-tagline">
              AI-driven marketing strategy for small businesses, agencies, and consultants.
              From live competitor data to a 90-day execution plan — in one guided session.
            </p>
            <div className="lp-footer-address">
              <div>College Park, MD 20740</div>
              <div><a href="mailto:hello@marketpilot.ai" className="lp-footer-email">hello@marketpilot.ai</a></div>
              <div><a href="mailto:support@marketpilot.ai" className="lp-footer-email">support@marketpilot.ai</a></div>
            </div>
            <div className="lp-footer-socials">
              <a href="#" className="lp-social-link" aria-label="LinkedIn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z" />
                  <rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" />
                </svg>
              </a>
              <a href="#" className="lp-social-link" aria-label="X / Twitter">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z" />
                </svg>
              </a>
              <a href="#" className="lp-social-link" aria-label="Instagram">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
                  <circle cx="12" cy="12" r="4" />
                  <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
                </svg>
              </a>
            </div>
          </div>

          <div className="lp-footer-col">
            <div className="lp-footer-col-title">Product</div>
            <a href="#how-it-works" className="lp-footer-link">How it Works</a>
            <a href="#features" className="lp-footer-link">Features</a>
            <a href="#samples" className="lp-footer-link">Sample Results</a>
            <a href="#audience" className="lp-footer-link">Who It's For</a>
            <button className="lp-footer-link lp-footer-link-btn" onClick={onOpenAuth}>Get Started</button>
          </div>

          <div className="lp-footer-col">
            <div className="lp-footer-col-title">Company</div>
            <a href="#" className="lp-footer-link">About Us</a>
            <a href="#" className="lp-footer-link">Blog</a>
            <a href="#" className="lp-footer-link">Careers</a>
            <a href="#" className="lp-footer-link">Press</a>
          </div>

          <div className="lp-footer-col">
            <div className="lp-footer-col-title">Contact &amp; Legal</div>
            <a href="mailto:hello@marketpilot.ai" className="lp-footer-link">hello@marketpilot.ai</a>
            <a href="mailto:support@marketpilot.ai" className="lp-footer-link">support@marketpilot.ai</a>
            <a href="#" className="lp-footer-link">Privacy Policy</a>
            <a href="#" className="lp-footer-link">Terms of Service</a>
            <a href="#" className="lp-footer-link">Cookie Policy</a>
          </div>
        </div>

        <div className="lp-footer-bottom">
          <span>© 2026 MarketPilot. All rights reserved.</span>
          <span>College Park, MD 20740 · hello@marketpilot.ai</span>
        </div>
      </div>
    </footer>
  );
}

// ── Main export ──────────────────────────────────────────────────
export default function LandingPage({ workflow }) {
  const [showAuth, setShowAuth] = useState(false);
  const openAuth = () => setShowAuth(true);
  const closeAuth = () => setShowAuth(false);

  useScrollReveal();

  return (
    <div className="lp-root">
      <LpNav onOpenAuth={openAuth} />
      <LpHero onOpenAuth={openAuth} />
      <LpTrustStrip />
      <LpStats />
      <LpHowItWorks />
      <LpFeatures />
      <LpSamples />
      <LpTestimonials />
      <LpAudience />
      <LpCta onOpenAuth={openAuth} />
      <LpFooter onOpenAuth={openAuth} />
      {showAuth && workflow && (
        <AuthModal workflow={workflow} onClose={closeAuth} />
      )}
    </div>
  );
}
