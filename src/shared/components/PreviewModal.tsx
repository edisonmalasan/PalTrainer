import { useEffect, useRef } from "react";
import type { MutationPreview } from "../types/contracts";

interface PreviewModalProps {
  readonly preview: MutationPreview | null;
  readonly committing: boolean;
  readonly onCancel: () => void;
  readonly onConfirm: () => Promise<void>;
}

export function PreviewModal({
  preview,
  committing,
  onCancel,
  onConfirm,
}: PreviewModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcut listener: Escape to close, Ctrl/Cmd + Enter to commit
  useEffect(() => {
    if (!preview) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !committing) {
        e.preventDefault();
        onCancel();
      } else if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && !committing) {
        e.preventDefault();
        void onConfirm();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [preview, committing, onCancel, onConfirm]);

  if (!preview) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="preview-modal-title"
      ref={modalRef}
    >
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col border border-shell-line bg-shell-surface shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="border-b border-shell-line px-5 py-4">
          <div className="flex items-center justify-between">
            <h3
              id="preview-modal-title"
              className="text-base font-semibold tracking-tight text-shell-ink"
            >
              Review Changes —{" "}
              <span className="font-mono text-sm uppercase text-shell-accent">
                {preview.operation}
              </span>
            </h3>
            <span
              className={[
                "border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide",
                preview.isSafe
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700"
                  : "border-shell-destructive/20 bg-shell-destructive-subtle text-shell-destructive",
              ].join(" ")}
            >
              {preview.isSafe ? "Safe with backup" : "Requires attention"}
            </span>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 text-sm">
          {/* Warnings */}
          {preview.warnings.length > 0 && (
            <div className="mb-4 border-l-4 border-shell-warning bg-shell-warning-subtle p-3 text-shell-warning">
              <p className="font-mono text-xs font-semibold uppercase">Warnings</p>
              <ul className="mt-1 list-disc pl-4 text-xs">
                {preview.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Entities to modify */}
          {preview.entitiesToModify.length > 0 && (
            <div className="mb-4">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                Entities to Modify ({preview.entitiesToModify.length})
              </p>
              <div className="mt-2 grid gap-2">
                {preview.entitiesToModify.map((e) => (
                  <div
                    key={`${e.entityType}-${e.entityId}`}
                    className="border border-shell-line bg-shell-panel p-3"
                  >
                    <p className="font-semibold text-xs text-shell-ink">{e.label}</p>
                    <p className="mt-1 font-mono text-xs text-shell-muted">
                      {e.changeDescription}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entities to delete */}
          {preview.entitiesToDelete.length > 0 && (
            <div className="mb-4">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-destructive">
                Entities to Delete ({preview.entitiesToDelete.length})
              </p>
              <div className="mt-2 grid gap-2">
                {preview.entitiesToDelete.map((e) => (
                  <div
                    key={`${e.entityType}-${e.entityId}`}
                    className="border border-shell-destructive/40 bg-shell-destructive-subtle p-3 text-shell-destructive"
                  >
                    <p className="font-semibold text-xs">{e.label}</p>
                    <p className="mt-1 font-mono text-xs opacity-80">{e.changeDescription}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Files */}
          <div className="border-t border-shell-line pt-3 font-mono text-[11px] text-shell-muted">
            <p className="uppercase">Files affected:</p>
            <ul className="mt-1 list-disc pl-4">
              {preview.filesToModify.map((f) => (
                <li key={f}>Modify: {f.split(/[\\/]/).pop()}</li>
              ))}
              {preview.filesToDelete.map((f) => (
                <li key={f} className="text-shell-destructive">
                  Delete: {f.split(/[\\/]/).pop()}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-shell-line bg-shell-panel px-5 py-3">
          <span className="text-xs text-shell-muted">Auto-backup created before apply.</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={committing}
              onClick={onCancel}
              className="border border-shell-line bg-shell-surface px-3.5 py-1.5 text-xs font-medium text-shell-ink transition hover:bg-shell-panel active:translate-y-[1px]"
            >
              Cancel (Esc)
            </button>
            <button
              type="button"
              disabled={committing}
              onClick={() => void onConfirm()}
              className="border border-shell-accent-solid bg-shell-accent-solid px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white transition hover:bg-shell-accent-solid-hover active:translate-y-[1px] disabled:opacity-60"
            >
              {committing ? "Applying..." : "Confirm & Commit (Ctrl+Enter)"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
