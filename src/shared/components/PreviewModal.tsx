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
  if (!preview) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col border border-shell-line bg-white shadow-xl">
        {/* Header */}
        <div className="border-b border-shell-line px-5 py-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Review Changes — <span className="font-mono text-sm uppercase text-shell-accent">{preview.operation}</span>
            </h3>
            <span
              className={[
                "rounded-sm px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide",
                preview.isSafe
                  ? "bg-[#edf5f2] text-shell-accent"
                  : "bg-red-50 text-red-700",
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
            <div className="mb-4 border-l-2 border-amber-400 bg-amber-50 p-3 text-amber-900">
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
                  <div key={`${e.entityType}-${e.entityId}`} className="border border-shell-line bg-shell-panel p-3">
                    <p className="font-semibold text-shell-ink">{e.label}</p>
                    <p className="mt-1 font-mono text-xs text-shell-muted">{e.changeDescription}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entities to delete */}
          {preview.entitiesToDelete.length > 0 && (
            <div className="mb-4">
              <p className="font-mono text-[10px] uppercase tracking-wide text-red-600">
                Entities to Delete ({preview.entitiesToDelete.length})
              </p>
              <div className="mt-2 grid gap-2">
                {preview.entitiesToDelete.map((e) => (
                  <div key={`${e.entityType}-${e.entityId}`} className="border border-red-200 bg-red-50 p-3 text-red-900">
                    <p className="font-semibold">{e.label}</p>
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
                <li key={f} className="text-red-600">Delete: {f.split(/[\\/]/).pop()}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-shell-line bg-shell-panel px-5 py-3">
          <span className="text-xs text-shell-muted">Auto-backup created before apply.</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={committing}
              onClick={onCancel}
              className="border border-shell-line bg-white px-3 py-1.5 text-xs font-medium text-shell-muted transition hover:bg-shell-panel active:translate-y-[1px]"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={committing}
              onClick={() => void onConfirm()}
              className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent transition hover:bg-[#d9ede7] active:translate-y-[1px] disabled:opacity-60"
            >
              {committing ? "Applying..." : "Confirm & Commit"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
