import { useEffect, useMemo, useState } from "react";
import type {
  AppInfo,
  AppLogEntry,
  AppSettings,
  CommandError,
  FeatureFlag,
} from "../shared/types/contracts";
import { invokeCommand } from "../shared/utils/command";
import { ErrorBoundary } from "./ErrorBoundary";
import { appRoutes } from "./routes";

const defaultSettings: AppSettings = {
  theme: "system",
  language: "en",
  showAdvancedTools: false,
};

const plannedMilestones = [
  "Pure Rust parser target with temporary hybrid bridge allowed only early.",
  "Versioned compressed successor exports plus legacy import support.",
  "Raw JSON editor defaults to read-only and gates edits behind backup, diff, and validation.",
  "Unsupported save versions preserve unknown bytes by the sacred roundtrip rule.",
];

export function App() {
  return (
    <ErrorBoundary>
      <Workbench />
    </ErrorBoundary>
  );
}

function Workbench() {
  const [activeRoute, setActiveRoute] = useState("settings");
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [featureFlags, setFeatureFlags] = useState<readonly FeatureFlag[]>([]);
  const [logs, setLogs] = useState<readonly AppLogEntry[]>([]);
  const [error, setError] = useState<CommandError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadShell() {
      try {
        const [info, loadedSettings, flags] = await Promise.all([
          invokeCommand<AppInfo>("get_app_info"),
          invokeCommand<AppSettings>("get_settings"),
          invokeCommand<readonly FeatureFlag[]>("get_feature_flags"),
        ]);

        if (!cancelled) {
          setAppInfo(info);
          setSettings(loadedSettings);
          setFeatureFlags(flags);
          setLogs([
            {
              level: "info",
              message: "Phase 1 shell initialized. Save editing is not enabled yet.",
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught as CommandError);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadShell();

    return () => {
      cancelled = true;
    };
  }, []);

  const enabledFlags = useMemo(
    () => featureFlags.filter((flag) => flag.enabled),
    [featureFlags],
  );

  async function updateSettings(nextSettings: AppSettings) {
    setSettings(nextSettings);
    setError(null);

    try {
      const saved = await invokeCommand<AppSettings>("save_settings", {
        settings: nextSettings,
      });
      setSettings(saved);
      setLogs((current) => [
        {
          level: "info",
          message: "Settings saved through the Tauri command bridge.",
          timestamp: new Date().toISOString(),
        },
        ...current,
      ]);
    } catch (caught) {
      setError(caught as CommandError);
    }
  }

  return (
    <main className="min-h-[100dvh] bg-shell-panel text-shell-ink">
      <div className="mx-auto grid min-h-[100dvh] max-w-[1440px] grid-cols-1 lg:grid-cols-[260px_1fr]">
        <aside className="border-b border-shell-line bg-shell-surface px-5 py-5 lg:border-b-0 lg:border-r">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-shell-accent">
              PalTrainer
            </p>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight">
              Save Workbench
            </h1>
            <p className="mt-3 text-sm leading-6 text-shell-muted">
              Phase 1 scaffold for a safer Palworld save editor.
            </p>
          </div>

          <nav className="mt-8 grid gap-1" aria-label="PalTrainer sections">
            {appRoutes.map((route) => (
              <button
                key={route.id}
                type="button"
                disabled={!route.enabled}
                onClick={() => setActiveRoute(route.id)}
                className={[
                  "flex items-center justify-between border px-3 py-2 text-left text-sm transition",
                  route.id === activeRoute
                    ? "border-shell-accent bg-[#edf5f2] text-shell-ink"
                    : "border-transparent text-shell-muted hover:border-shell-line hover:bg-shell-panel",
                  route.enabled
                    ? "active:translate-y-[1px]"
                    : "cursor-not-allowed opacity-55",
                ].join(" ")}
              >
                <span>{route.label}</span>
                <span className="font-mono text-[11px]">{route.phase}</span>
              </button>
            ))}
          </nav>
        </aside>

        <section className="grid grid-rows-[auto_1fr]">
          <header className="border-b border-shell-line bg-shell-surface px-6 py-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-shell-muted">
                  No Save Loaded
                </p>
                <h2 className="mt-1 text-xl font-semibold tracking-tight">
                  Foundation mode
                </h2>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-shell-muted md:grid-cols-3">
                <Metric label="App" value={appInfo?.version ?? "loading"} />
                <Metric label="Flags" value={`${enabledFlags.length} enabled`} />
                <Metric label="State" value={loading ? "loading" : "ready"} />
              </div>
            </div>
          </header>

          <div className="grid gap-6 px-6 py-6 xl:grid-cols-[1fr_340px]">
            <section className="min-w-0">
              {loading ? (
                <LoadingState />
              ) : (
                <SettingsPanel
                  settings={settings}
                  error={error}
                  onChange={updateSettings}
                />
              )}

              <section className="mt-6 border-t border-shell-line pt-6">
                <h3 className="text-base font-semibold">Phase 1 scope</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {plannedMilestones.map((milestone) => (
                    <div
                      key={milestone}
                      className="border border-shell-line bg-white p-4"
                    >
                      <p className="text-sm leading-6 text-shell-muted">{milestone}</p>
                    </div>
                  ))}
                </div>
              </section>
            </section>

            <aside className="border-t border-shell-line pt-6 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
              <h3 className="text-base font-semibold">Progress Log</h3>
              <div className="mt-4 grid gap-3">
                {logs.length === 0 ? (
                  <p className="border border-dashed border-shell-line p-4 text-sm text-shell-muted">
                    No command activity yet.
                  </p>
                ) : (
                  logs.map((entry) => (
                    <article
                      key={`${entry.timestamp}-${entry.message}`}
                      className="border-l-2 border-shell-accent pl-3"
                    >
                      <p className="font-mono text-[11px] uppercase text-shell-muted">
                        {entry.level} / {new Date(entry.timestamp).toLocaleTimeString()}
                      </p>
                      <p className="mt-1 text-sm leading-6">{entry.message}</p>
                    </article>
                  ))
                )}
              </div>

              <h3 className="mt-8 text-base font-semibold">Feature Flags</h3>
              <div className="mt-4 grid gap-3">
                {featureFlags.map((flag) => (
                  <article
                    key={flag.id}
                    className="border border-shell-line bg-white p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium">{flag.label}</p>
                      <span className="font-mono text-[11px] uppercase text-shell-muted">
                        {flag.enabled ? "enabled" : "locked"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-shell-muted">
                      {flag.description}
                    </p>
                  </article>
                ))}
              </div>
            </aside>
          </div>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div className="border border-shell-line bg-white px-3 py-2">
      <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
        {label}
      </p>
      <p className="mt-1 font-mono text-xs text-shell-ink">{value}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <section className="border border-shell-line bg-white p-5">
      <div className="h-4 w-40 animate-pulse bg-shell-line" />
      <div className="mt-5 grid gap-3">
        <div className="h-10 animate-pulse bg-shell-panel" />
        <div className="h-10 animate-pulse bg-shell-panel" />
        <div className="h-24 animate-pulse bg-shell-panel" />
      </div>
    </section>
  );
}

function SettingsPanel({
  settings,
  error,
  onChange,
}: {
  readonly settings: AppSettings;
  readonly error: CommandError | null;
  readonly onChange: (settings: AppSettings) => Promise<void>;
}) {
  return (
    <section className="border border-shell-line bg-white p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-base font-semibold">Settings Storage</h3>
          <p className="mt-2 max-w-[65ch] text-sm leading-6 text-shell-muted">
            Settings are saved through Rust so filesystem ownership starts in the
            correct place.
          </p>
        </div>
      </div>

      {error ? (
        <p className="mt-4 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error.message}
        </p>
      ) : null}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="grid gap-2 text-sm">
          <span className="font-medium">Theme</span>
          <select
            value={settings.theme}
            onChange={(event) =>
              void onChange({
                ...settings,
                theme: event.target.value as AppSettings["theme"],
              })
            }
            className="border border-shell-line bg-white px-3 py-2"
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
          <span className="text-xs text-shell-muted">Visual shell preference.</span>
        </label>

        <label className="grid gap-2 text-sm">
          <span className="font-medium">Advanced tools</span>
          <select
            value={settings.showAdvancedTools ? "true" : "false"}
            onChange={(event) =>
              void onChange({
                ...settings,
                showAdvancedTools: event.target.value === "true",
              })
            }
            className="border border-shell-line bg-white px-3 py-2"
          >
            <option value="false">Hidden</option>
            <option value="true">Visible</option>
          </select>
          <span className="text-xs text-shell-muted">
            Gates future raw JSON and recovery workflows.
          </span>
        </label>
      </div>
    </section>
  );
}
