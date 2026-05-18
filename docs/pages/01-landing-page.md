# Landing Page

**File:** `apps/frontend/src/pages/LandingPage.jsx`
**Route:** `/` (shown only to unauthenticated users)
**Access:** Public — no login required

---

## Purpose

The landing page is the public-facing marketing page for MarketPilot. Its job is to:
1. Explain the product's value proposition to visitors who know nothing about it
2. Show real sample outputs so users understand what they'll get
3. Build trust through stats, testimonials, and social proof
4. Convert visitors into signed-up users via the auth modal

---

## What the User Sees (Section by Section)

### 1. Navigation Bar (`LpNav`)
- Fixed top bar with the brand name "MarketPilot"
- Links scroll to sections: How it Works, See Results, Who It's For
- Two CTA buttons: "Sign In" and "Get Started →"
- The nav adds a solid background (`lp-nav-solid`) once the user scrolls past 20px

### 2. Hero Section (`LpHero`)
- Main headline: "Your competitors are gaining customers you don't know you're losing."
- Sub-copy explaining the product in one paragraph
- Two action buttons: "Get My Free Analysis →" (primary) and "See it in action ↓" (ghost)
- A live browser preview mock on the right side showing a sample competitive benchmarking report for "The Bloom Room, College Park MD" — a fictional local flower shop used throughout as the demo business

### 3. Trust Strip (`LpTrustStrip`)
- A list of industries the tool supports (Hair Salons, Dental Practices, etc.)
- Four stat badges: 500+ businesses analyzed, 30 min average time, 100% real Google data, Free to start

### 4. Stats Bar (`LpStats`)
- Four large-number highlights: 9-Step Workflow, 30 Min strategy, 100% Real Google Data, Free to Get Started

### 5. Product Demo (`LpProductDemo`)
- A dark browser-chrome mock showing real sample outputs
- Tab switcher with four tabs: Competitor Analysis, Positioning Statement, Buyer Persona, 90-Day Roadmap
- Each tab swaps in a different mock output card
- Switching tabs triggers a CSS entrance animation via `key={active}` on the panel div

### 6. How It Works (`LpHowItWorks`)
- Four-phase workflow cards: Set Up → Analyse → Strategise → Execute
- Each card shows the phase number, title, subtitle, description, step tags (e.g., "Buyer Personas"), and approximate time
- Arrow separators between phases (hidden on the last card)

### 7. Feature Deep-Dives (`LpFeatures`)
- Three alternating feature rows (text left + visual right, then flipped, then normal)
  - Feature 01: Competitive Intelligence (with `CompetitorMock`)
  - Feature 02: Buyer Personas (with `PersonaMock`)
  - Feature 03: 90-Day Roadmap (with `RoadmapMock`)
- Each feature has a kicker label, title, and 4 bullet points

### 8. Testimonials (`LpTestimonials`)
- Three quote cards in a grid
- Each card shows: a metric badge (e.g., "★ 3 new bookings in week one"), 5 stars, the quote, avatar initials, name, role, and location

### 9. Who It's For (`LpAudience`)
- Three audience cards: Small Business Owners, Marketing Agencies, Business Consultants
- Each has a custom SVG icon, a tagline, description, and three bullet points

### 10. Final CTA (`LpCta`)
- Eyebrow text: "Your local market is moving."
- Headline: "Know exactly where the opportunity is — before your competitors do."
- Sub-copy and a large primary CTA button

### 11. Footer (`LpFooter`)
- Brand column with logo, tagline, address, email links, and social media icons
- Product links column
- Company links column
- Contact & Legal links column
- Bottom bar with copyright

---

## Auth Modal (`AuthModal`)

Clicking any CTA button opens a floating modal with:
- **Sign In tab**: email + password fields, "Sign In →" button
- **Create Account tab**: email + password + company name fields, "Create Account →" button
- Tab switching between Sign In and Create Account with a toggle link at the bottom
- Closes on `Escape` key press or clicking the backdrop
- While open, `document.body.style.overflow = "hidden"` prevents the page behind from scrolling
- Error/success messages appear below the form via `state.msg`

On successful login or registration, the `workflow.actions.login()` / `workflow.actions.register()` action updates `state.me`, which causes `App.jsx` to redirect the user into the authenticated pipeline (`/projects`).

---

## Mock Output Components

These are static display-only components used in the hero preview and product demo sections. They use hardcoded data for "The Bloom Room" flower shop:

| Component | Displays |
|---|---|
| `CompetitorMock` | Competitor table with ratings, prices, threat levels, and SWOT tags |
| `PersonaMock` | A single buyer persona card ("Celebration Chloe") |
| `PositioningMock` | A positioning statement card with differentiators |
| `RoadmapMock` | A 4-milestone week-by-week roadmap |

---

## Scroll Reveal Animations

The `useScrollReveal` hook (defined inside the file) sets up an `IntersectionObserver` that adds the class `lp-visible` to any element with class `lp-reveal` when it enters the viewport (8% threshold). CSS transitions on `.lp-reveal` animate the element from opacity 0 + translateY(20px) to fully visible. The observer unobserves each element after it has fired once, so the animation plays only on first scroll-in.

---

## State Used

This page reads from and writes to `workflow.state`:

| State field | How it's used |
|---|---|
| `state.email` | Bound to the email input in the auth modal |
| `state.password` | Bound to the password input |
| `state.companyName` | Bound to the company name input (create account only) |
| `state.busy` | Disables the submit button while a login/register request is in flight |
| `state.msg` | Displays success or error messages below the form |

---

## When This Page Is Shown

`App.jsx` renders `LandingPage` when `state.me === null` (the user is not authenticated). Once the user logs in successfully, `state.me` is populated and `App.jsx` renders the authenticated app shell, redirecting to `/projects`.
