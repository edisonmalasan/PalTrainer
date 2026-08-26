// Shared async view wrapper: loading skeleton, error banner, and ready slot.
import type { ReactNode } from "react";

export function ViewShell({
  title,
  subtitle,
  description,
  status = "ok",
  errorMessage,
  actionSlot,
  children,
}: {
  readonly title: string;
  readonly subtitle?: string;
  readonly description?: string;
  readonly status?: "idle" | "loading" | "ok" | "error";
  readonly errorMessage?: string;
  readonly actionSlot?: ReactNode;
  readonly children: ReactNode;
}) {
  const displaySubtitle = description ?? subtitle;

  return (
    <section className="flex flex-col gap-5 animate-fade-in">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-shell-ink">{title}</h2>
          {displaySubtitle && (
            <p className="mt-1 text-sm text-shell-muted">{displaySubtitle}</p>
          )}
        </div>
        {actionSlot && <div className="flex items-center gap-2">{actionSlot}</div>}
      </div>

      {status === "loading" || status === "idle" ? (
        <ViewSkeleton />
      ) : status === "error" ? (
        <ErrorBanner message={errorMessage ?? "Unexpected error occurred."} />
      ) : (
        <div className="animate-slide-up">{children}</div>
      )}
    </section>
  );
}

function ViewSkeleton() {
  return (
    <div className="flex flex-col gap-3" aria-busy="true" aria-label="Loading content">
      <div className="h-8 w-48 animate-pulse bg-shell-line/80" />
      <div className="h-[1px] w-full bg-shell-line" />
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="h-10 w-full animate-pulse bg-shell-panel"
          style={{ opacity: 1 - i * 0.14 }}
        />
      ))}
    </div>
  );
}

function ErrorBanner({ message }: { readonly message: string }) {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 border border-shell-destructive/40 bg-shell-destructive-subtle px-4 py-3 text-sm text-shell-destructive"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        className="shrink-0 text-shell-destructive"
        aria-hidden="true"
      >
        <path
          d="M8 1.5L14.5 13H1.5L8 1.5Z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <line x1="8" y1="6" x2="8" y2="9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="8" cy="11.5" r="0.75" fill="currentColor" />
      </svg>
      <div>
        <span className="font-mono font-semibold uppercase tracking-wide text-xs">Error — </span>
        <span>{message}</span>
      </div>
    </div>
  );
}
