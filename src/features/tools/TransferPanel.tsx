import { useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import type {
  CharacterTransferAuditResult,
  CharacterTransferOptions,
  HostSwapAuditResult,
  HostSwapInspectionDto,
  HostSwapOptions,
  MutationPreview,
  TransferPlayerSummaryDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function TransferPanel() {
  // Mode selection: "character-transfer" | "host-swap"
  const [subMode, setSubMode] = useState<"transfer" | "host-swap">("transfer");

  // Character Transfer state
  const [sourcePath, setSourcePath] = useState("");
  const [targetPath, setTargetPath] = useState("");
  const [availablePlayers, setAvailablePlayers] = useState<readonly TransferPlayerSummaryDto[]>([]);
  const [selectedPlayerUid, setSelectedPlayerUid] = useState("");
  const [transferPals, setTransferPals] = useState(true);
  const [transferInventory, setTransferInventory] = useState(true);
  const [transferTech, setTransferTech] = useState(true);
  const [transferPreview, setTransferPreview] = useState<MutationPreview | null>(null);
  const [transferReport, setTransferReport] = useState<CharacterTransferAuditResult | null>(null);
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferCommitting, setTransferCommitting] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);

  // Host Swap state
  const [hostSourceUid, setHostSourceUid] = useState("00000000000000000000000000000001");
  const [hostTargetUid, setHostTargetUid] = useState("");
  const [swapMode, setSwapMode] = useState(true);
  const [hostInspection, setHostInspection] = useState<HostSwapInspectionDto | null>(null);
  const [hostPreview, setHostPreview] = useState<MutationPreview | null>(null);
  const [hostReport, setHostReport] = useState<HostSwapAuditResult | null>(null);
  const [hostLoading, setHostLoading] = useState(false);
  const [hostCommitting, setHostCommitting] = useState(false);
  const [hostError, setHostError] = useState<string | null>(null);

  // Transfer Actions
  async function handleScanSourcePlayers() {
    if (!sourcePath.trim()) return;
    setTransferLoading(true);
    setTransferError(null);
    try {
      const list = await invokeCommand<readonly TransferPlayerSummaryDto[]>(
        "inspect_transfer_source",
        { sourcePath: sourcePath.trim() },
      );
      setAvailablePlayers(list);
      if (list.length > 0 && !selectedPlayerUid) {
        setSelectedPlayerUid(list[0].uid);
      }
    } catch (err: unknown) {
      setTransferError((err as { message?: string }).message ?? "Failed to scan source players");
    } finally {
      setTransferLoading(false);
    }
  }

  async function handlePreviewTransfer() {
    if (!sourcePath.trim() || !targetPath.trim() || !selectedPlayerUid) {
      setTransferError("Please specify Source Path, Target Path, and select a Character.");
      return;
    }
    setTransferLoading(true);
    setTransferError(null);
    setTransferReport(null);
    try {
      const options: CharacterTransferOptions = {
        sourceSavePath: sourcePath.trim(),
        targetSavePath: targetPath.trim(),
        playerUid: selectedPlayerUid,
        transferPals,
        transferInventory,
        transferTech,
        transferAllPlayers: false,
      };
      const preview = await invokeCommand<MutationPreview>("preview_character_transfer", {
        options,
      });
      setTransferPreview(preview);
    } catch (err: unknown) {
      setTransferError((err as { message?: string }).message ?? "Failed to preview transfer");
    } finally {
      setTransferLoading(false);
    }
  }

  async function handleCommitTransfer() {
    if (!transferPreview) return;
    setTransferCommitting(true);
    setTransferError(null);
    try {
      const options: CharacterTransferOptions = {
        sourceSavePath: sourcePath.trim(),
        targetSavePath: targetPath.trim(),
        playerUid: selectedPlayerUid,
        transferPals,
        transferInventory,
        transferTech,
        transferAllPlayers: false,
      };
      const report = await invokeCommand<CharacterTransferAuditResult>(
        "commit_character_transfer",
        { options },
      );
      setTransferReport(report);
      setTransferPreview(null);
    } catch (err: unknown) {
      setTransferError((err as { message?: string }).message ?? "Transfer commit failed");
    } finally {
      setTransferCommitting(false);
    }
  }

  // Host Swap Actions
  async function handleInspectHostSwap() {
    if (!hostSourceUid.trim() || !hostTargetUid.trim()) return;
    setHostLoading(true);
    setHostError(null);
    try {
      const res = await invokeCommand<HostSwapInspectionDto>("inspect_host_swap", {
        sourceUid: hostSourceUid.trim(),
        targetUid: hostTargetUid.trim(),
      });
      setHostInspection(res);
    } catch (err: unknown) {
      setHostError((err as { message?: string }).message ?? "Failed to inspect host swap");
    } finally {
      setHostLoading(false);
    }
  }

  async function handlePreviewHostSwap() {
    if (!hostSourceUid.trim() || !hostTargetUid.trim()) return;
    setHostLoading(true);
    setHostError(null);
    setHostReport(null);
    try {
      const options: HostSwapOptions = {
        sourceUid: hostSourceUid.trim(),
        targetUid: hostTargetUid.trim(),
        swapMode,
      };
      const preview = await invokeCommand<MutationPreview>("preview_host_swap", {
        options,
      });
      setHostPreview(preview);
    } catch (err: unknown) {
      setHostError((err as { message?: string }).message ?? "Failed to preview host swap");
    } finally {
      setHostLoading(false);
    }
  }

  async function handleCommitHostSwap() {
    if (!hostPreview) return;
    setHostCommitting(true);
    setHostError(null);
    try {
      const options: HostSwapOptions = {
        sourceUid: hostSourceUid.trim(),
        targetUid: hostTargetUid.trim(),
        swapMode,
      };
      const report = await invokeCommand<HostSwapAuditResult>("commit_host_swap", {
        options,
      });
      setHostReport(report);
      setHostPreview(null);
    } catch (err: unknown) {
      setHostError((err as { message?: string }).message ?? "Failed to commit host swap");
    } finally {
      setHostCommitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* ── Sub-navigation toggle ────────────────────────────────────────── */}
      <div className="flex border-b border-shell-line">
        <button
          type="button"
          onClick={() => setSubMode("transfer")}
          className={[
            "border-b-2 px-5 py-2.5 text-xs font-semibold uppercase tracking-wider transition",
            subMode === "transfer"
              ? "border-shell-accent text-shell-accent bg-shell-surface"
              : "border-transparent text-shell-muted hover:text-shell-ink",
          ].join(" ")}
        >
          Character Transfer Wizard
        </button>
        <button
          type="button"
          onClick={() => setSubMode("host-swap")}
          className={[
            "border-b-2 px-5 py-2.5 text-xs font-semibold uppercase tracking-wider transition",
            subMode === "host-swap"
              ? "border-shell-accent text-shell-accent bg-shell-surface"
              : "border-transparent text-shell-muted hover:text-shell-ink",
          ].join(" ")}
        >
          Fix Host Save / UID Swap
        </button>
      </div>

      {/* ── Mode 1: Character Transfer ───────────────────────────────────── */}
      {subMode === "transfer" && (
        <section className="border border-shell-line bg-shell-surface p-5 space-y-6">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Cross-World Character Transfer
            </h3>
            <p className="text-xs text-shell-muted">
              Transfer character level, inventory, Pal team, palbox storage, and technology between save roots.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
                Source Save Directory
              </label>
              <div className="mt-1 flex gap-2">
                <input
                  type="text"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                  placeholder="C:/Palworld/SaveGames/.../SourceSave"
                  className="w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => void handleScanSourcePlayers()}
                  disabled={transferLoading || !sourcePath.trim()}
                  className="border border-shell-line bg-shell-panel px-3 text-xs font-medium hover:bg-shell-surface disabled:opacity-50"
                >
                  Scan
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
                Target Save Directory
              </label>
              <input
                type="text"
                value={targetPath}
                onChange={(e) => setTargetPath(e.target.value)}
                placeholder="C:/Palworld/SaveGames/.../TargetSave"
                className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-1.5 font-mono text-xs"
              />
            </div>
          </div>

          {availablePlayers.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider mb-2">
                Select Player to Transfer
              </label>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {availablePlayers.map((p) => (
                  <button
                    key={p.uid}
                    type="button"
                    onClick={() => setSelectedPlayerUid(p.uid)}
                    className={[
                      "border p-3 text-left transition",
                      selectedPlayerUid === p.uid
                        ? "border-shell-accent-solid bg-shell-accent-solid-subtle"
                        : "border-shell-line bg-shell-surface hover:bg-shell-panel",
                    ].join(" ")}
                  >
                    <p className="font-semibold text-xs text-shell-ink">{p.nickname}</p>
                    <p className="mt-1 font-mono text-[10px] text-shell-muted truncate">{p.uid}</p>
                    <div className="mt-2 flex gap-2 font-mono text-[10px] text-shell-muted">
                      <span>Lv.{p.level}</span>
                      <span>•</span>
                      <span>{p.palCount} Pals</span>
                      <span>•</span>
                      <span>{p.itemCount} Items</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-shell-line pt-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
                <input
                  type="checkbox"
                  checked={transferPals}
                  onChange={(e) => setTransferPals(e.target.checked)}
                />
                <span>Transfer Pals &amp; Palbox</span>
              </label>

              <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
                <input
                  type="checkbox"
                  checked={transferInventory}
                  onChange={(e) => setTransferInventory(e.target.checked)}
                />
                <span>Transfer Inventory &amp; Gear</span>
              </label>

              <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
                <input
                  type="checkbox"
                  checked={transferTech}
                  onChange={(e) => setTransferTech(e.target.checked)}
                />
                <span>Transfer Technology &amp; Stats</span>
              </label>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => void handlePreviewTransfer()}
                disabled={transferLoading || !sourcePath.trim() || !targetPath.trim() || !selectedPlayerUid}
                className="border border-shell-accent-solid bg-shell-accent-solid px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
              >
                {transferLoading ? "Analyzing..." : "Preview Transfer"}
              </button>
            </div>
          </div>

          {transferError && (
            <div className="border-l-2 border-shell-destructive bg-shell-destructive-subtle p-3 text-xs text-shell-destructive">
              {transferError}
            </div>
          )}

          {transferReport && (
            <div className="border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
              <p className="font-semibold">{transferReport.message}</p>
              <p className="mt-1 font-mono text-[11px] text-emerald-700">
                Pals: {transferReport.palsTransferred} | Items: {transferReport.itemsTransferred} | Backup: {transferReport.backupPath ?? "Automatic snapshot"}
              </p>
            </div>
          )}
        </section>
      )}

      {/* ── Mode 2: Fix Host Save / UID Swap ─────────────────────────────── */}
      {subMode === "host-swap" && (
        <section className="border border-shell-line bg-shell-surface p-5 space-y-6">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Fix Host Save &amp; Player UID Swap
            </h3>
            <p className="text-xs text-shell-muted">
              Migrate local co-op host (00000000-0000-0000-0000-000000000001) to a dedicated server Steam GUID with deep reference patching.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
                Source Player UID (Old / Co-op Host)
              </label>
              <input
                type="text"
                value={hostSourceUid}
                onChange={(e) => setHostSourceUid(e.target.value)}
                placeholder="00000000000000000000000000000001"
                className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
                Target Player UID (New / Steam Dedicated GUID)
              </label>
              <input
                type="text"
                value={hostTargetUid}
                onChange={(e) => setHostTargetUid(e.target.value)}
                placeholder="e.g. 70390ba5000000000000000000000000"
                className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm"
              />
            </div>
          </div>

          <div className="flex gap-4 border-y border-shell-line py-3">
            <label className="flex items-center gap-2 text-xs text-shell-ink">
              <input
                type="radio"
                name="swap_mode"
                checked={swapMode}
                onChange={() => setSwapMode(true)}
              />
              <span>Two-Way Exchange (Swap Player Files &amp; Records)</span>
            </label>

            <label className="flex items-center gap-2 text-xs text-shell-ink">
              <input
                type="radio"
                name="swap_mode"
                checked={!swapMode}
                onChange={() => setSwapMode(false)}
              />
              <span>One-Way Migration (Migrate Source to Target)</span>
            </label>
          </div>

          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={() => void handleInspectHostSwap()}
              disabled={hostLoading || !hostSourceUid.trim() || !hostTargetUid.trim()}
              className="border border-shell-line bg-shell-panel px-4 py-2 text-xs font-medium hover:bg-shell-surface disabled:opacity-50"
            >
              Inspect References
            </button>

            <button
              type="button"
              onClick={() => void handlePreviewHostSwap()}
              disabled={hostLoading || !hostSourceUid.trim() || !hostTargetUid.trim()}
              className="border border-shell-accent-solid bg-shell-accent-solid px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
            >
              {hostLoading ? "Inspecting..." : "Preview Host Swap"}
            </button>
          </div>

          {hostInspection && (
            <div className="grid gap-3 border border-shell-line bg-shell-panel p-4 sm:grid-cols-2">
              <div>
                <span className="font-mono text-[10px] uppercase text-shell-muted">Source Player</span>
                <p className="mt-1 font-semibold text-xs text-shell-ink">{hostInspection.sourceNickname}</p>
                <p className="font-mono text-[10px] text-shell-muted">{hostInspection.sourcePalCount} Pals</p>
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase text-shell-muted">Target Player</span>
                <p className="mt-1 font-semibold text-xs text-shell-ink">{hostInspection.targetNickname}</p>
                <p className="font-mono text-[10px] text-shell-muted">{hostInspection.targetPalCount} Pals</p>
              </div>
            </div>
          )}

          {hostError && (
            <div className="border-l-2 border-shell-destructive bg-shell-destructive-subtle p-3 text-xs text-shell-destructive">
              {hostError}
            </div>
          )}

          {hostReport && (
            <div className="border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
              <p className="font-semibold">{hostReport.message}</p>
              <p className="mt-1 font-mono text-[11px] text-emerald-700">
                Mode: {hostReport.mode} | Renamed Files: {hostReport.filesRenamed.length} | Backup: {hostReport.backupPath ?? "Automatic snapshot"}
              </p>
            </div>
          )}
        </section>
      )}

      {/* ── Preview Modals ────────────────────────────────────────────── */}
      <PreviewModal
        preview={transferPreview}
        committing={transferCommitting}
        onCancel={() => setTransferPreview(null)}
        onConfirm={handleCommitTransfer}
      />

      <PreviewModal
        preview={hostPreview}
        committing={hostCommitting}
        onCancel={() => setHostPreview(null)}
        onConfirm={handleCommitHostSwap}
      />
    </div>
  );
}
