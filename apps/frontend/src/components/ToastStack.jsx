export default function ToastStack({ toasts = [], onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="toast-stack">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast ${t.type || "info"}`}
          onClick={() => onDismiss?.(t.id)}
          role="status"
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
