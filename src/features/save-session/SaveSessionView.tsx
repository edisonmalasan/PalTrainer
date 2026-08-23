import { useCallback, useState } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { AppSettings, CommandError } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function SaveSessionView() {
  const state = useAsync(
    useCallback(() => invokeCommand<AppSettings>("get_settings"), []),
    [],
  );

  const [savePath, setSavePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  async function handleLoad() {
    if (!savePath.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      await invokeCommand("load_save_session", { savePath: savePath.trim() });
      setMessage({ kind: "ok", text: "Save loaded successfully." });
    } catch (err: unknown) {
      const e = err as CommandError;
      setMessage({ kind: "error", text: e.message ?? "Failed to load save." });
    } finally {
      setLoading(false);
    }
  }

  async function handleClose() {
    setLoading(true);
    setMessage(null);
    try {
      await invokeCommand("close_save_session");
      setMessage({ kind: "ok", text: "Save session closed." });
    } catch (err: unknown) {
      const e = err as CommandError;
      setMessage({ kind: "error", text: e.message ?? "Failed to close session." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <ViewShell
      title="Save Session"
      subtitle="Load a Palworld save directory to inspect players, Pals, guilds, and more."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-6">
        {/* Load form */}
        <div className="border border-shell-line bg-white p-5">
          <h3 className="text-base font-semibold">Load Save Directory</h3>
          <p className="mt-2 max-w-[65ch] text-sm leading-6 text-shell-muted">
            Point to the folder containing your{" "}
            <code className="font-mono text-xs">Level.sav</code> and player save
            files. The path is validated and never modified without a backup.
          </p>

          <div className="mt-5 grid gap-2">
            <label className="grid gap-2 text-sm" htmlFor="save-path-input">
              <span className="font-medium">Save path</span>
              <input
                id="save-path-input"
                type="text"
                value={savePath}
                onChange={(e) => setSavePath(e.target.value)}
                placeholder="C:\Users\…\Pal\Saved\SaveGames\…"
                className="border border-shell-line bg-white px-3 py-2 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-shell-accent"
              />
            </label>
          </div>

          {message && (
            <p
              className={[
                "mt-4 px-3 py-2 text-sm",
                message.kind === "ok"
                  ? "border border-shell-accent bg-[#edf5f2] text-shell-accent"
                  : "border border-red-200 bg-red-50 text-red-800",
              ].join(" ")}
            >
              {message.text}
            </p>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              id="btn-load-save"
              type="button"
              disabled={loading || !savePath.trim()}
              onClick={() => void handleLoad()}
              className={[
                "border px-4 py-2 text-sm font-medium transition active:translate-y-[1px]",
                loading || !savePath.trim()
                  ? "cursor-not-allowed border-shell-line text-shell-muted opacity-60"
                  : "border-shell-accent bg-[#edf5f2] text-shell-accent hover:bg-[#d9ede7]",
              ].join(" ")}
            >
              {loading ? "Loading…" : "Load save"}
            </button>

            <button
              id="btn-close-session"
              type="button"
              disabled={loading}
              onClick={() => void handleClose()}
              className="border border-shell-line px-4 py-2 text-sm text-shell-muted transition hover:bg-shell-panel active:translate-y-[1px] disabled:opacity-60"
            >
              Close session
            </button>
          </div>
        </div>

        {/* Safety notes */}
        <div className="border-t border-shell-line pt-4">
          <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
            Safety guarantees
          </p>
          <ul className="mt-3 flex flex-col gap-2 text-sm text-shell-muted">
            {[
              "Path is canonicalized and validated before any read operation.",
              "All data is read-only in Phase 4 — no write operations are exposed.",
              "A backup is created automatically before any future write operations.",
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
