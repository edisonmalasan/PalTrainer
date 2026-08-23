// Shared async view wrapper: loading skeleton, error banner, and ready slot.
import type { ReactNode } from "react";

export function ViewShell({
  title,
  subtitle,
  status,
  errorMessage,
  children,
}: {
  readonly title: string;
  readonly subtitle?: string;
  readonly status: "idle" | "loading" | "ok" | "error";
  readonly errorMessage?: string;
  readonly children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-5">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm text-shell-muted">{subtitle}</p>
        )}
      </div>

      {status === "loading" || status === "idle" ? (
        <ViewSkeleton />
      ) : status === "error" ? (
        <ErrorBanner message={errorMessage ?? "Unexpected error."} />
      ) : (
        children
      )}
    </section>
  );
}

function ViewSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="h-8 w-48 animate-pulse bg-shell-line" />
      <div className="h-[2px] w-full animate-pulse bg-shell-line" />
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          // eslint-disable-next-line react/no-array-index-key
          key={i}
          className="h-9 w-full animate-pulse bg-shell-panel"
          style={{ opacity: 1 - i * 0.12 }}
        />
      ))}
    </div>
  );
}

function ErrorBanner({ message }: { readonly message: string }) {
  return (
    <div className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      <span className="font-mono font-semibold uppercase tracking-wide">Error — </span>
      {message}
    </div>
  );
}
