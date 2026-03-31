import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authClient } from "../lib/mvpClient";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("verifying"); // verifying | success | error
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("Invalid verification link — no token found.");
      return;
    }
    authClient.verifyEmail(token)
      .then((data) => {
        setStatus("success");
        setMessage(data.message || "Email verified successfully.");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err?.response?.data?.detail || "Verification failed. The link may have expired.");
      });
  }, []);

  return (
    <div className="cas-page">
      <div className="cas-topbar">MARKETPILOT</div>
      <div className="cas-wrap">
        <div className="cas-verify-card">
          {status === "verifying" && (
            <>
              <div className="cas-verify-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              </div>
              <h2 className="cas-verify-title">Verifying your email…</h2>
            </>
          )}

          {status === "success" && (
            <>
              <div className="cas-verify-icon cas-verify-icon-success">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <h2 className="cas-verify-title">Email verified!</h2>
              <p className="cas-verify-sub">{message}</p>
              <button className="cas-login-btn" onClick={() => navigate("/login")}
                style={{ marginTop: 16 }}>
                Sign In →
              </button>
            </>
          )}

          {status === "error" && (
            <>
              <div className="cas-verify-icon cas-verify-icon-error">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
              </div>
              <h2 className="cas-verify-title">Verification failed</h2>
              <p className="cas-verify-sub">{message}</p>
              <button className="cas-login-btn" onClick={() => navigate("/login")}
                style={{ marginTop: 16 }}>
                Back to Sign In
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
