import { useState } from "react";
import type {
  ConversionResult,
  ConvertJsonToSavDto,
  ConvertSavToJsonDto,
  IdConversionResult,
  RawJsonSummary,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function ConverterPanel() {
  // ID Converter state
  const [idInput, setIdInput] = useState("76561197960287930");
  const [idResult, setIdResult] = useState<IdConversionResult | null>(null);
  const [idLoading, setIdLoading] = useState(false);
  const [idError, setIdError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // File Converter state
  const [savInputPath, setSavInputPath] = useState("");
  const [jsonOutputPath, setJsonOutputPath] = useState("");
  const [minifyJson, setMinifyJson] = useState(false);
  const [jsonInputPath, setJsonInputPath] = useState("");
  const [savOutputPath, setSavOutputPath] = useState("");
  const [targetSaveType, setTargetSaveType] = useState("plz");
  const [convResult, setConvResult] = useState<ConversionResult | null>(null);
  const [convLoading, setConvLoading] = useState(false);
  const [convError, setConvError] = useState<string | null>(null);

  // Raw JSON Inspector state
  const [rawSummary, setRawSummary] = useState<RawJsonSummary | null>(null);
  const [rawLoading, setRawLoading] = useState(false);
  const [rawError, setRawError] = useState<string | null>(null);

  async function handleConvertIds() {
    if (!idInput.trim()) return;
    setIdLoading(true);
    setIdError(null);
    try {
      const res = await invokeCommand<IdConversionResult>(
        "calculate_identifier_conversion",
        { input: idInput },
      );
      setIdResult(res);
    } catch (err: unknown) {
      setIdError((err as { message?: string }).message ?? "Failed to convert identifier");
    } finally {
      setIdLoading(false);
    }
  }

  async function handleConvertSavToJson() {
    if (!savInputPath.trim()) return;
    setConvLoading(true);
    setConvError(null);
    setConvResult(null);
    try {
      const dto: ConvertSavToJsonDto = {
        inputPath: savInputPath.trim(),
        outputPath: jsonOutputPath.trim() || undefined,
        minify: minifyJson,
      };
      const res = await invokeCommand<ConversionResult>("convert_sav_to_json", { dto });
      setConvResult(res);
    } catch (err: unknown) {
      setConvError((err as { message?: string }).message ?? "SAV to JSON conversion failed");
    } finally {
      setConvLoading(false);
    }
  }

  async function handleConvertJsonToSav() {
    if (!jsonInputPath.trim()) return;
    setConvLoading(true);
    setConvError(null);
    setConvResult(null);
    try {
      const dto: ConvertJsonToSavDto = {
        inputPath: jsonInputPath.trim(),
        outputPath: savOutputPath.trim() || undefined,
        saveType: targetSaveType,
      };
      const res = await invokeCommand<ConversionResult>("convert_json_to_sav", { dto });
      setConvResult(res);
    } catch (err: unknown) {
      setConvError((err as { message?: string }).message ?? "JSON to SAV conversion failed");
    } finally {
      setConvLoading(false);
    }
  }

  async function handleInspectRawJson() {
    setRawLoading(true);
    setRawError(null);
    try {
      const res = await invokeCommand<RawJsonSummary>("inspect_raw_json");
      setRawSummary(res);
    } catch (err: unknown) {
      setRawError((err as { message?: string }).message ?? "Failed to inspect active save session");
    } finally {
      setRawLoading(false);
    }
  }

  function copyToClipboard(text: string, fieldName: string) {
    void navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  }

  return (
    <div className="space-y-8">
      {/* ── Section 1: Identifier Calculator ────────────────────────────── */}
      <section className="border border-shell-line bg-shell-surface p-5">
        <div className="flex items-center justify-between border-b border-shell-line pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Identifier Calculator
            </h3>
            <p className="text-xs text-shell-muted">
              Convert between 64-bit SteamID, Palworld Player UID, and No-Steam local UID format.
            </p>
          </div>
          <span className="border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-700">
            CityHash64
          </span>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto]">
          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              SteamID64, Community URL, or Palworld UID
            </label>
            <input
              type="text"
              value={idInput}
              onChange={(e) => setIdInput(e.target.value)}
              placeholder="e.g. 76561197960287930 or https://steamcommunity.com/profiles/..."
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm text-shell-ink focus:border-shell-accent focus:outline-none"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => void handleConvertIds()}
              disabled={idLoading || !idInput.trim()}
              className="h-[38px] border border-shell-accent-solid bg-shell-accent-solid px-5 text-xs font-semibold uppercase tracking-wider text-white transition hover:bg-opacity-90 disabled:opacity-50"
            >
              {idLoading ? "Calculating..." : "Calculate IDs"}
            </button>
          </div>
        </div>

        {idError && (
          <div className="mt-4 border-l-2 border-shell-destructive bg-shell-destructive-subtle p-3 text-xs text-shell-destructive">
            {idError}
          </div>
        )}

        {idResult && (
          <div className="mt-5 grid gap-3 border-t border-shell-line pt-4 sm:grid-cols-3">
            <div className="border border-shell-line bg-shell-panel p-3">
              <span className="font-mono text-[10px] uppercase text-shell-muted">SteamID64</span>
              <p className="mt-1 font-mono text-xs font-semibold text-shell-ink truncate">
                {idResult.steamId}
              </p>
              <button
                type="button"
                onClick={() => copyToClipboard(idResult.steamId, "steam")}
                className="mt-2 text-[11px] text-shell-accent hover:underline"
              >
                {copiedField === "steam" ? "Copied" : "Copy SteamID"}
              </button>
            </div>

            <div className="border border-shell-line bg-shell-panel p-3">
              <span className="font-mono text-[10px] uppercase text-shell-muted">Palworld Player UID</span>
              <p className="mt-1 font-mono text-xs font-semibold text-emerald-700 truncate">
                {idResult.palworldUid}
              </p>
              <button
                type="button"
                onClick={() => copyToClipboard(idResult.palworldUid, "pal")}
                className="mt-2 text-[11px] text-shell-accent hover:underline"
              >
                {copiedField === "pal" ? "Copied" : "Copy Palworld UID"}
              </button>
            </div>

            <div className="border border-shell-line bg-shell-panel p-3">
              <span className="font-mono text-[10px] uppercase text-shell-muted">No-Steam Local UID</span>
              <p className="mt-1 font-mono text-xs font-semibold text-shell-ink truncate">
                {idResult.nosteamUid}
              </p>
              <button
                type="button"
                onClick={() => copyToClipboard(idResult.nosteamUid, "nosteam")}
                className="mt-2 text-[11px] text-shell-accent hover:underline"
              >
                {copiedField === "nosteam" ? "Copied" : "Copy No-Steam UID"}
              </button>
            </div>
          </div>
        )}
      </section>

      {/* ── Section 2: SAV <-> JSON Format Converter ───────────────────── */}
      <section className="border border-shell-line bg-shell-surface p-5">
        <div className="border-b border-shell-line pb-3">
          <h3 className="text-base font-semibold tracking-tight text-shell-ink">
            Format Converter (SAV &lt;-&gt; JSON)
          </h3>
          <p className="text-xs text-shell-muted">
            Decompress .sav containers to structured JSON or package JSON back into GVAS .sav binary.
          </p>
        </div>

        <div className="mt-5 grid gap-6 md:grid-cols-2">
          {/* SAV -> JSON */}
          <div className="border border-shell-line bg-shell-panel p-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-shell-ink">
              SAV to JSON
            </h4>
            <div className="mt-3 space-y-3">
              <div>
                <label className="block text-[11px] text-shell-muted">Input .sav File Path</label>
                <input
                  type="text"
                  value={savInputPath}
                  onChange={(e) => setSavInputPath(e.target.value)}
                  placeholder="C:/Palworld/Level.sav"
                  className="mt-1 w-full border border-shell-line bg-shell-surface px-2.5 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] text-shell-muted">Output .json File Path (Optional)</label>
                <input
                  type="text"
                  value={jsonOutputPath}
                  onChange={(e) => setJsonOutputPath(e.target.value)}
                  placeholder="Defaults to same folder as .json"
                  className="mt-1 w-full border border-shell-line bg-shell-surface px-2.5 py-1.5 font-mono text-xs"
                />
              </div>
              <label className="flex items-center gap-2 text-xs text-shell-ink">
                <input
                  type="checkbox"
                  checked={minifyJson}
                  onChange={(e) => setMinifyJson(e.target.checked)}
                />
                <span>Minify JSON output</span>
              </label>
              <button
                type="button"
                onClick={() => void handleConvertSavToJson()}
                disabled={convLoading || !savInputPath.trim()}
                className="w-full border border-shell-line bg-shell-surface py-2 text-xs font-semibold uppercase tracking-wider text-shell-ink hover:bg-shell-surface disabled:opacity-50"
              >
                {convLoading ? "Converting..." : "Convert SAV to JSON"}
              </button>
            </div>
          </div>

          {/* JSON -> SAV */}
          <div className="border border-shell-line bg-shell-panel p-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-shell-ink">
              JSON to SAV
            </h4>
            <div className="mt-3 space-y-3">
              <div>
                <label className="block text-[11px] text-shell-muted">Input .json File Path</label>
                <input
                  type="text"
                  value={jsonInputPath}
                  onChange={(e) => setJsonInputPath(e.target.value)}
                  placeholder="C:/Palworld/Level.json"
                  className="mt-1 w-full border border-shell-line bg-shell-surface px-2.5 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] text-shell-muted">Output .sav File Path (Optional)</label>
                <input
                  type="text"
                  value={savOutputPath}
                  onChange={(e) => setSavOutputPath(e.target.value)}
                  placeholder="Defaults to same folder as .sav"
                  className="mt-1 w-full border border-shell-line bg-shell-surface px-2.5 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] text-shell-muted">Compression Type</label>
                <select
                  value={targetSaveType}
                  onChange={(e) => setTargetSaveType(e.target.value)}
                  className="mt-1 w-full border border-shell-line bg-shell-surface px-2.5 py-1.5 font-mono text-xs"
                >
                  <option value="plz">PLZ (Double Zlib - Standard Steam)</option>
                  <option value="cnk">CNK (Chunked Zlib)</option>
                </select>
              </div>
              <button
                type="button"
                onClick={() => void handleConvertJsonToSav()}
                disabled={convLoading || !jsonInputPath.trim()}
                className="w-full border border-shell-line bg-shell-surface py-2 text-xs font-semibold uppercase tracking-wider text-shell-ink hover:bg-shell-surface disabled:opacity-50"
              >
                {convLoading ? "Converting..." : "Convert JSON to SAV"}
              </button>
            </div>
          </div>
        </div>

        {convError && (
          <div className="mt-4 border-l-2 border-shell-destructive bg-shell-destructive-subtle p-3 text-xs text-shell-destructive">
            {convError}
          </div>
        )}

        {convResult && (
          <div className="mt-4 border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
            <p className="font-semibold">{convResult.message}</p>
            <p className="mt-1 font-mono text-[11px] text-emerald-700 truncate">
              Output: {convResult.targetPath} ({convResult.bytesWritten.toLocaleString()} bytes)
            </p>
          </div>
        )}
      </section>

      {/* ── Section 3: Gated Raw JSON Inspector ─────────────────────────── */}
      <section className="border border-shell-line bg-shell-surface p-5">
        <div className="flex items-center justify-between border-b border-shell-line pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Raw JSON Inspector &amp; Schema Guard
            </h3>
            <p className="text-xs text-shell-muted">
              Inspect top-level GVAS property mappings of the loaded save session. Advanced editing is read-only protected.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleInspectRawJson()}
            disabled={rawLoading}
            className="border border-shell-line bg-shell-panel px-3 py-1 text-xs font-medium text-shell-ink hover:bg-shell-surface disabled:opacity-50"
          >
            {rawLoading ? "Reading Session..." : "Inspect Active Session"}
          </button>
        </div>

        {rawError && (
          <div className="mt-4 border-l-2 border-shell-warning bg-shell-warning-subtle p-3 text-xs text-shell-warning">
            {rawError} (Load a save session to view raw structure)
          </div>
        )}

        {rawSummary && (
          <div className="mt-4 space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="border border-shell-line bg-shell-panel p-3">
                <span className="font-mono text-[10px] uppercase text-shell-muted">Save Container</span>
                <p className="mt-1 font-mono text-xs font-semibold text-shell-ink">{rawSummary.saveType}</p>
              </div>
              <div className="border border-shell-line bg-shell-panel p-3">
                <span className="font-mono text-[10px] uppercase text-shell-muted">Key Properties</span>
                <p className="mt-1 font-mono text-xs font-semibold text-shell-ink">{rawSummary.propertyCount}</p>
              </div>
              <div className="border border-shell-line bg-shell-panel p-3">
                <span className="font-mono text-[10px] uppercase text-shell-muted">Edit Safety Guard</span>
                <p className="mt-1 font-mono text-xs font-semibold text-emerald-700">
                  {rawSummary.isReadOnly ? "Read-Only (Protected)" : "Advanced Unlocked"}
                </p>
              </div>
            </div>

            <div>
              <span className="font-mono text-[11px] uppercase tracking-wider text-shell-muted">
                Top-Level Property Keys
              </span>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {rawSummary.topLevelKeys.map((key) => (
                  <span
                    key={key}
                    className="border border-shell-line bg-shell-panel px-2 py-0.5 font-mono text-xs text-shell-ink"
                  >
                    {key}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
