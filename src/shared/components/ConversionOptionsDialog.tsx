//! Fixed-width (380px) confirmation dialog for conversion options. Shown
//! after a file is picked, before the conversion command runs; keeps the
//! options context next to the picked file instead of scattered inputs.

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

interface ConversionOptionsDialogProps {
  readonly open: boolean;
  readonly title: string;
  readonly pickedFileLabel?: string | null;
  readonly description?: string;
  readonly confirmLabel?: string;
  readonly busy?: boolean;
  readonly onConfirm: () => void;
  readonly onClose: () => void;
  readonly children?: ReactNode;
}

export function ConversionOptionsDialog({
  open,
  title,
  pickedFileLabel,
  description,
  confirmLabel = "Run Conversion",
  busy = false,
  onConfirm,
  onClose,
  children,
}: ConversionOptionsDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) {
        event.preventDefault();
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, busy, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="conversion-options-title"
    >
      {/* Fixed 380px per the tools UX contract. */}
      <div
        ref={dialogRef}
        data-testid="conversion-options-card"
        className="w-[380px] rounded-[2.5rem] border border-shell-line bg-shell-surface p-6 shadow-2xl animate-slide-up"
      >
        <h3
          id="conversion-options-title"
          className="text-sm font-semibold tracking-tight text-shell-ink"
        >
          {title}
        </h3>

        {pickedFileLabel && (
          <p
            className="mt-2 truncate rounded-xl border border-shell-line bg-shell-panel px-3 py-2 font-mono text-[11px] text-shell-ink"
            title={pickedFileLabel}
          >
            {pickedFileLabel}
          </p>
        )}

        {description && <p className="mt-2 text-xs text-shell-muted">{description}</p>}

        {children && <div className="mt-4 space-y-3">{children}</div>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-xl border border-shell-line bg-shell-panel px-4 py-1.5 text-xs font-medium text-shell-ink hover:bg-shell-surface disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className="rounded-xl bg-shell-accent-solid px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white hover:opacity-90 disabled:opacity-50"
          >
            {busy ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
