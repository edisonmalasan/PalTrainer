import { useEffect, useState } from "react";

interface DestructiveConfirmModalProps {
  readonly isOpen: boolean;
  readonly title: string;
  readonly entityLabel: string;
  readonly expectedConfirmationText?: string;
  readonly warningMessage: string;
  readonly committing: boolean;
  readonly onCancel: () => void;
  readonly onConfirm: () => Promise<void>;
}

export function DestructiveConfirmModal({
  isOpen,
  title,
  entityLabel,
  expectedConfirmationText = "DELETE",
  warningMessage,
  committing,
  onCancel,
  onConfirm,
}: DestructiveConfirmModalProps) {
  const [typedValue, setTypedValue] = useState("");

  const isMatch = typedValue.trim().toUpperCase() === expectedConfirmationText.toUpperCase();

  useEffect(() => {
    if (!isOpen) {
      setTypedValue("");
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !committing) {
        e.preventDefault();
        onCancel();
      } else if (e.key === "Enter" && isMatch && !committing) {
        e.preventDefault();
        void onConfirm();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isMatch, committing, onCancel, onConfirm]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4 backdrop-blur-sm animate-fade-in"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="destructive-modal-title"
      aria-describedby="destructive-modal-desc"
    >
      <div className="flex max-h-[90vh] w-full max-w-md flex-col border border-shell-destructive/40 bg-shell-surface shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="border-b border-shell-destructive/40 bg-shell-destructive-subtle px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-shell-destructive-solid font-mono text-xs font-bold text-white">
              !
            </span>
            <div>
              <h3
                id="destructive-modal-title"
                className="text-base font-semibold tracking-tight text-shell-destructive"
              >
                {title}
              </h3>
              <p className="font-mono text-[11px] text-shell-destructive truncate">{entityLabel}</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 text-xs">
          <p id="destructive-modal-desc" className="leading-relaxed text-shell-ink">
            {warningMessage}
          </p>

          <div className="border-l-2 border-shell-destructive bg-shell-destructive-subtle p-3 text-shell-destructive space-y-1">
            <p className="font-semibold uppercase tracking-wide text-[10px]">
              Safety Guarantee
            </p>
            <p className="opacity-90">
              An automatic snapshot backup will be created in your <code className="font-mono">Backups/</code> folder prior to executing this modification.
            </p>
          </div>

          <div className="space-y-1.5 pt-2">
            <label
              htmlFor="destructive-confirm-input"
              className="block font-medium text-shell-muted"
            >
              Type <strong className="font-mono text-shell-destructive">{expectedConfirmationText}</strong> to confirm:
            </label>
            <input
              id="destructive-confirm-input"
              type="text"
              value={typedValue}
              onChange={(e) => setTypedValue(e.target.value)}
              placeholder={expectedConfirmationText}
              autoFocus
              className="w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm text-shell-ink focus:border-shell-destructive focus:outline-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-shell-line bg-shell-panel px-5 py-3">
          <button
            type="button"
            disabled={committing}
            onClick={onCancel}
            className="border border-shell-line bg-shell-surface px-3.5 py-1.5 text-xs font-medium text-shell-ink hover:bg-shell-panel active:translate-y-[1px]"
          >
            Cancel (Esc)
          </button>
          <button
            type="button"
            disabled={!isMatch || committing}
            onClick={() => void onConfirm()}
            className="border border-shell-destructive-solid bg-shell-destructive-solid px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white transition hover:bg-shell-destructive-solid-hover active:translate-y-[1px] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {committing ? "Executing..." : "Confirm & Destroy"}
          </button>
        </div>
      </div>
    </div>
  );
}
