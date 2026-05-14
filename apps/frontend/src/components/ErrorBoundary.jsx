import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    const { pageName = "This page" } = this.props;
    return (
      <div className="eb-wrap">
        <div className="eb-icon" aria-hidden="true">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h3 className="eb-title">{pageName} ran into a problem</h3>
        <p className="eb-desc">
          Something went wrong rendering this section. Your data is safe — try refreshing the page.
        </p>
        {this.state.error?.message && (
          <pre className="eb-detail">{this.state.error.message}</pre>
        )}
        <button
          className="eb-btn"
          onClick={() => this.setState({ hasError: false, error: null })}
        >
          Try again
        </button>
      </div>
    );
  }
}
