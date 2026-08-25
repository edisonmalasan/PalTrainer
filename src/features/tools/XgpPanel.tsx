import { useEffect, useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { WarningBanner } from "../../shared/components/WarningBanner";
import type {
  MutationPreview,
  XgpExtractOptions,
  XgpExtractResult,
  XgpImportAuditResult,
  XgpImportOptions,
  XgpSaveEntry,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function XgpPanel() {
  // Discovery state
  const [discoveredSaves, setDiscoveredSaves] = useState<readonly XgpSaveEntry[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState<string | null>(null);

  // Extraction state
  const [extractWgsDir, setExtractWgsDir] = useState("");
  const [extractDestPath, setExtractDestPath] = useState("");
  const [extractResult, setExtractResult] = useState<XgpExtractResult | null>(null);
  const [extractLoading, setExtractLoading] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  // Import / Package state
  const [importSteamPath, setImportSteamPath] = useState("");
  const [importWgsTarget, setImportWgsTarget] = useState("");
  const [importPreview, setImportPreview] = useState<MutationPreview | null>(null);
  const [importReport, setImportReport] = useState<XgpImportAuditResult | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importCommitting, setImportCommitting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);

  useEffect(() => {
    void handleDiscoverXgp();
  }, []);

  async function handleDiscoverXgp() {
    setDiscovering(true);
    setDiscoverError(null);
    try {
      const list = await invokeCommand<readonly XgpSaveEntry[]>("discover_xgp_saves");
      setDiscoveredSaves(list);
      if (list.length > 0) {
        setExtractWgsDir(list[0].wgsDir);
        setImportWgsTarget(list[0].wgsDir);
      }
    } catch (err: unknown) {
      setDiscoverError((err as { message?: string }).message ?? "Failed to scan Xbox GamePass saves");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleExtractXgp() {
    if (!extractWgsDir.trim() || !extractDestPath.trim()) return;
    setExtractLoading(true);
    setExtractError(null);
    setExtractResult(null);
    try {
      const options: XgpExtractOptions = {
        wgsUserDir: extractWgsDir.trim(),
        destinationPath: extractDestPath.trim(),
      };
      const res = await invokeCommand<XgpExtractResult>("extract_xgp_save", { options });
      setExtractResult(res);
    } catch (err: unknown) {
      setExtractError((err as { message?: string }).message ?? "Failed to extract XGP save");
    } finally {
      setExtractLoading(false);
    }
  }

  async function handlePreviewImportSteam() {
    if (!importSteamPath.trim() || !importWgsTarget.trim()) return;
    setImportLoading(true);
    setImportError(null);
    setImportReport(null);
    try {
      const options: XgpImportOptions = {
        sourceSteamPath: importSteamPath.trim(),
        targetWgsUserDir: importWgsTarget.trim(),
      };
      const preview = await invokeCommand<MutationPreview>("preview_import_steam_to_xgp", {
        options,
      });
      setImportPreview(preview);
    } catch (err: unknown) {
      setImportError((err as { message?: string }).message ?? "Failed to preview XGP import");
    } finally {
      setImportLoading(false);
    }
  }

  async function handleCommitImportSteam() {
    if (!importPreview) return;
    setImportCommitting(true);
    setImportError(null);
    try {
      const options: XgpImportOptions = {
        sourceSteamPath: importSteamPath.trim(),
        targetWgsUserDir: importWgsTarget.trim(),
      };
      const report = await invokeCommand<XgpImportAuditResult>("commit_import_steam_to_xgp", {
        options,
      });
      setImportReport(report);
      setImportPreview(null);
    } catch (err: unknown) {
      setImportError((err as { message?: string }).message ?? "Failed to package save to XGP");
    } finally {
      setImportCommitting(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* ── Section 1: Xbox Cloud Sync Advisory Banner ─────────────────── */}
      <WarningBanner
        severity="warning"
        badge="XBOX CLOUD SYNC ADVISORY"
        title="Game Client & Gaming Services Precaution"
        description="Before extracting or importing Xbox GamePass saves, ensure the Palworld game client and Xbox Gaming Services app are completely closed. Writing container blobs while cloud synchronization is active can trigger cloud conflict dialogs upon next launch."
      />

      {/* ── Section 2: Discovered Xbox GamePass Saves ───────────────────── */}
      <section className="border border-shell-line bg-white p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-shell-line pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Xbox GamePass Save Explorer
            </h3>
            <p className="text-xs text-shell-muted">
              Auto-scans %LOCALAPPDATA%/Packages/PocketpairInc.Palworld_*/SystemAppData/wgs/
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleDiscoverXgp()}
            disabled={discovering}
            className="border border-shell-line bg-shell-panel px-3 py-1.5 text-xs font-medium text-shell-ink hover:bg-shell-surface disabled:opacity-50"
          >
            {discovering ? "Scanning..." : "Refresh Discovery"}
          </button>
        </div>

        {discoverError && (
          <div className="border-l-2 border-red-500 bg-red-50 p-3 text-xs text-red-800">
            {discoverError}
          </div>
        )}

        {discoveredSaves.length === 0 && !discovering && (
          <p className="border border-dashed border-shell-line p-6 text-center text-xs text-shell-muted">
            No active Xbox GamePass Palworld saves detected on this system. You can manually specify a WGS folder below.
          </p>
        )}

        {discoveredSaves.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2">
            {discoveredSaves.map((entry) => (
              <div
                key={entry.wgsDir}
                className="border border-shell-line bg-shell-panel p-3 text-xs"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-shell-ink truncate">User ID: {entry.userId}</p>
                    <p className="mt-0.5 font-mono text-[10px] text-shell-muted truncate">
                      {entry.wgsDir}
                    </p>
                  </div>
                  <span className="border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 font-mono text-[10px] text-emerald-700">
                    {entry.containerCount} Containers
                  </span>
                </div>

                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setExtractWgsDir(entry.wgsDir);
                      setExtractDestPath("C:/Palworld/Extracted_From_GamePass");
                    }}
                    className="border border-shell-line bg-white px-2.5 py-1 text-[11px] font-medium hover:bg-shell-surface"
                  >
                    Select for Extract
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportWgsTarget(entry.wgsDir)}
                    className="border border-shell-line bg-white px-2.5 py-1 text-[11px] font-medium hover:bg-shell-surface"
                  >
                    Select as Import Target
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Section 3: GamePass to Steam Extraction ────────────────────── */}
      <section className="border border-shell-line bg-white p-5 space-y-4">
        <div className="border-b border-shell-line pb-3">
          <h3 className="text-base font-semibold tracking-tight text-shell-ink">
            Extract GamePass Save to Steam Folder
          </h3>
          <p className="text-xs text-shell-muted">
            Unpack container blobs into standard Level.sav, LevelMeta.sav, and Players/*.sav files.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              Source GamePass WGS User Directory
            </label>
            <input
              type="text"
              value={extractWgsDir}
              onChange={(e) => setExtractWgsDir(e.target.value)}
              placeholder=".../SystemAppData/wgs/000900000_..."
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              Destination Steam Save Folder
            </label>
            <input
              type="text"
              value={extractDestPath}
              onChange={(e) => setExtractDestPath(e.target.value)}
              placeholder="C:/Palworld/Extracted_Save"
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={() => void handleExtractXgp()}
            disabled={extractLoading || !extractWgsDir.trim() || !extractDestPath.trim()}
            className="border border-shell-accent bg-shell-accent px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
          >
            {extractLoading ? "Extracting Blobs..." : "Extract Save to Steam Format"}
          </button>
        </div>

        {extractError && (
          <div className="border-l-2 border-red-500 bg-red-50 p-3 text-xs text-red-800">
            {extractError}
          </div>
        )}

        {extractResult && (
          <div className="border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
            <p className="font-semibold">{extractResult.message}</p>
            <p className="mt-1 font-mono text-[11px] text-emerald-700 truncate">
              Extracted to: {extractResult.destinationPath} ({extractResult.filesExtracted.length} files)
            </p>
          </div>
        )}
      </section>

      {/* ── Section 4: Steam to GamePass Packaging ─────────────────────── */}
      <section className="border border-shell-line bg-white p-5 space-y-4">
        <div className="border-b border-shell-line pb-3">
          <h3 className="text-base font-semibold tracking-tight text-shell-ink">
            Package Steam Save to Xbox GamePass WGS
          </h3>
          <p className="text-xs text-shell-muted">
            Generate containers.index v14 and package Level and Player save files into WGS format.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              Source Steam Save Folder
            </label>
            <input
              type="text"
              value={importSteamPath}
              onChange={(e) => setImportSteamPath(e.target.value)}
              placeholder="C:/Palworld/SaveGames/.../SaveA"
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              Target GamePass WGS User Directory
            </label>
            <input
              type="text"
              value={importWgsTarget}
              onChange={(e) => setImportWgsTarget(e.target.value)}
              placeholder=".../SystemAppData/wgs/000900000_..."
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={() => void handlePreviewImportSteam()}
            disabled={importLoading || !importSteamPath.trim() || !importWgsTarget.trim()}
            className="border border-shell-accent bg-shell-accent px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
          >
            {importLoading ? "Analyzing..." : "Preview GamePass Import"}
          </button>
        </div>

        {importError && (
          <div className="border-l-2 border-red-500 bg-red-50 p-3 text-xs text-red-800">
            {importError}
          </div>
        )}

        {importReport && (
          <div className="border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
            <p className="font-semibold">{importReport.message}</p>
            <p className="mt-1 font-mono text-[11px] text-emerald-700 truncate">
              Target: {importReport.targetWgsUserDir} | Backup: {importReport.backupPath ?? "Automatic snapshot"}
            </p>
          </div>
        )}
      </section>

      {/* ── Preview Modal ────────────────────────────────────────────── */}
      <PreviewModal
        preview={importPreview}
        committing={importCommitting}
        onCancel={() => setImportPreview(null)}
        onConfirm={handleCommitImportSteam}
      />
    </div>
  );
}
