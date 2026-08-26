import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  BaseProjection,
  ImportBaseBundleDto,
  MutationPreview,
  NudgeBaseCoordinatesDto,
  UpdateBaseDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function BasesView() {
  const [reloadKey, setReloadKey] = useState(0);

  const state = useAsync(
    useCallback(() => invokeCommand<readonly BaseProjection[]>("get_bases"), []),
    [reloadKey],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.baseName.toLowerCase().includes(q) || r.baseId.toLowerCase().includes(q),
  );

  // Edit base level / radius
  const [selectedBase, setSelectedBase] = useState<BaseProjection | null>(null);
  const [editLevel, setEditLevel] = useState(1);

  // Nudge coordinates drawer
  const [nudgeBase, setNudgeBase] = useState<BaseProjection | null>(null);
  const [nudgeOffsets, setNudgeOffsets] = useState<{ dx: number; dy: number; dz: number }>({
    dx: 0,
    dy: 0,
    dz: 0,
  });

  // Import dialog
  const [showImport, setShowImport] = useState(false);
  const [importPath, setImportPath] = useState("");
  const [importGuildId, setImportGuildId] = useState("");

  // Clone base dialog
  const [cloneBase, setCloneBase] = useState<BaseProjection | null>(null);
  const [cloneTargetGuild, setCloneTargetGuild] = useState("");

  // Preview & mutation state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function startEdit(base: BaseProjection) {
    setSelectedBase(base);
    setEditLevel(base.currentLevel);
  }

  function startNudge(base: BaseProjection) {
    setNudgeBase(base);
    setNudgeOffsets({ dx: 0, dy: 0, dz: 0 });
  }

  function startClone(base: BaseProjection) {
    setCloneBase(base);
    setCloneTargetGuild("");
  }

  async function handleRequestClonePreview() {
    if (!cloneBase || !cloneTargetGuild.trim()) return;
    const dto = {
      baseId: cloneBase.baseId,
      targetGuildId: cloneTargetGuild.trim(),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_clone_base", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_clone_base", { dto });
        setActionMessage(`Cloned base ${cloneBase.baseId} into guild ${cloneTargetGuild}`);
        setCloneBase(null);
        setCloneTargetGuild("");
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestRepairPreview(base: BaseProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_repair_base_structures", {
        baseId: base.baseId,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_repair_base_structures", { baseId: base.baseId });
        setActionMessage(`Repaired all structures for base ${base.baseName || base.baseId}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestEditPreview() {
    if (!selectedBase) return;
    const dto: UpdateBaseDto = {
      baseId: selectedBase.baseId,
      level: Number(editLevel),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_base", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_base", { dto });
        setActionMessage(`Updated base ${selectedBase.baseId}`);
        setSelectedBase(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestNudgePreview() {
    if (!nudgeBase) return;
    const dto: NudgeBaseCoordinatesDto = {
      baseId: nudgeBase.baseId,
      deltaX: Number(nudgeOffsets.dx),
      deltaY: Number(nudgeOffsets.dy),
      deltaZ: Number(nudgeOffsets.dz),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_nudge_base_coordinates", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_nudge_base_coordinates", { dto });
        setActionMessage(`Nudged base ${nudgeBase.baseId} coordinates`);
        setNudgeBase(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleExportBase(base: BaseProjection) {
    const exportPath = `base_${base.baseId.slice(0, 8)}.json`;
    try {
      const savedPath = await invokeCommand<string>("export_base_bundle", {
        baseId: base.baseId,
        exportPath,
      });
      setActionMessage(`Exported base bundle to ${savedPath}`);
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestImportPreview() {
    if (!importPath.trim() || !importGuildId.trim()) return;
    const dto: ImportBaseBundleDto = {
      bundlePath: importPath.trim(),
      targetGuildId: importGuildId.trim(),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_import_base_bundle", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_import_base_bundle", { dto });
        setActionMessage(`Imported base bundle into guild ${importGuildId}`);
        setShowImport(false);
        setImportPath("");
        setImportGuildId("");
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestDeletePreview(base: BaseProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_base", {
        baseId: base.baseId,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_delete_base", { baseId: base.baseId });
        setActionMessage(`Deleted base ${base.baseId}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleConfirmCommit() {
    if (!pendingCommit) return;
    setCommitting(true);
    try {
      await pendingCommit();
      setActivePreview(null);
      setPendingCommit(null);
    } catch (err: unknown) {
      setActionMessage(String(err));
    } finally {
      setCommitting(false);
    }
  }

  return (
    <ViewShell
      title="Bases"
      subtitle="Base camp coordinates, levels, and structure bundles with position nudging, cloning, and repair."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4">
        {/* Action Bar */}
        <div className="flex items-center justify-between border border-shell-line bg-shell-surface px-4 py-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-shell-muted">
              Base Management
            </p>
            <p className="mt-0.5 text-xs text-shell-muted">
              {rows.length} base camp{rows.length !== 1 ? "s" : ""} active
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowImport(!showImport)}
            className="border border-shell-line bg-shell-surface px-3 py-1.5 font-mono text-xs text-shell-ink transition hover:bg-shell-panel active:translate-y-[1px]"
          >
            {showImport ? "Cancel Import" : "Import Base Bundle"}
          </button>
        </div>

        {actionMessage && (
          <div className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-2 text-xs font-mono text-shell-accent">
            {actionMessage}
          </div>
        )}

        {/* Clone Base Drawer */}
        {cloneBase && (
          <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
            <h3 className="text-base font-semibold">Clone Base — {cloneBase.baseName || cloneBase.baseId}</h3>
            <p className="mt-1 text-xs text-shell-muted">
              Duplicate base structures and worker configuration into a target guild.
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Target Guild ID</span>
                <input
                  type="text"
                  placeholder="e.g. 00000000000000000000000000000001"
                  value={cloneTargetGuild}
                  onChange={(e) => setCloneTargetGuild(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setCloneBase(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!cloneTargetGuild.trim()}
                onClick={() => void handleRequestClonePreview()}
                className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px] disabled:opacity-50"
              >
                Preview Clone
              </button>
            </div>
          </div>
        )}

        {/* Import Base Bundle Drawer */}
        {showImport && (
          <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
            <h3 className="text-base font-semibold">Import Base Bundle</h3>
            <p className="mt-1 text-xs text-shell-muted">
              Import a standalone base layout file and assign it to a target guild.
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Bundle File Path</span>
                <input
                  type="text"
                  placeholder="e.g. base_export.json"
                  value={importPath}
                  onChange={(e) => setImportPath(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>Target Guild ID</span>
                <input
                  type="text"
                  placeholder="e.g. 00000000000000000000000000000001"
                  value={importGuildId}
                  onChange={(e) => setImportGuildId(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setShowImport(false)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!importPath.trim() || !importGuildId.trim()}
                onClick={() => void handleRequestImportPreview()}
                className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px] disabled:opacity-50"
              >
                Preview Import
              </button>
            </div>
          </div>
        )}

        {/* Bases Table */}
        <DataTable
          columns={[
            {
              key: "name",
              header: "Base Name",
              sortable: true,
              sortValue: (r) => r.baseName || r.baseId,
              render: (r) => <span className="font-semibold text-shell-ink">{r.baseName || "—"}</span>,
            },
            {
              key: "level",
              header: "Level",
              sortable: true,
              sortValue: (r) => r.currentLevel,
              render: (r) => r.currentLevel,
              width: "70px",
            },
            {
              key: "workers",
              header: "Workers",
              sortable: true,
              sortValue: (r) => r.workerCount,
              render: (r) => r.workerCount,
              width: "80px",
            },
            {
              key: "pos",
              header: "World Coordinates",
              render: (r) => `${r.worldX.toFixed(0)}, ${r.worldY.toFixed(0)}, ${r.worldZ.toFixed(0)}`,
            },
            {
              key: "guild",
              header: "Owner Guild",
              render: (r) => <span className="text-shell-muted">{r.ownerGuildId.slice(0, 12)}…</span>,
              width: "140px",
            },
            {
              key: "actions",
              header: "Actions",
              render: (r) => (
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => startEdit(r)}
                    className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => startNudge(r)}
                    className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Nudge
                  </button>
                  <button
                    type="button"
                    onClick={() => startClone(r)}
                    className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                    title="Clone base to another guild"
                  >
                    Clone
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRequestRepairPreview(r)}
                    className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                    title="Repair all damaged structures to full HP"
                  >
                    Repair
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleExportBase(r)}
                    className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Export
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRequestDeletePreview(r)}
                    className="border border-shell-destructive/40 bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-destructive hover:bg-shell-destructive-subtle active:translate-y-[1px]"
                  >
                    Delete
                  </button>
                </div>
              ),
              width: "280px",
            },
          ]}
          rows={filtered}
          rowKey={(r) => r.baseId}
          searchValue={query}
          onSearchChange={setQuery}
          searchPlaceholder="Filter by base name or ID…"
          emptyHeadline="No bases found"
          emptyDescription="Load a Palworld save directory in Save Session to inspect base camps and camp structures."
        />

        {/* Edit Base Level Drawer */}
        {selectedBase && (
          <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Edit Base — {selectedBase.baseName || selectedBase.baseId}
                </h3>
                <p className="font-mono text-xs text-shell-muted">ID: {selectedBase.baseId}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedBase(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Base Level (1-20)</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={editLevel}
                  onChange={(e) => setEditLevel(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setSelectedBase(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleRequestEditPreview()}
                className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px]"
              >
                Preview & Apply
              </button>
            </div>
          </div>
        )}

        {/* Nudge Coordinates Drawer */}
        {nudgeBase && (
          <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Nudge Coordinates — {nudgeBase.baseName || nudgeBase.baseId}
                </h3>
                <p className="font-mono text-xs text-shell-muted">
                  Current: ({nudgeBase.worldX.toFixed(0)}, {nudgeBase.worldY.toFixed(0)}, {nudgeBase.worldZ.toFixed(0)})
                </p>
              </div>
              <button
                type="button"
                onClick={() => setNudgeBase(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>ΔX (Offset)</span>
                <input
                  type="number"
                  step="100"
                  value={nudgeOffsets.dx}
                  onChange={(e) => setNudgeOffsets({ ...nudgeOffsets, dx: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>ΔY (Offset)</span>
                <input
                  type="number"
                  step="100"
                  value={nudgeOffsets.dy}
                  onChange={(e) => setNudgeOffsets({ ...nudgeOffsets, dy: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>ΔZ (Offset)</span>
                <input
                  type="number"
                  step="50"
                  value={nudgeOffsets.dz}
                  onChange={(e) => setNudgeOffsets({ ...nudgeOffsets, dz: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setNudgeBase(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleRequestNudgePreview()}
                className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px]"
              >
                Preview & Shift
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Mutation Review Modal */}
      <PreviewModal
        preview={activePreview}
        committing={committing}
        onCancel={() => {
          setActivePreview(null);
          setPendingCommit(null);
        }}
        onConfirm={handleConfirmCommit}
      />
    </ViewShell>
  );
}
