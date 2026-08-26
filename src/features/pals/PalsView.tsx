import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  ClonePalDto,
  CreatePalDto,
  MutationPreview,
  PalProjection,
  UpdatePalDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function PalsView() {
  const [reloadKey, setReloadKey] = useState(0);

  const state = useAsync(
    useCallback(() => invokeCommand<readonly PalProjection[]>("get_pals"), []),
    [reloadKey],
  );

  const rows = state.status === "ok" ? state.data : [];
  const [locationFilter, setLocationFilter] = useState<string>("All");

  const locationFiltered =
    locationFilter === "All"
      ? rows
      : rows.filter((r) => r.location.toLowerCase() === locationFilter.toLowerCase());

  const { query, setQuery, filtered } = useSearchFilter(
    locationFiltered,
    (r, q) =>
      (r.nickname || r.speciesId).toLowerCase().includes(q) ||
      r.speciesId.toLowerCase().includes(q) ||
      r.instanceId.toLowerCase().includes(q),
  );

  // Bulk Selection & Operations state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [syncSourceId, setSyncSourceId] = useState("");
  const [syncPassives, setSyncPassives] = useState(true);
  const [syncActives, setSyncActives] = useState(true);

  const [showDeleteSpeciesModal, setShowDeleteSpeciesModal] = useState(false);
  const [deleteSpeciesTarget, setDeleteSpeciesTarget] = useState("");

  // Edit Drawer state
  const [selectedPal, setSelectedPal] = useState<PalProjection | null>(null);
  const [editNickname, setEditNickname] = useState("");
  const [editLevel, setEditLevel] = useState(50);
  const [editGender, setEditGender] = useState("Male");
  const [editIvHp, setEditIvHp] = useState(100);
  const [editIvAtk, setEditIvAtk] = useState(100);
  const [editIvDef, setEditIvDef] = useState(100);
  const [editRank, setEditRank] = useState(4);
  const [editSouls, setEditSouls] = useState(30);
  const [editPassives, setEditPassives] = useState<string[]>([]);
  const [editActives, setEditActives] = useState<string[]>([]);
  const [editBoss, setEditBoss] = useState(false);
  const [editLucky, setEditLucky] = useState(false);
  const [editCheatMode, setEditCheatMode] = useState(false);

  // Create Pal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSpecies, setNewSpecies] = useState("Anubis");
  const [newNickname, setNewNickname] = useState("");
  const [newLevel, setNewLevel] = useState(50);
  const [newGender, setNewGender] = useState("Male");
  const [newContainer, setNewContainer] = useState("Party");
  const [newCheatMode, setNewCheatMode] = useState(false);

  // Clone Pal state
  const [clonePal, setClonePal] = useState<PalProjection | null>(null);
  const [cloneTargetContainer, setCloneTargetContainer] = useState("Palbox");

  // Preview & mutation commit state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filtered.map((r) => r.instanceId)));
    }
  }

  async function handleBulkMaxPreview(cheatMode: boolean) {
    const ids = Array.from(selectedIds);
    const dto = { instanceIds: ids, cheatMode };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_bulk_max_pals", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_bulk_max_pals", { dto });
        setActionMessage(`Maxed stats for ${count} Pals (${cheatMode ? "Cheat Mode" : "Normal Caps"})`);
        setSelectedIds(new Set());
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleBulkSyncSkillsPreview() {
    if (!syncSourceId || selectedIds.size === 0) return;
    const targetIds = Array.from(selectedIds).filter((id) => id !== syncSourceId);
    const dto = {
      sourceInstanceId: syncSourceId,
      targetInstanceIds: targetIds,
      syncPassives,
      syncActiveSkills: syncActives,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_bulk_sync_pal_skills", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_bulk_sync_pal_skills", { dto });
        setActionMessage(`Synced skills to ${count} target Pals`);
        setShowSyncModal(false);
        setSyncSourceId("");
        setSelectedIds(new Set());
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleBulkDeleteSelectedPreview() {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_pal", {
        dto: { instanceIds: ids },
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_delete_pal", {
          dto: { instanceIds: ids },
        });
        setActionMessage(`Deleted ${count} selected Pals`);
        setSelectedIds(new Set());
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleBulkDeleteBySpeciesPreview() {
    if (!deleteSpeciesTarget.trim()) return;
    const matched = rows.filter(
      (r) => r.speciesId.toLowerCase() === deleteSpeciesTarget.trim().toLowerCase(),
    );
    if (matched.length === 0) {
      setActionMessage(`No Pals found with species "${deleteSpeciesTarget}"`);
      return;
    }
    const ids = matched.map((r) => r.instanceId);

    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_pal", {
        dto: { instanceIds: ids },
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_delete_pal", {
          dto: { instanceIds: ids },
        });
        setActionMessage(`Deleted all ${count} instances of ${deleteSpeciesTarget}`);
        setShowDeleteSpeciesModal(false);
        setDeleteSpeciesTarget("");
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  function startEdit(pal: PalProjection) {
    setSelectedPal(pal);
    setEditNickname(pal.nickname || "");
    setEditLevel(pal.level);
    setEditGender(pal.gender);
    setEditIvHp(pal.ivHp);
    setEditIvAtk(pal.ivAttack);
    setEditIvDef(pal.ivDefense);
    setEditRank(pal.rank);
    setEditSouls(pal.souls);
    setEditPassives([...pal.passiveSkills]);
    setEditActives([...pal.activeSkills]);
    setEditBoss(pal.isBoss);
    setEditLucky(pal.isLucky);
    setEditCheatMode(false);
  }

  async function handleRequestEditPreview() {
    if (!selectedPal) return;
    const dto: UpdatePalDto = {
      instanceId: selectedPal.instanceId,
      nickname: editNickname.trim() ? editNickname.trim() : undefined,
      level: editLevel,
      gender: editGender,
      ivHp: editIvHp,
      ivAttack: editIvAtk,
      ivDefense: editIvDef,
      condenserRank: editRank,
      souls: editSouls,
      passiveSkills: editPassives,
      activeSkills: editActives,
      isBoss: editBoss,
      isLucky: editLucky,
      cheatMode: editCheatMode,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_pal", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_pal", { dto });
        setActionMessage(`Updated Pal ${selectedPal.nickname || selectedPal.speciesId}`);
        setSelectedPal(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestCreatePreview() {
    if (!newSpecies.trim()) return;
    const dto: CreatePalDto = {
      speciesId: newSpecies.trim(),
      nickname: newNickname.trim() ? newNickname.trim() : undefined,
      level: newLevel,
      gender: newGender,
      containerType: newContainer,
      cheatMode: newCheatMode,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_create_pal", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_create_pal", { dto });
        setActionMessage(`Created new ${newSpecies} Pal in ${newContainer}`);
        setShowCreateModal(false);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestClonePreview() {
    if (!clonePal) return;
    const dto: ClonePalDto = {
      instanceId: clonePal.instanceId,
      targetContainerType: cloneTargetContainer,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_clone_pal", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_clone_pal", { dto });
        setActionMessage(`Cloned Pal ${clonePal.speciesId} to ${cloneTargetContainer}`);
        setClonePal(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleExportPal(pal: PalProjection) {
    const exportPath = `pal_${pal.speciesId}_${pal.instanceId.slice(0, 8)}.json`;
    try {
      const path = await invokeCommand<string>("export_pal_bundle", {
        dto: { instanceId: pal.instanceId, exportPath },
      });
      setActionMessage(`Exported Pal to ${path}`);
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestDeletePreview(pal: PalProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_pal", {
        dto: { instanceIds: [pal.instanceId] },
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_delete_pal", {
          dto: { instanceIds: [pal.instanceId] },
        });
        setActionMessage(`Deleted Pal ${pal.nickname || pal.speciesId}`);
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
      title="Pals"
      subtitle="Pal instances across party, palbox, base workers, and storage with formula stat recalculation and legality protection."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4">
        {/* Action Header & Location Filter Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border border-shell-line bg-white p-3">
          <div className="flex items-center gap-1">
            {["All", "Party", "Palbox", "Base", "DPS", "GPS"].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setLocationFilter(tab)}
                className={[
                  "px-3 py-1 text-xs font-medium transition active:translate-y-[1px]",
                  locationFilter.toLowerCase() === tab.toLowerCase()
                    ? "border border-shell-accent bg-[#edf5f2] font-semibold text-shell-accent"
                    : "border border-transparent text-shell-muted hover:border-shell-line hover:text-shell-ink",
                ].join(" ")}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowDeleteSpeciesModal(true)}
              className="border border-shell-line bg-white px-3 py-1.5 font-mono text-xs text-shell-muted transition hover:bg-shell-panel active:translate-y-[1px]"
            >
              Delete by Species
            </button>
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="border border-shell-accent bg-[#edf5f2] px-3 py-1.5 font-mono text-xs font-semibold text-shell-accent transition hover:bg-[#d9ede7] active:translate-y-[1px]"
            >
              + Create Pal
            </button>
          </div>
        </div>

        {/* Bulk Actions Bar (Shown when Pals are selected) */}
        {selectedIds.size > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 border border-shell-accent bg-[#edf5f2] p-3">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-semibold text-shell-accent">
                {selectedIds.size} Pal{selectedIds.size !== 1 ? "s" : ""} selected
              </span>
              <button
                type="button"
                onClick={() => setSelectedIds(new Set())}
                className="text-xs text-shell-muted underline hover:text-shell-ink"
              >
                Clear Selection
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleBulkMaxPreview(false)}
                className="border border-shell-line bg-white px-3 py-1 text-xs font-medium text-shell-ink hover:bg-shell-panel active:translate-y-[1px]"
              >
                Max Selected (Lv 55)
              </button>
              <button
                type="button"
                onClick={() => void handleBulkMaxPreview(true)}
                className="border border-shell-line bg-white px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-50 active:translate-y-[1px]"
              >
                Max Selected (Lv 60 Cheat)
              </button>
              <button
                type="button"
                onClick={() => {
                  setSyncSourceId(Array.from(selectedIds)[0]);
                  setShowSyncModal(true);
                }}
                className="border border-shell-line bg-white px-3 py-1 text-xs font-medium text-shell-ink hover:bg-shell-panel active:translate-y-[1px]"
              >
                Sync Skills…
              </button>
              <button
                type="button"
                onClick={() => void handleBulkDeleteSelectedPreview()}
                className="border border-red-300 bg-white px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50 active:translate-y-[1px]"
              >
                Delete Selected
              </button>
            </div>
          </div>
        )}

        {actionMessage && (
          <div className="border border-shell-accent bg-[#edf5f2] px-4 py-2 font-mono text-xs text-shell-accent">
            {actionMessage}
          </div>
        )}

        {/* Sync Skills Modal */}
        {showSyncModal && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold">Sync Skills Across Selected Pals</h3>
            <p className="mt-1 text-xs text-shell-muted">
              Copy passives and/or active skills from a source Pal to {selectedIds.size} target Pals.
            </p>

            <div className="mt-4 grid max-w-md gap-4">
              <label className="grid gap-1 text-xs font-medium">
                <span>Source Pal Instance ID</span>
                <select
                  value={syncSourceId}
                  onChange={(e) => setSyncSourceId(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                >
                  {Array.from(selectedIds).map((id) => {
                    const pal = rows.find((r) => r.instanceId === id);
                    return (
                      <option key={id} value={id}>
                        {pal ? `${pal.nickname || pal.speciesId} (${id.slice(0, 8)})` : id}
                      </option>
                    );
                  })}
                </select>
              </label>

              <div className="flex gap-4 text-xs font-medium">
                <label className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={syncPassives}
                    onChange={(e) => setSyncPassives(e.target.checked)}
                  />
                  <span>Sync Passive Skills</span>
                </label>
                <label className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={syncActives}
                    onChange={(e) => setSyncActives(e.target.checked)}
                  />
                  <span>Sync Active Skills</span>
                </label>
              </div>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setShowSyncModal(false)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleBulkSyncSkillsPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Preview Sync
              </button>
            </div>
          </div>
        )}

        {/* Delete by Species Modal */}
        {showDeleteSpeciesModal && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold">Bulk Delete by Species</h3>
            <p className="mt-1 text-xs text-shell-muted">
              Permanently remove all instances of a species (e.g. Lamball, Chikipi) across all storage.
            </p>

            <div className="mt-4 max-w-sm">
              <label className="grid gap-1 text-xs font-medium">
                <span>Species Name / ID</span>
                <input
                  type="text"
                  placeholder="e.g. Lamball, Chikipi"
                  value={deleteSpeciesTarget}
                  onChange={(e) => setDeleteSpeciesTarget(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setShowDeleteSpeciesModal(false)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!deleteSpeciesTarget.trim()}
                onClick={() => void handleBulkDeleteBySpeciesPreview()}
                className="border border-red-300 bg-white px-4 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 active:translate-y-[1px] disabled:opacity-50"
              >
                Preview Deletion
              </button>
            </div>
          </div>
        )}

        {/* Create Pal Modal Drawer */}
        {showCreateModal && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold">Create New Pal</h3>
            <p className="mt-1 text-xs text-shell-muted">
              Spawn a Pal directly into a chosen party, palbox, or storage slot.
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <label className="grid gap-1 text-xs font-medium">
                <span>Species ID</span>
                <input
                  type="text"
                  value={newSpecies}
                  onChange={(e) => setNewSpecies(e.target.value)}
                  placeholder="e.g. Anubis, Jetragon"
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Nickname (Optional)</span>
                <input
                  type="text"
                  value={newNickname}
                  onChange={(e) => setNewNickname(e.target.value)}
                  placeholder="Custom name"
                  className="border border-shell-line px-3 py-1.5 text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Level</span>
                <input
                  type="number"
                  min={1}
                  max={newCheatMode ? 60 : 55}
                  value={newLevel}
                  onChange={(e) => setNewLevel(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Gender</span>
                <select
                  value={newGender}
                  onChange={(e) => setNewGender(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 text-xs"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Target Container</span>
                <select
                  value={newContainer}
                  onChange={(e) => setNewContainer(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 text-xs"
                >
                  <option value="Party">Party</option>
                  <option value="Palbox">Palbox</option>
                  <option value="Base">Base Workers</option>
                  <option value="DPS">DPS Storage</option>
                  <option value="GPS">Global Pal Storage</option>
                </select>
              </label>

              <label className="flex items-center gap-2 pt-6 text-xs font-medium">
                <input
                  type="checkbox"
                  checked={newCheatMode}
                  onChange={(e) => setNewCheatMode(e.target.checked)}
                />
                <span>Enable Cheat Mode Caps</span>
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!newSpecies.trim()}
                onClick={() => void handleRequestCreatePreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px] disabled:opacity-50"
              >
                Preview Create
              </button>
            </div>
          </div>
        )}

        {/* Clone Pal Modal */}
        {clonePal && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold">
              Clone Pal — {clonePal.nickname || clonePal.speciesId}
            </h3>
            <p className="mt-1 text-xs text-shell-muted">
              Duplicate this exact Pal into another container slot.
            </p>

            <div className="mt-4 grid max-w-sm gap-2 text-xs font-medium">
              <span>Target Container</span>
              <select
                value={cloneTargetContainer}
                onChange={(e) => setCloneTargetContainer(e.target.value)}
                className="border border-shell-line px-3 py-1.5 text-xs"
              >
                <option value="Party">Party</option>
                <option value="Palbox">Palbox</option>
                <option value="Base">Base Workers</option>
                <option value="DPS">DPS Storage</option>
                <option value="GPS">Global Pal Storage</option>
              </select>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setClonePal(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleRequestClonePreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Preview Clone
              </button>
            </div>
          </div>
        )}

        {/* Pals Table */}
        <DataTable
          columns={[
            {
              key: "select",
              header: (
                <input
                  type="checkbox"
                  checked={filtered.length > 0 && selectedIds.size === filtered.length}
                  onChange={toggleSelectAll}
                  aria-label="Select all Pals"
                />
              ),
              render: (r) => (
                <input
                  type="checkbox"
                  checked={selectedIds.has(r.instanceId)}
                  onChange={() => toggleSelect(r.instanceId)}
                  aria-label={`Select ${r.nickname || r.speciesId}`}
                />
              ),
              width: "40px",
            },
            {
              key: "species",
              header: "Species / Nickname",
              render: (r) => (
                <div>
                  <span className="font-semibold text-shell-ink">
                    {r.nickname ? `${r.nickname} (${r.speciesId})` : r.speciesId}
                  </span>
                  <div className="font-mono text-[10px] text-shell-muted">
                    {r.instanceId.slice(0, 14)}…
                  </div>
                </div>
              ),
            },
            { key: "level", header: "Lv", render: (r) => r.level, width: "50px" },
            {
              key: "gender",
              header: "Gender",
              render: (r) => (
                <span className={r.gender === "Male" ? "text-blue-600" : "text-rose-600"}>
                  {r.gender}
                </span>
              ),
              width: "70px",
            },
            {
              key: "rank",
              header: "Stars / Souls",
              render: (r) => (
                <span className="font-mono text-xs">
                  ★{r.rank} / +{r.souls}
                </span>
              ),
              width: "100px",
            },
            {
              key: "ivs",
              header: "IVs (HP/ATK/DEF)",
              render: (r) => (
                <span className="font-mono text-xs">
                  {r.ivHp}% / {r.ivAttack}% / {r.ivDefense}%
                </span>
              ),
              width: "140px",
            },
            {
              key: "stats",
              header: "Combat (HP/ATK/DEF)",
              render: (r) => (
                <span className="font-mono text-xs">
                  {r.maxHp} / {r.attack} / {r.defense}
                </span>
              ),
              width: "160px",
            },
            {
              key: "passives",
              header: "Passives",
              render: (r) => (
                <div className="flex flex-wrap gap-1">
                  {r.passiveSkills.map((p) => (
                    <span
                      key={p}
                      className="border border-shell-line bg-shell-panel px-1.5 py-0.5 text-[10px] font-medium"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              ),
            },
            {
              key: "location",
              header: "Location",
              render: (r) => (
                <span className="border border-shell-line bg-white px-2 py-0.5 font-mono text-[11px] text-shell-muted">
                  {r.location}
                </span>
              ),
              width: "90px",
            },
            {
              key: "actions",
              header: "Actions",
              render: (r) => (
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => startEdit(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => setClonePal(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Clone
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleExportPal(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Export
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRequestDeletePreview(r)}
                    className="border border-red-200 bg-white px-2 py-1 text-[11px] font-medium text-red-600 hover:bg-red-50 active:translate-y-[1px]"
                  >
                    Delete
                  </button>
                </div>
              ),
              width: "220px",
            },
          ]}
          rows={filtered}
          rowKey={(r) => r.instanceId}
          searchValue={query}
          onSearchChange={setQuery}
          searchPlaceholder="Filter by species, nickname, or instance ID…"
          emptyHeadline="No Pals found in this location."
          emptyDescription="Switch locations or clear the search filter to see more Pals."
        />

        {/* Edit Pal Drawer */}
        {selectedPal && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Edit Pal — {selectedPal.speciesId}
                </h3>
                <p className="font-mono text-xs text-shell-muted">{selectedPal.instanceId}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPal(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-4">
              <label className="grid gap-1 text-xs font-medium">
                <span>Nickname</span>
                <input
                  type="text"
                  value={editNickname}
                  onChange={(e) => setEditNickname(e.target.value)}
                  placeholder="Custom name"
                  className="border border-shell-line px-3 py-1.5 text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Level ({editCheatMode ? "1–60" : "1–55"})</span>
                <input
                  type="number"
                  min={1}
                  max={editCheatMode ? 60 : 55}
                  value={editLevel}
                  onChange={(e) => setEditLevel(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Gender</span>
                <select
                  value={editGender}
                  onChange={(e) => setEditGender(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 text-xs"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Condenser Rank (Stars 0–4)</span>
                <input
                  type="number"
                  min={0}
                  max={4}
                  value={editRank}
                  onChange={(e) => setEditRank(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Soul Upgrades (0–30)</span>
                <input
                  type="number"
                  min={0}
                  max={30}
                  value={editSouls}
                  onChange={(e) => setEditSouls(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>IV HP (0–100%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={editIvHp}
                  onChange={(e) => setEditIvHp(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>IV Attack (0–100%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={editIvAtk}
                  onChange={(e) => setEditIvAtk(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>IV Defense (0–100%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={editIvDef}
                  onChange={(e) => setEditIvDef(Number(e.target.value))}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            {/* Passives & Flags */}
            <div className="mt-4 grid gap-4 border-t border-shell-line pt-4 sm:grid-cols-2">
              <label className="grid gap-1 text-xs font-medium">
                <span>Passive Skills (comma-separated)</span>
                <input
                  type="text"
                  value={editPassives.join(", ")}
                  onChange={(e) =>
                    setEditPassives(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    )
                  }
                  placeholder="e.g. Legend, Musclehead, Ferocious, Swift"
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1 text-xs font-medium">
                <span>Active Skills (comma-separated)</span>
                <input
                  type="text"
                  value={editActives.join(", ")}
                  onChange={(e) =>
                    setEditActives(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    )
                  }
                  placeholder="e.g. GroundPunch, Earthquake, SolarBeam"
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-3 flex flex-wrap gap-4 text-xs font-medium">
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={editBoss}
                  onChange={(e) => setEditBoss(e.target.checked)}
                />
                <span>Boss / Alpha Pal</span>
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={editLucky}
                  onChange={(e) => setEditLucky(e.target.checked)}
                />
                <span>Lucky / Shiny Pal</span>
              </label>
              <label className="flex items-center gap-1.5 text-amber-800">
                <input
                  type="checkbox"
                  checked={editCheatMode}
                  onChange={(e) => setEditCheatMode(e.target.checked)}
                />
                <span>Cheat Mode (Permit Over-Cap Values)</span>
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setSelectedPal(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleRequestEditPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Preview Changes
              </button>
            </div>
          </div>
        )}

        {/* Diff Review & Auto-Backup Confirmation Modal */}
        <PreviewModal
          preview={activePreview}
          committing={committing}
          onCancel={() => {
            setActivePreview(null);
            setPendingCommit(null);
          }}
          onConfirm={handleConfirmCommit}
        />
      </div>
    </ViewShell>
  );
}
