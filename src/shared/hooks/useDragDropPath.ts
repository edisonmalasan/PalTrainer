//! Drag-and-drop path tracking for the tools workbench. Uses the Tauri
//! webview drag-drop event stream so dropped files arrive as real filesystem
//! paths (web `dataTransfer` hides paths in a desktop webview). Falls back
//! to an inert state outside the Tauri runtime so tests render safely.

import { useCallback, useEffect, useRef, useState } from "react";

export interface DragDropPathState {
  /** True while a file is hovered over the window. */
  readonly dragActive: boolean;
  /** Last dropped filesystem path (null until a drop happens). */
  readonly droppedPath: string | null;
  /** Consumes the current dropped path (clears it). */
  consumeDroppedPath: () => void;
}

type UnlistenFn = () => void;

/// Subscribes to native drag events. `isTauriRuntime` is injectable for tests.
export function useDragDropPath(
  isTauriRuntime: () => boolean = tauriRuntimeDefault,
): DragDropPathState {
  const [dragActive, setDragActive] = useState(false);
  const [droppedPath, setDroppedPath] = useState<string | null>(null);
  const unlistenRef = useRef<UnlistenFn | null>(null);

  const consumeDroppedPath = useCallback(() => setDroppedPath(null), []);

  useEffect(() => {
    if (!isTauriRuntime()) return;

    let cancelled = false;

    void (async () => {
      try {
        const { getCurrentWebview } = await import("@tauri-apps/api/webview");
        const unlisten = await getCurrentWebview().onDragDropEvent((event) => {
          if (cancelled) return;
          if (event.payload.type === "over") {
            setDragActive(true);
          } else if (event.payload.type === "drop") {
            setDragActive(false);
            const first = event.payload.paths[0];
            if (first) setDroppedPath(first);
          } else {
            setDragActive(false);
          }
        });
        if (cancelled) {
          unlisten();
        } else {
          unlistenRef.current = unlisten;
        }
      } catch {
        // Non-Tauri or event API unavailable: stay inert.
      }
    })();

    return () => {
      cancelled = true;
      unlistenRef.current?.();
      unlistenRef.current = null;
    };
  }, [isTauriRuntime]);

  return { dragActive, droppedPath, consumeDroppedPath };
}

function tauriRuntimeDefault(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}
