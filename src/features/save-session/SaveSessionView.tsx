import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { ViewShell } from "../../shared/components/ViewShell";
import type { CommandError, SaveSummary } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const LEVEL_SAV_FILE_NAME = "level.sav";

// Mirrors PalworldSaveTools: a single file picker filtered to *.sav, titled
// "Select Level.sav". The *.sav filter is what makes Level.sav visible in the
// world folder — a directory-only picker hides every file.
async function pickLevelSavFile(): Promise<string | null> {
  const selection = await open({
    directory: false,
    multiple: false,
    title: "Select Level.sav",
    filters: [{ name: "Palworld save files (*.sav)", extensions: ["sav"] }],
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
  const [message, setMessage] = useState<SessionMessage>(null);

  // Single-step flow like PalworldSaveTools: pick Level.sav and the session
  // loads immediately with no intermediate confirm button.
  async function handleLoadSave() {
    setMessage(null);
    setLoading(true);
    try {
      const selection = await pickLevelSavFile();
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
      const loadedSummary = await invokeCommand<SaveSummary>("load_save_session", {
        path: saveRoot,
      });
      setSummary(loadedSummary);
      setMessage({ kind: "ok", text: "Save loaded successfully." });
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

  return (
    <ViewShell
      title="Save Session"
      subtitle="Select your world's Level.sav to inspect players, Pals, guilds, and more."
    >
      <div className="flex flex-col gap-6">
        {/* Load control */}
        <div className="border border-shell-line bg-shell-surface p-5">
          <h3 className="text-base font-semibold">Load Save</h3>
          <p className="mt-2 max-w-[65ch] text-sm leading-6 text-shell-muted">
            Pick the <code className="font-mono text-xs">Level.sav</code> file inside your
            world folder (for example{" "}
            <span className="font-mono text-xs">
              …\Pal\Saved\SaveGames\&lt;SteamID&gt;\&lt;WorldID&gt;\Level.sav
            </span>
            ). The whole directory is validated and never modified without a backup.
          </p>

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
                  : "border-shell-accent bg-shell-accent-subtle text-shell-accent hover:bg-shell-accent-subtle-hover",
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
