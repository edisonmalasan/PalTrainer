import type { ReactNode } from "react";

interface EmptyStateProps {
  readonly headline: string;
  readonly description?: string;
  readonly action?: {
    readonly label: string;
    readonly onClick: () => void;
  };
  readonly secondaryAction?: {
    readonly label: string;
    readonly onClick: () => void;
  };
  readonly children?: ReactNode;
  readonly className?: string;
}

export function EmptyState({
  headline,
  description,
  action,
  secondaryAction,
  children,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={[
        "flex flex-col items-center justify-center border border-dashed border-shell-line bg-shell-panel/50 px-6 py-12 text-center",
        className,
      ].join(" ")}
    >
      {/* Technical geometric empty glyph */}
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-sm border border-shell-line bg-shell-surface shadow-sm">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-shell-muted"
          aria-hidden="true"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18" />
          <path d="M9 21V9" />
          <circle cx="15" cy="15" r="2" strokeDasharray="2 2" />
        </svg>
      </div>

      <h3 className="text-sm font-semibold tracking-tight text-shell-ink">{headline}</h3>

      {description && (
        <p className="mt-1.5 max-w-[45ch] text-xs leading-relaxed text-shell-muted">
          {description}
        </p>
      )}

      {(action || secondaryAction) && (
        <div className="mt-5 flex items-center gap-3">
          {action && (
            <button
              type="button"
              onClick={action.onClick}
              className="border border-shell-accent-solid bg-shell-accent-solid px-4 py-1.5 text-xs font-medium uppercase tracking-wider text-white transition hover:bg-shell-accent-solid-hover active:translate-y-[1px]"
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="border border-shell-line bg-shell-surface px-4 py-1.5 text-xs font-medium uppercase tracking-wider text-shell-ink transition hover:bg-shell-panel active:translate-y-[1px]"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}

      {children && <div className="mt-4 w-full max-w-sm">{children}</div>}
    </div>
  );
}
