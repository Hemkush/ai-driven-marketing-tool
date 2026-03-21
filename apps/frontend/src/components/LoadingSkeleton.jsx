export function LoadingSkeleton({ lines = 4 }) {
  return (
    <div className="compact-card">
      {Array.from({ length: lines }).map((_, idx) => (
        <div key={idx} className="skeleton line" />
      ))}
    </div>
  );
}
