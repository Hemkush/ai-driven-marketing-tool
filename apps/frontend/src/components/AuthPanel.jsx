import { useState } from "react";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validate(email, password, createMode, companyName) {
  if (!email.trim()) return "Email is required.";
  if (!EMAIL_RE.test(email.trim())) return "Enter a valid email address (e.g. you@example.com).";
  if (!password) return "Password is required.";
  if (createMode && password.length < 8) return "Password must be at least 8 characters.";
  if (createMode && !companyName?.trim()) return "Company or organization name is required.";
  return null;
}

function PendingVerificationScreen({ email, resendVerification, busy, onBack }) {
  const [resent, setResent] = useState(false);

  const handleResend = async () => {
    await resendVerification(email);
    setResent(true);
  };

  return (
    <div className="cas-page">
      <div className="cas-topbar">MARKETPILOT</div>
      <div className="cas-wrap">
        <div className="cas-verify-card">
          <div className="cas-verify-icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
          </div>
          <h2 className="cas-verify-title">Check your email</h2>
          <p className="cas-verify-sub">
            We sent a verification link to<br />
            <strong>{email}</strong>
          </p>
          <p className="cas-verify-hint">
            Click the link in the email to activate your account. Check your spam folder if you don't see it.
          </p>
          {resent && (
            <p className="cas-verify-resent">Verification email resent!</p>
          )}
          <button
            className="cas-login-btn"
            onClick={handleResend}
            disabled={busy || resent}
            style={{ marginTop: 8 }}
          >
            {busy ? "Sending…" : resent ? "Email sent ✓" : "Resend verification email"}
          </button>
          <button className="btn ghost" onClick={onBack} style={{ marginTop: 8 }}>
            ← Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AuthPanel({
  companyName,
  setCompanyName,
  email,
  setEmail,
  password,
  setPassword,
  register,
  login,
  resendVerification,
  clearPendingVerification,
  busy,
  msg,
  pendingVerificationEmail,
}) {
  const [createMode, setCreateMode] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const onPrimaryAction = () => {
    const err = validate(email, password, createMode, companyName);
    if (err) { setValidationError(err); return; }
    setValidationError(null);
    if (createMode) { register(); return; }
    login();
  };

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    if (validationError) setValidationError(null);
  };

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
    if (validationError) setValidationError(null);
  };

  // Show pending verification screen after register or unverified login attempt
  if (pendingVerificationEmail) {
    return (
      <PendingVerificationScreen
        email={pendingVerificationEmail}
        resendVerification={resendVerification}
        busy={busy}
        onBack={clearPendingVerification}
      />
    );
  }

  const loginErrorIsUnverified = msg?.includes("EMAIL_NOT_VERIFIED");

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
              placeholder="you@example.com"
              type="email"
              value={email}
              onChange={handleEmailChange}
              onKeyDown={(e) => e.key === "Enter" && onPrimaryAction()}
            />

            <label className="cas-label">PASSWORD</label>
            <input
              className="cas-input"
              placeholder={createMode ? "Min. 8 characters" : "Password"}
              type="password"
              value={password}
              onChange={handlePasswordChange}
              onKeyDown={(e) => e.key === "Enter" && onPrimaryAction()}
            />

            {createMode && (
              <>
                <label className="cas-label">COMPANY / ORGANIZATION</label>
                <input
                  className="cas-input"
                  placeholder="Company or organization name"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </>
            )}

            {validationError && (
              <p className="cas-validation-error">{validationError}</p>
            )}

            {loginErrorIsUnverified && (
              <p className="cas-validation-error">
                Email not verified. Check your inbox or{" "}
                <button
                  className="cas-inline-link"
                  onClick={() => resendVerification(email)}
                  disabled={busy}
                >
                  resend the verification email
                </button>.
              </p>
            )}

            <button className="cas-login-btn" onClick={onPrimaryAction} disabled={busy}>
              {busy ? "Please wait…" : createMode ? "Create Account" : "Sign In"}
            </button>
            <button
              className="btn ghost"
              onClick={() => { setCreateMode((v) => !v); setValidationError(null); }}
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
          <a href="#" onClick={(e) => e.preventDefault()}>Forgot your password?</a>
          <span>/</span>
          <a href="#" onClick={(e) => e.preventDefault()}>Need help?</a>
        </div>

        {msg && !loginErrorIsUnverified && <p className="cas-msg">{msg}</p>}
      </div>
    </div>
  );
}
