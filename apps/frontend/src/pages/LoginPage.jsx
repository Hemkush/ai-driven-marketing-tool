import { Link } from "react-router-dom";
import AuthPanel from "../components/AuthPanel";

export default function LoginPage({ workflow }) {
  const { state, set, actions } = workflow;
  return (
    <>
      <div className="lp-auth-back-bar">
        <Link to="/" className="lp-auth-back-link">← Back to MarketPilot</Link>
      </div>
      <AuthPanel
        companyName={state.companyName}
        setCompanyName={set.setCompanyName}
        email={state.email}
        setEmail={set.setEmail}
        password={state.password}
        setPassword={set.setPassword}
        register={actions.register}
        login={actions.login}
        resendVerification={actions.resendVerification}
        clearPendingVerification={actions.clearPendingVerification}
        busy={state.busy}
        msg={state.msg}
        pendingVerificationEmail={state.pendingVerificationEmail}
      />
    </>
  );
}
