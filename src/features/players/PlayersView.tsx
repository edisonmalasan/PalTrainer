import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  MutationPreview,
  PlayerProjection,
  UpdatePlayerDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function PlayersView() {
  const [reloadKey, setReloadKey] = useState(0);

  const state = useAsync(
    useCallback(() => invokeCommand<readonly PlayerProjection[]>("get_players"), []),
    [reloadKey],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.displayName.toLowerCase().includes(q) || r.uid.toLowerCase().includes(q),
  );

  // Edit drawer state
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerProjection | null>(null);
  const [editForm, setEditForm] = useState<{
    nickname: string;
    level: number;
    hp: number;
    maxHp: number;
  }>({ nickname: "", level: 55, hp: 5000, maxHp: 5000 });

  // Preview & mutation state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function startEdit(player: PlayerProjection) {
    setSelectedPlayer(player);
    setEditForm({
      nickname: player.displayName || "",
      level: player.level,
      hp: player.hp,
      maxHp: player.maxHp,
    });
  }

  async function handleRequestEditPreview() {
    if (!selectedPlayer) return;
    const dto: UpdatePlayerDto = {
      uid: selectedPlayer.uid,
      nickname: editForm.nickname,
      level: Number(editForm.level),
      hp: Number(editForm.hp),
      maxHp: Number(editForm.maxHp),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_player", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_player", { dto });
        setActionMessage(`Updated player ${selectedPlayer.uid}`);
        setSelectedPlayer(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestDeletePreview(player: PlayerProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_player", { uid: player.uid });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_delete_player", { uid: player.uid });
        setActionMessage(`Queued deletion for player ${player.uid}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleBulkMaxPreview() {
    const uids = rows.map((p) => p.uid);
    if (uids.length === 0) return;

    try {
      const preview = await invokeCommand<MutationPreview>("preview_bulk_max_players", {
        dto: { uids },
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_bulk_max_players", { dto: { uids } });
        setActionMessage(`Maxed stats for ${uids.length} players`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleUnlockPreview(player: PlayerProjection, feature: "effigies" | "fast_travel") {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_unlock_player_features", {
        uid: player.uid,
        feature,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_unlock_player_features", { uid: player.uid, feature });
        setActionMessage(`Unlocked ${feature} for player ${player.uid}`);
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
      title="Players"
      subtitle="Inspect, edit, or manage player records with automatic backups and preview confirmation."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4">
        {/* Bulk Action Bar */}
        <div className="flex items-center justify-between border border-shell-line bg-white px-4 py-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-shell-muted">
              Bulk Management
            </p>
            <p className="mt-0.5 text-xs text-shell-muted">
              {rows.length} player{rows.length !== 1 ? "s" : ""} loaded
            </p>
          </div>
          <button
            type="button"
            disabled={rows.length === 0}
            onClick={() => void handleBulkMaxPreview()}
            className="border border-shell-accent bg-[#edf5f2] px-3 py-1.5 font-mono text-xs font-semibold text-shell-accent transition hover:bg-[#d9ede7] active:translate-y-[1px] disabled:opacity-50"
          >
            Max All Players (Lv 60)
          </button>
        </div>

        {actionMessage && (
          <div className="border border-shell-accent bg-[#edf5f2] px-4 py-2 text-xs font-mono text-shell-accent">
            {actionMessage}
          </div>
        )}

        {/* Players Table */}
        <DataTable
          columns={[
            {
              key: "uid",
              header: "UID",
              render: (r) => <span className="text-shell-muted">{r.uid.slice(0, 16)}…</span>,
              width: "180px",
            },
            {
              key: "name",
              header: "Name",
              render: (r) => <span className="font-semibold text-shell-ink">{r.displayName || "—"}</span>,
            },
            { key: "level", header: "Lv", render: (r) => r.level, width: "60px" },
            { key: "hp", header: "HP", render: (r) => `${r.hp} / ${r.maxHp}`, width: "110px" },
            {
              key: "host",
              header: "Host",
              render: (r) => (r.isHost ? <Badge color="accent">Host</Badge> : null),
              width: "70px",
            },
            {
              key: "actions",
              header: "Actions",
              render: (r) => (
                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => startEdit(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleUnlockPreview(r, "effigies")}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                    title="Unlock all Lifmunk Effigies"
                  >
                    Effigies
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleUnlockPreview(r, "fast_travel")}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                    title="Unlock all Fast Travel points"
                  >
                    Map
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
          rowKey={(r) => r.uid}
          searchValue={query}
          onSearchChange={setQuery}
          searchPlaceholder="Filter by name or UID…"
          emptyMessage="No players found. Load a save file first."
        />

        {/* Edit Player Drawer / Form */}
        {selectedPlayer && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Edit Player — {selectedPlayer.displayName || selectedPlayer.uid}
                </h3>
                <p className="font-mono text-xs text-shell-muted">UID: {selectedPlayer.uid}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPlayer(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Display Name</span>
                <input
                  type="text"
                  value={editForm.nickname}
                  onChange={(e) => setEditForm({ ...editForm, nickname: e.target.value })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>Level (1-60)</span>
                <input
                  type="number"
                  min={1}
                  max={60}
                  value={editForm.level}
                  onChange={(e) => setEditForm({ ...editForm, level: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>HP</span>
                <input
                  type="number"
                  value={editForm.hp}
                  onChange={(e) => setEditForm({ ...editForm, hp: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>Max HP</span>
                <input
                  type="number"
                  value={editForm.maxHp}
                  onChange={(e) => setEditForm({ ...editForm, maxHp: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setSelectedPlayer(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleRequestEditPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Preview & Apply
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

function Badge({ color, children }: { color: "accent" | "muted"; children: React.ReactNode }) {
  return (
    <span
      className={[
        "rounded-sm px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide",
        color === "accent"
          ? "bg-[#edf5f2] text-shell-accent"
          : "bg-shell-panel text-shell-muted",
      ].join(" ")}
    >
      {children}
    </span>
  );
}
