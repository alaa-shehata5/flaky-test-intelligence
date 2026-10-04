export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({
  message,
  requestId,
  onRetry,
}: {
  message: string;
  requestId?: string;
  onRetry: () => void;
}) {
  return (
    <div className="state state-error" role="alert">
      <p className="state-title">Something went wrong</p>
      <p>{message}</p>
      {requestId && requestId !== '-' && <p className="muted">Request ID: {requestId}</p>}
      <button type="button" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="state" role="status">
      <p className="state-title">No data</p>
      <p>{message}</p>
    </div>
  );
}
