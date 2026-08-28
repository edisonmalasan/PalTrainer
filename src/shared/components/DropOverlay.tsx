//! Drag-drop + click-to-browse target used by every tools card that needs a
//! filesystem path. Renders children inside a dashed drop zone; when a native
//! drag is active an overlay highlights the zone.

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useDragDropPath } from "../hooks/useDragDropPath";

interface DropOverlayProps {
  readonly label: string;
  readonly hint?: string;
  readonly selectedLabel?: string | null;
  readonly onPickedPath: (path: string) => void;
  readonly onBrowse: () => void;
  readonly disabled?: boolean;
  readonly children?: ReactNode;
}

export function DropOverlay({
  label,
  hint,
  selectedLabel,
  onPickedPath,
  onBrowse,
  disabled = false,
  children,
}: DropOverlayProps) {
  const { dragActive, droppedPath, consumeDroppedPath } = useDragDropPath();

  useEffect(() => {
    if (droppedPath) {
      onPickedPath(droppedPath);
      consumeDroppedPath();
    }
  }, [droppedPath, onPickedPath, consumeDroppedPath]);

  return (
    <div
      className={[
        "relative rounded-2xl border-2 border-dashed p-4 text-center transition",
        dragActive
          ? "border-shell-accent bg-shell-accent/5"
          : "border-shell-line bg-shell-panel hover:border-shell-accent/50",
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
      ].join(" ")}
      onClick={() => {
        if (!disabled) onBrowse();
      }}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={`${label} — click to browse or drop a file`}
      onKeyDown={(event) => {
        if (!disabled && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          onBrowse();
        }
      }}
      data-drag-active={dragActive ? "true" : "false"}
    >
      {dragActive && (
        <div
          data-testid="drop-overlay-active"
          className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-2xl bg-shell-accent/10 text-xs font-semibold uppercase tracking-wider text-shell-accent"
        >
          Drop to select
        </div>
      )}
      <p className="text-xs font-semibold text-shell-ink">{label}</p>
      {hint && <p className="mt-0.5 text-[11px] text-shell-muted">{hint}</p>}
      {selectedLabel && (
        <p
          className="mt-2 truncate rounded-lg border border-shell-line bg-shell-surface px-2 py-1 font-mono text-[11px] text-shell-ink"
          title={selectedLabel}
        >
          {selectedLabel}
        </p>
      )}
      {children}
    </div>
  );
}
