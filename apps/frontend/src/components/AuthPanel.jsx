import { useState } from "react";

export default function AuthPanel({
  companyName,
  setCompanyName,
  email,
  setEmail,
  password,
  setPassword,
  register,
  login,
  busy,
  msg,
}) {
  const [createMode, setCreateMode] = useState(false);

  const onPrimaryAction = () => {
    if (createMode) {
      register();
      return;
    }
    login();
  };

  return (
    <div className="cas-page">
      <div className="cas-topbar">MARKETPILOT</div>

      <div className="cas-wrap">
        <h1 className="cas-title">
          {createMode ? "Create your workspace account" : "Sign in to your workspace"}
        </h1>

        <section className="cas-card">
          <div className="cas-left">
            <div className="cas-id-row">
              <span className="cas-user-icon" aria-hidden="true" />
              <span className="cas-label">EMAIL</span>
            </div>
            <input
              className="cas-input strong"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <label className="cas-label">PASSWORD</label>
            <input
              className="cas-input"
              placeholder="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {createMode && (
              <>
                <label className="cas-label">COMPANY / ORGANIZATION</label>
                <input
                  className="cas-input optional"
                  placeholder="Company or organization name"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </>
            )}

            <button className="cas-login-btn" onClick={onPrimaryAction} disabled={busy}>
              {createMode ? "Create Account" : "Sign In"}
            </button>
            <button
              className="btn ghost"
              onClick={() => setCreateMode((v) => !v)}
              disabled={busy}
            >
              {createMode ? "Back to sign in" : "Create account"}
            </button>
          </div>

          <div className="cas-right">
            <p>
              Build, refine, and execute your AI-powered marketing strategy in one place.
            </p>
            <hr />
            <p>
              Keep your credentials safe. Never share your password and always sign in from
              trusted devices.
            </p>
            <p className="cas-warning">Your strategy data is private to your account.</p>
          </div>
        </section>

        <div className="cas-links">
          <a href="#" onClick={(e) => e.preventDefault()}>
            Forgot your password?
          </a>
          <span>/</span>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Forgot your email?
          </a>
          <span>/</span>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Need help?
          </a>
        </div>

        {msg && <p className="cas-msg">{msg}</p>}
      </div>
    </div>
  );
}
