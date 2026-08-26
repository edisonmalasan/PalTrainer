import { useEffect, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { ViewShell } from "../../shared/components/ViewShell";
import type { AppSettings, CommandError, SaveSummary } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const LEVEL_SAV_FILE_NAME = "level.sav";

// Mirrors PalworldSaveTools: a single file picker filtered to *.sav, titled
// "Select Level.sav". The *.sav filter is what makes Level.sav visible in the
// world folder — a directory-only picker hides every file.
async function pickLevelSavFile(defaultPath?: string | null): Promise<string | null> {
  const selection = await open({
    directory: false,
    multiple: false,
    title: "Select Level.sav",
    filters: [{ name: "Palworld save files (*.sav)", extensions: ["sav"] }],
    defaultPath: defaultPath ?? undefined,
  });
  return typeof selection === "string" ? selection : null;
}

// The backend session expects the world save root directory; derive it from the
// picked Level.sav so users only ever interact with one file.
function toSaveRootFromLevelSav(selectedPath: string): string | null {
  const segments = selectedPath.split(/[\\/]/);
  const fileName = segments[segments.length - 1] ?? "";
  if (fileName.toLowerCase() !== LEVEL_SAV_FILE_NAME) return null;
  segments.pop();
  return segments.join("\\");
}

type SessionMessage = { kind: "ok" | "error"; text: string } | null;

export function SaveSessionView() {
  const [summary, setSummary] = useState<SaveSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [message, setMessage] = useState<SessionMessage>(null);
  const [recentPaths, setRecentPaths] = useState<readonly string[]>([]);

  async function refreshRecentPaths() {
    try {
      const settings = await invokeCommand<AppSettings>("get_settings");
      setRecentPaths(settings.recentSavePaths ?? []);
    } catch {
      // settings unavailable in tests / browser preview
    }
  }

  useEffect(() => {
    void refreshRecentPaths();
  }, []);

  // Keep recent list in sync after a successful load (backend also pushes).
  useEffect(() => {
    if (summary) void refreshRecentPaths();
  }, [summary]);

  async function loadFromSaveRoot(saveRoot: string) {
    const loadedSummary = await invokeCommand<SaveSummary>("load_save_session", {
      path: saveRoot,
    });
    setSummary(loadedSummary);
    setMessage({ kind: "ok", text: "Save loaded successfully." });
    // Optimistic recent update for instant feedback; backend is source of truth.
    setRecentPaths((prev) => {
      const next = [saveRoot, ...prev.filter((p) => p !== saveRoot)];
      return next.slice(0, 5);
    });
  }

  async function handleLoadRecent(path: string) {
    setMessage(null);
    setLoading(true);
    try {
      await loadFromSaveRoot(path);
    } catch (err: unknown) {
      const e = err as CommandError;
      setMessage({ kind: "error", text: e.message ?? "Failed to load save." });
    } finally {
      setLoading(false);
    }
  }

  function handleDroppedPath(droppedPath: string) {
    const saveRoot = toSaveRootFromLevelSav(droppedPath);
    if (!saveRoot) {
      setMessage({
        kind: "error",
        text: `Please drop ${LEVEL_SAV_FILE_NAME} — got “${droppedPath.split(/[\\/]/).pop()}”.`,
      });
      return;
    }
    void (async () => {
      setMessage(null);
      setLoading(true);
      try {
        await loadFromSaveRoot(saveRoot);
      } catch (err: unknown) {
        const e = err as CommandError;
        setMessage({ kind: "error", text: e.message ?? "Failed to load save." });
      } finally {
        setLoading(false);
      }
    })();
  }

  // Tauri desktop drop — mirrors PalworldSaveTools DropOverlay on Tools tab.
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let cancelled = false;
    (async () => {
      try {
        const { getCurrentWebviewWindow } =
          await import("@tauri-apps/api/webviewWindow");
        if (cancelled) return;
        const win = getCurrentWebviewWindow();
        unlisten = await win.onDragDropEvent((event) => {
          if (event.payload.type === "enter" || event.payload.type === "over") {
            setIsDragOver(true);
          } else if (event.payload.type === "leave") {
            setIsDragOver(false);
          } else if (event.payload.type === "drop") {
            setIsDragOver(false);
            const first = (event.payload.paths as string[])[0];
            if (first) handleDroppedPath(first);
          }
        });
      } catch {
        // Not in Tauri (browser / vitest jsdom) — fall back to HTML5 handlers below.
      }
    })();
    return () => {
      cancelled = true;
      unlisten?.();
    };
    // handleDroppedPath is stable (only uses setters + pure helper)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Single-step flow like PalworldSaveTools: pick Level.sav and the session
  // loads immediately with no intermediate confirm button.
  // Uses the most recent save as `defaultPath` so the dialog opens where the
  // user last loaded (mirrors common.get_preferred_save_path).
  async function handleLoadSave() {
    setMessage(null);
    setLoading(true);
    try {
      const defaultPath = recentPaths[0] ?? undefined;
      const selection = await pickLevelSavFile(defaultPath ?? null);
      if (!selection) {
        return;
      }
      const saveRoot = toSaveRootFromLevelSav(selection);
      if (!saveRoot) {
        setMessage({
          kind: "error",
          text: `Please select ${LEVEL_SAV_FILE_NAME} from your world save folder.`,
        });
        return;
      }
      await loadFromSaveRoot(saveRoot);
    } catch (err: unknown) {
      const e = err as CommandError;
      setMessage({ kind: "error", text: e.message ?? "Failed to load save." });
    } finally {
      setLoading(false);
    }
  }

  async function handleCloseSession() {
    setLoading(true);
    setMessage(null);
    try {
      await invokeCommand("close_save_session");
      setSummary(null);
      setMessage({ kind: "ok", text: "Save session closed." });
    } catch (err: unknown) {
      const e = err as CommandError;
      setMessage({ kind: "error", text: e.message ?? "Failed to close session." });
    } finally {
      setLoading(false);
    }
  }

  // ── Loaded-save projection straight from the backend session ────────────────
  function summaryItems(summary: SaveSummary) {
    return [
      { label: "World", value: summary.worldName || "Unknown" },
      { label: "Save type", value: summary.saveType },
      { label: "Players", value: String(summary.playerCount) },
      { label: "Level.sav size", value: `${summary.levelSavSize.toLocaleString()} bytes` },
      { label: "Save root", value: summary.saveRoot },
      {
        label: "Loaded at",
        value: new Date(summary.loadedAt * 1000).toLocaleString(),
      },
    ];
  }

  // Browser fallback for `pnpm dev` without Tauri — file name check only
  function handleBrowserDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(true);
  }
  function handleBrowserDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (!file) return;
    if (file.name.toLowerCase() !== LEVEL_SAV_FILE_NAME) {
      setMessage({
        kind: "error",
        text: `Please drop ${LEVEL_SAV_FILE_NAME} — got “${file.name}”.`,
      });
      return;
    }
    setMessage({
      kind: "error",
      text: `Browser drop cannot resolve the full Level.sav path. Pick “Load Save…” or drop the file in the desktop app.`,
    });
  }

  return (
    <ViewShell
      title="Save Session"
      subtitle="Select your world's Level.sav to inspect players, Pals, guilds, and more."
    >
      <div
        className="flex flex-col gap-6"
        onDragOver={handleBrowserDragOver}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleBrowserDrop}
      >
        {/* Load control — drop target */}
        <div
          className={[
            "relative border bg-shell-surface p-5 transition-colors",
            isDragOver ? "border-shell-accent bg-shell-accent-subtle" : "border-shell-line",
          ].join(" ")}
        >
          {isDragOver && (
            <div className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 border-2 border-dashed border-shell-accent bg-shell-accent-subtle/80 backdrop-blur-[2px]">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-shell-accent text-white shadow-sm">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                  <path d="M12 16V3" />
                  <path d="M8 7l4-4 4 4" />
                  <path d="M3 17v3h18v-3" />
                </svg>
              </div>
              <p className="text-sm font-semibold text-shell-accent">Drop Level.sav here</p>
              <p className="font-mono text-xs text-shell-muted">…\SaveGames\SteamID\WorldID\Level.sav</p>
            </div>
          )}
          <h3 className="text-base font-semibold">Load Save</h3>
          <p className="mt-2 max-w-[65ch] text-sm leading-6 text-shell-muted">
            Pick the <code className="font-mono text-xs">Level.sav</code> file inside your
            world folder (for example{" "}
            <span className="font-mono text-xs">
              …\Pal\Saved\SaveGames\&lt;SteamID&gt;\&lt;WorldID&gt;\Level.sav
            </span>
            ) — or drag & drop it here. The directory is validated and never modified without a backup.
          </p>
          <p className="mt-1 font-mono text-xs text-shell-muted">or drag & drop a Level.sav file here</p>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              id="btn-load-save"
              type="button"
              disabled={loading}
              onClick={() => void handleLoadSave()}
              className={[
                "border px-4 py-2 text-sm font-medium transition active:translate-y-[1px]",
                loading
                  ? "cursor-not-allowed border-shell-line text-shell-muted opacity-60"
                  : "border-shell-accent-solid bg-shell-accent-solid-subtle text-shell-accent hover:bg-shell-accent-subtle-hover",
              ].join(" ")}
            >
              {loading && !summary ? "Loading…" : summary ? "Load another save…" : "Load Save…"}
            </button>

            {summary && (
              <button
                id="btn-close-session"
                type="button"
                disabled={loading}
                onClick={() => void handleCloseSession()}
                className="border border-shell-line px-4 py-2 text-sm text-shell-muted transition hover:bg-shell-panel active:translate-y-[1px] disabled:opacity-60"
              >
                {loading ? "Closing…" : "Close Session"}
              </button>
            )}
          </div>

          {recentPaths.length > 0 && (
            <div className="mt-4 border-t border-shell-line pt-3">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">Recent saves</p>
              <ul className="mt-2 grid gap-1.5">
                {recentPaths.map((p) => (
                  <li key={p}>
                    <button
                      type="button"
                      disabled={loading}
                      onClick={() => void handleLoadRecent(p)}
                      className="flex w-full items-center gap-2 truncate text-left font-mono text-xs text-shell-muted transition hover:text-shell-ink disabled:opacity-50"
                      title={p}
                    >
                      <span className="h-1 w-1 shrink-0 rounded-full bg-shell-accent" aria-hidden="true" />
                      <span className="truncate">{p}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {message && (
            <p
              role="status"
              className={[
                "mt-4 border px-3 py-2 text-sm",
                message.kind === "ok"
                  ? "border-shell-accent/40 bg-shell-accent-subtle text-shell-accent"
                  : "border-shell-destructive/40 bg-shell-destructive-subtle text-shell-destructive",
              ].join(" ")}
            >
              {message.text}
            </p>
          )}

          {summary && (
            <dl
              className="mt-5 grid grid-cols-1 gap-3 border-t border-shell-line pt-5 sm:grid-cols-2 lg:grid-cols-3"
              aria-label="Loaded save summary"
            >
              {summaryItems(summary).map((item) => (
                <div key={item.label} className="bg-shell-panel px-3 py-2">
                  <dt className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                    {item.label}
                  </dt>
                  <dd
                    className={[
                      "mt-1 break-all text-sm text-shell-ink",
                      item.label === "Save root" ? "font-mono text-xs" : "",
                    ].join(" ")}
                  >
                    {item.value}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        {/* Safety notes */}
        <div className="border-t border-shell-line pt-4">
          <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
            Safety guarantees
          </p>
          <ul className="mt-3 flex flex-col gap-2 text-sm text-shell-muted">
            {[
              "Path is canonicalized and validated before any read operation.",
              "Loaded data stays read-only until an explicit write command is used.",
              "A backup is created automatically before any write operations.",
              "Stale save detection prevents overwriting files modified externally.",
            ].map((note) => (
              <li key={note} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-shell-accent" />
                {note}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </ViewShell>
  );
}
