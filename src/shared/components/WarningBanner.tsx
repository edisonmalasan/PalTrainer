import type { ReactNode } from "react";

export type WarningSeverity = "info" | "warning" | "destructive";

interface WarningBannerProps {
  readonly severity?: WarningSeverity;
  readonly badge?: string;
  readonly title: string;
  readonly description?: string;
  readonly action?: {
    readonly label: string;
    readonly onClick: () => void;
  };
  readonly children?: ReactNode;
  readonly className?: string;
}

const SEVERITY_STYLES: Record<
  WarningSeverity,
  {
    readonly border: string;
    readonly bg: string;
    readonly text: string;
    readonly badgeBg: string;
    readonly badgeText: string;
    readonly iconColor: string;
  }
> = {
  info: {
    border: "border-sky-500",
    bg: "bg-sky-50/80",
    text: "text-sky-950",
    badgeBg: "bg-sky-100 text-sky-800 border-sky-300",
    badgeText: "text-sky-800",
    iconColor: "text-sky-600",
  },
  warning: {
    border: "border-shell-warning",
    bg: "bg-shell-warning-subtle",
    text: "text-shell-warning",
    badgeBg: "bg-shell-warning-subtle text-shell-warning border-shell-warning/40",
    badgeText: "text-shell-warning",
    iconColor: "text-shell-warning",
  },
  destructive: {
    border: "border-shell-destructive",
    bg: "bg-shell-destructive-subtle",
    text: "text-shell-destructive",
    badgeBg: "bg-shell-destructive-subtle text-shell-destructive border-shell-destructive/40",
    badgeText: "text-shell-destructive",
    iconColor: "text-shell-destructive",
  },
};

export function WarningBanner({
  severity = "warning",
  badge,
  title,
  description,
  action,
  children,
  className = "",
}: WarningBannerProps) {
  const styles = SEVERITY_STYLES[severity];
  const defaultBadge =
    badge ??
    (severity === "destructive"
      ? "Destructive Action"
      : severity === "warning"
        ? "Safety Advisory"
        : "Notice");

  return (
    <div
      role="alert"
      className={[
        "flex flex-col gap-2 border-l-4 p-4 shadow-2xs transition-all",
        styles.border,
        styles.bg,
        styles.text,
        className,
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className={["shrink-0", styles.iconColor].join(" ")}
            aria-hidden="true"
          >
            {severity === "destructive" || severity === "warning" ? (
              <>
                <path
                  d="M8 1.5L14.5 13H1.5L8 1.5Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <line
                  x1="8"
                  y1="6"
                  x2="8"
                  y2="9.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
                <circle cx="8" cy="11.5" r="0.75" fill="currentColor" />
              </>
            ) : (
              <>
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" />
                <line
                  x1="8"
                  y1="7.5"
                  x2="8"
                  y2="11.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
                <circle cx="8" cy="5" r="0.75" fill="currentColor" />
              </>
            )}
          </svg>
          <span
            className={[
              "border px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider",
              styles.badgeBg,
            ].join(" ")}
          >
            {defaultBadge}
          </span>
          <span className="text-xs font-semibold tracking-tight">{title}</span>
        </div>

        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="shrink-0 border border-current bg-shell-surface px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider transition hover:bg-opacity-90 active:translate-y-[1px]"
          >
            {action.label}
          </button>
        )}
      </div>

      {description && (
        <p className="text-xs leading-relaxed opacity-90 pl-6">{description}</p>
      )}

      {children && <div className="pl-6 pt-1">{children}</div>}
    </div>
  );
}
