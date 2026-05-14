import { useEffect, useRef } from "react";
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from "lucide-react";

const ICON_MAP = {
  success: <CheckCircle size={16} strokeWidth={2} />,
  error:   <AlertCircle  size={16} strokeWidth={2} />,
  info:    <Info         size={16} strokeWidth={2} />,
  warning: <AlertTriangle size={16} strokeWidth={2} />,
};

const DEFAULT_DURATION = 4000;

function Toast({ toast, onDismiss }) {
  const progressRef = useRef(null);
  const duration = toast.duration ?? DEFAULT_DURATION;

  useEffect(() => {
    const t = setTimeout(() => onDismiss(toast.id), duration);

    if (progressRef.current) {
      progressRef.current.style.transition = `width ${duration}ms linear`;
      requestAnimationFrame(() => {
        if (progressRef.current) progressRef.current.style.width = "0%";
      });
    }

    return () => clearTimeout(t);
  }, [toast.id, onDismiss, duration]);

  const type = toast.type || "info";

  return (
    <div className={`toast2 toast2-${type}`} role="status" aria-live="polite">
      <div className="toast2-body">
        <span className={`toast2-icon toast2-icon-${type}`}>
          {ICON_MAP[type] || ICON_MAP.info}
        </span>
        <div className="toast2-content">
          {toast.title && <div className="toast2-title">{toast.title}</div>}
          <div className="toast2-message">{toast.message}</div>
          {toast.action && (
            <button
              className="toast2-action"
              onClick={() => { toast.action.handler(); onDismiss(toast.id); }}
            >
              {toast.action.label}
            </button>
          )}
        </div>
        <button className="toast2-close" onClick={() => onDismiss(toast.id)} aria-label="Dismiss">
          <X size={14} strokeWidth={2.5} />
        </button>
      </div>
      <div className="toast2-progress-track">
        <div
          ref={progressRef}
          className={`toast2-progress toast2-progress-${type}`}
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}

export default function ToastStack({ toasts = [], onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="toast-stack">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
