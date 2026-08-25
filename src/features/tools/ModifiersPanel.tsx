import { useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import type {
  MutationPreview,
  PalboxCapacityDto,
  RestoreMapOptions,
  RestoreMapReport,
  SlotInjectionAuditResult,
  SlotInjectionParams,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function ModifiersPanel() {
  // Map Fog Restorer state
  const [mapOptions, setMapOptions] = useState<RestoreMapOptions>({
    customLocalDataPath: "",
    clearUiFog: true,
    clearHiddenLocations: true,
    disableSkyCloudOverlay: true,
  });
  const [mapPreview, setMapPreview] = useState<MutationPreview | null>(null);
  const [mapReport, setMapReport] = useState<RestoreMapReport | null>(null);
  const [mapLoading, setMapLoading] = useState(false);
  const [mapCommitting, setMapCommitting] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Palbox Slot Injector state
  const [playerUid, setPlayerUid] = useState("00000000000000000000000000000001");
  const [targetPages, setTargetPages] = useState<number>(64);
  const [capacityInfo, setCapacityInfo] = useState<PalboxCapacityDto | null>(null);
  const [slotPreview, setSlotPreview] = useState<MutationPreview | null>(null);
  const [slotReport, setSlotReport] = useState<SlotInjectionAuditResult | null>(null);
  const [slotLoading, setSlotLoading] = useState(false);
  const [slotCommitting, setSlotCommitting] = useState(false);
  const [slotError, setSlotError] = useState<string | null>(null);

  // Map Restorer Actions
  async function handlePreviewRestoreMap() {
    setMapLoading(true);
    setMapError(null);
    setMapReport(null);
    try {
      const preview = await invokeCommand<MutationPreview>("preview_restore_map", {
        options: {
          ...mapOptions,
          customLocalDataPath: mapOptions.customLocalDataPath?.trim() || undefined,
        },
      });
      setMapPreview(preview);
    } catch (err: unknown) {
      setMapError((err as { message?: string }).message ?? "Failed to preview map restore");
    } finally {
      setMapLoading(false);
    }
  }

  async function handleCommitRestoreMap() {
    if (!mapPreview) return;
    setMapCommitting(true);
    setMapError(null);
    try {
      const report = await invokeCommand<RestoreMapReport>("commit_restore_map", {
        options: {
          ...mapOptions,
          customLocalDataPath: mapOptions.customLocalDataPath?.trim() || undefined,
        },
      });
      setMapReport(report);
      setMapPreview(null);
    } catch (err: unknown) {
      setMapError((err as { message?: string }).message ?? "Failed to execute map restore");
    } finally {
      setMapCommitting(false);
    }
  }

  // Palbox Slot Actions
  async function handleCheckCapacity() {
    if (!playerUid.trim()) return;
    setSlotLoading(true);
    setSlotError(null);
    try {
      const cap = await invokeCommand<PalboxCapacityDto>("get_palbox_capacity", {
        playerUid: playerUid.trim(),
      });
      setCapacityInfo(cap);
    } catch (err: unknown) {
      setSlotError((err as { message?: string }).message ?? "Failed to query Palbox capacity");
    } finally {
      setSlotLoading(false);
    }
  }

  async function handlePreviewInjectSlots() {
    if (!playerUid.trim()) return;
    setSlotLoading(true);
    setSlotError(null);
    setSlotReport(null);
    try {
      const params: SlotInjectionParams = {
        playerUid: playerUid.trim(),
        targetPageCount: targetPages,
      };
      const preview = await invokeCommand<MutationPreview>("preview_inject_palbox_slots", {
        params,
      });
      setSlotPreview(preview);
    } catch (err: unknown) {
      setSlotError((err as { message?: string }).message ?? "Failed to preview slot injection");
    } finally {
      setSlotLoading(false);
    }
  }

  async function handleCommitInjectSlots() {
    if (!slotPreview) return;
    setSlotCommitting(true);
    setSlotError(null);
    try {
      const params: SlotInjectionParams = {
        playerUid: playerUid.trim(),
        targetPageCount: targetPages,
      };
      const report = await invokeCommand<SlotInjectionAuditResult>("commit_inject_palbox_slots", {
        params,
      });
      setSlotReport(report);
      setSlotPreview(null);
    } catch (err: unknown) {
      setSlotError((err as { message?: string }).message ?? "Failed to commit slot injection");
    } finally {
      setSlotCommitting(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* ── Section 1: Map Fog & Exploration Restorer ───────────────────── */}
      <section className="border border-shell-line bg-white p-5">
        <div className="flex items-center justify-between border-b border-shell-line pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Map Fog &amp; Exploration Restorer
            </h3>
            <p className="text-xs text-shell-muted">
              Reveal world map exploration fog in LocalData.sav across the active world or standard Steam saves.
            </p>
          </div>
          <span className="border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-700">
            Non-Destructive
          </span>
        </div>

        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
              Target LocalData.sav or Save Folder (Optional — Defaults to loaded world)
            </label>
            <input
              type="text"
              value={mapOptions.customLocalDataPath}
              onChange={(e) =>
                setMapOptions((prev) => ({ ...prev, customLocalDataPath: e.target.value }))
              }
              placeholder="Leave blank to scan active session and Steam save folder"
              className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
              <input
                type="checkbox"
                checked={mapOptions.clearUiFog}
                onChange={(e) =>
                  setMapOptions((prev) => ({ ...prev, clearUiFog: e.target.checked }))
                }
              />
              <span>Clear Map UI Exploration Mask</span>
            </label>

            <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
              <input
                type="checkbox"
                checked={mapOptions.clearHiddenLocations}
                onChange={(e) =>
                  setMapOptions((prev) => ({ ...prev, clearHiddenLocations: e.target.checked }))
                }
              />
              <span>Reset Hidden Location Flags</span>
            </label>

            <label className="flex items-center gap-2 border border-shell-line bg-shell-panel p-3 text-xs text-shell-ink">
              <input
                type="checkbox"
                checked={mapOptions.disableSkyCloudOverlay}
                onChange={(e) =>
                  setMapOptions((prev) => ({ ...prev, disableSkyCloudOverlay: e.target.checked }))
                }
              />
              <span>Disable Sky Island Clouds</span>
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={() => void handlePreviewRestoreMap()}
              disabled={mapLoading}
              className="border border-shell-accent bg-shell-accent px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
            >
              {mapLoading ? "Scanning Targets..." : "Preview Map Restore"}
            </button>
          </div>
        </div>

        {mapError && (
          <div className="mt-4 border-l-2 border-red-500 bg-red-50 p-3 text-xs text-red-800">
            {mapError}
          </div>
        )}

        {mapReport && (
          <div className="mt-4 border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
            <p className="font-semibold">{mapReport.message}</p>
            <p className="mt-1 font-mono text-[11px] text-emerald-700">
              Updated files: {mapReport.filesUpdated.length} | Backup: {mapReport.backupPath ?? "Automatic snapshot"}
            </p>
          </div>
        )}
      </section>

      {/* ── Section 2: Palbox Storage Slot Injector ────────────────────── */}
      <section className="border border-shell-line bg-white p-5">
        <div className="flex items-center justify-between border-b border-shell-line pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-shell-ink">
              Palbox Storage Slot Injector
            </h3>
            <p className="text-xs text-shell-muted">
              Expand player Palbox storage capacity beyond standard 32 pages (960 slots) safely.
            </p>
          </div>
          <span className="border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 font-mono text-[11px] font-medium text-amber-700">
            Container Mutation
          </span>
        </div>

        <div className="mt-4 space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <div>
              <label className="block text-xs font-medium text-shell-muted uppercase tracking-wider">
                Target Player UID
              </label>
              <input
                type="text"
                value={playerUid}
                onChange={(e) => setPlayerUid(e.target.value)}
                placeholder="e.g. 00000000000000000000000000000001"
                className="mt-1 w-full border border-shell-line bg-shell-panel px-3 py-2 font-mono text-sm"
              />
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={() => void handleCheckCapacity()}
                disabled={slotLoading || !playerUid.trim()}
                className="h-[38px] border border-shell-line bg-shell-panel px-4 text-xs font-medium text-shell-ink hover:bg-shell-surface disabled:opacity-50"
              >
                Inspect Capacity
              </button>
            </div>
          </div>

          {capacityInfo && (
            <div className="grid gap-3 border border-shell-line bg-shell-panel p-3 sm:grid-cols-3">
              <div>
                <span className="font-mono text-[10px] uppercase text-shell-muted">Current Capacity</span>
                <p className="mt-1 font-mono text-sm font-semibold text-shell-ink">
                  {capacityInfo.currentPageCount} Pages ({capacityInfo.currentSlotCount} slots)
                </p>
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase text-shell-muted">Occupied Slots</span>
                <p className="mt-1 font-mono text-sm font-semibold text-shell-ink">
                  {capacityInfo.occupiedSlotCount} Pals Stored
                </p>
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase text-shell-muted">Max Recommended</span>
                <p className="mt-1 font-mono text-sm font-semibold text-emerald-700">
                  {capacityInfo.maxRecommendedPages} Pages (3,840 slots)
                </p>
              </div>
            </div>
          )}

          <div className="border-t border-shell-line pt-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-shell-muted uppercase tracking-wider">
                Target Palbox Capacity
              </label>
              <span className="font-mono text-xs font-semibold text-shell-accent">
                {targetPages} Pages ({targetPages * 30} Total Slots)
              </span>
            </div>

            <div className="mt-3 grid grid-cols-4 gap-2">
              {[32, 48, 64, 128].map((pages) => (
                <button
                  key={pages}
                  type="button"
                  onClick={() => setTargetPages(pages)}
                  className={[
                    "border py-2 text-center text-xs font-medium transition",
                    targetPages === pages
                      ? "border-shell-accent bg-[#edf5f2] text-shell-ink"
                      : "border-shell-line bg-white text-shell-muted hover:bg-shell-panel",
                  ].join(" ")}
                >
                  <p className="font-semibold">{pages} Pages</p>
                  <p className="font-mono text-[10px]">{pages * 30} slots</p>
                </button>
              ))}
            </div>

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => void handlePreviewInjectSlots()}
                disabled={slotLoading || !playerUid.trim()}
                className="border border-shell-accent bg-shell-accent px-5 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-opacity-90 disabled:opacity-50"
              >
                {slotLoading ? "Analyzing Container..." : "Preview Slot Injection"}
              </button>
            </div>
          </div>
        </div>

        {slotError && (
          <div className="mt-4 border-l-2 border-red-500 bg-red-50 p-3 text-xs text-red-800">
            {slotError}
          </div>
        )}

        {slotReport && (
          <div className="mt-4 border-l-2 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-800">
            <p className="font-semibold">{slotReport.message}</p>
            <p className="mt-1 font-mono text-[11px] text-emerald-700">
              Capacity: {slotReport.newPageCount} pages ({slotReport.newSlotCount} slots) | Backup: {slotReport.backupPath ?? "Automatic snapshot"}
            </p>
          </div>
        )}
      </section>

      {/* ── Preview Modals ────────────────────────────────────────────── */}
      <PreviewModal
        preview={mapPreview}
        committing={mapCommitting}
        onCancel={() => setMapPreview(null)}
        onConfirm={handleCommitRestoreMap}
      />

      <PreviewModal
        preview={slotPreview}
        committing={slotCommitting}
        onCancel={() => setSlotPreview(null)}
        onConfirm={handleCommitInjectSlots}
      />
    </div>
  );
}
