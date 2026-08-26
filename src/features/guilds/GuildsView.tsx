import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  GuildProjection,
  MutationPreview,
  TransferGuildAdminDto,
  UpdateGuildDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function GuildsView() {
  const [reloadKey, setReloadKey] = useState(0);

  const state = useAsync(
    useCallback(() => invokeCommand<readonly GuildProjection[]>("get_guilds"), []),
    [reloadKey],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.name.toLowerCase().includes(q) || r.guildId.toLowerCase().includes(q),
  );

  // Edit drawer state
  const [selectedGuild, setSelectedGuild] = useState<GuildProjection | null>(null);
  const [editName, setEditName] = useState("");

  // Transfer leadership dialog
  const [transferTargetGuild, setTransferTargetGuild] = useState<GuildProjection | null>(null);
  const [newAdminUid, setNewAdminUid] = useState("");

  // Preview & mutation state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function startEdit(guild: GuildProjection) {
    setSelectedGuild(guild);
    setEditName(guild.name || "");
  }

  async function handleRequestEditPreview() {
    if (!selectedGuild) return;
    const dto: UpdateGuildDto = {
      guildId: selectedGuild.guildId,
      name: editName,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_guild", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_guild", { dto });
        setActionMessage(`Updated guild ${selectedGuild.guildId}`);
        setSelectedGuild(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleTransferAdminPreview() {
    if (!transferTargetGuild || !newAdminUid.trim()) return;
    const dto: TransferGuildAdminDto = {
      guildId: transferTargetGuild.guildId,
      newAdminUid: newAdminUid.trim(),
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_transfer_guild_admin", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_transfer_guild_admin", { dto });
        setActionMessage(`Transferred admin of guild ${transferTargetGuild.guildId} to ${newAdminUid}`);
        setTransferTargetGuild(null);
        setNewAdminUid("");
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleUnlockLabResearchPreview(guild: GuildProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_unlock_all_lab_research", {
        guildId: guild.guildId,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_unlock_all_lab_research", { guildId: guild.guildId });
        setActionMessage(`Unlocked all lab research for guild ${guild.name || guild.guildId}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestDeletePreview(guild: GuildProjection) {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_delete_guild", {
        guildId: guild.guildId,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_delete_guild", { guildId: guild.guildId });
        setActionMessage(`Disbanded guild ${guild.guildId}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleDisbandEmptyPreview() {
    try {
      const preview = await invokeCommand<MutationPreview>("preview_disband_empty_guilds");
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_disband_empty_guilds");
        setActionMessage(`Disbanded empty guilds (${count} cleaned up)`);
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
      title="Guilds"
      subtitle="Guild memberships, leadership, and base ownership with safe preview and backup protections."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4">
        {/* Bulk Action Bar */}
        <div className="flex items-center justify-between border border-shell-line bg-white px-4 py-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-shell-muted">
              Guild Management
            </p>
            <p className="mt-0.5 text-xs text-shell-muted">
              {rows.length} guild{rows.length !== 1 ? "s" : ""} registered
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleDisbandEmptyPreview()}
            className="border border-shell-line bg-white px-3 py-1.5 font-mono text-xs text-shell-muted transition hover:bg-shell-panel active:translate-y-[1px]"
          >
            Clean Empty Guilds (0 Members)
          </button>
        </div>

        {actionMessage && (
          <div className="border border-shell-accent bg-[#edf5f2] px-4 py-2 text-xs font-mono text-shell-accent">
            {actionMessage}
          </div>
        )}

        {/* Guilds Table */}
        <DataTable
          columns={[
            {
              key: "id",
              header: "Guild ID",
              render: (r) => <span className="text-shell-muted">{r.guildId.slice(0, 16)}…</span>,
              width: "180px",
            },
            {
              key: "name",
              header: "Guild Name",
              sortable: true,
              sortValue: (r) => r.name || r.guildId,
              render: (r) => <span className="font-semibold text-shell-ink">{r.name || "—"}</span>,
            },
            {
              key: "members",
              header: "Members",
              sortable: true,
              sortValue: (r) => r.members.length,
              render: (r) => r.members.length,
              width: "90px",
            },
            {
              key: "bases",
              header: "Bases",
              sortable: true,
              sortValue: (r) => r.baseCount,
              render: (r) => r.baseCount,
              width: "70px",
            },
            {
              key: "admin",
              header: "Admin Player",
              render: (r) => (
                <span className="text-shell-muted">
                  {r.adminPlayerName || r.adminPlayerUid.slice(0, 8)}
                </span>
              ),
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
                    onClick={() => void handleUnlockLabResearchPreview(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                    title="Unlock All Lab Research"
                  >
                    Lab
                  </button>
                  <button
                    type="button"
                    onClick={() => setTransferTargetGuild(r)}
                    className="border border-shell-line bg-white px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                  >
                    Transfer
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRequestDeletePreview(r)}
                    className="border border-red-200 bg-white px-2 py-1 text-[11px] font-medium text-red-600 hover:bg-red-50 active:translate-y-[1px]"
                  >
                    Disband
                  </button>
                </div>
              ),
              width: "220px",
            },
          ]}
          rows={filtered}
          rowKey={(r) => r.guildId}
          searchValue={query}
          onSearchChange={setQuery}
          searchPlaceholder="Filter by guild name or ID…"
          emptyHeadline="No guilds found"
          emptyDescription="Load a Palworld save directory in Save Session to view registered guilds and bases."
        />

        {/* Edit Guild Drawer */}
        {selectedGuild && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Edit Guild — {selectedGuild.name || selectedGuild.guildId}
                </h3>
                <p className="font-mono text-xs text-shell-muted">ID: {selectedGuild.guildId}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedGuild(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Guild Name</span>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setSelectedGuild(null)}
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

        {/* Transfer Leadership Dialog */}
        {transferTargetGuild && (
          <div className="border border-shell-line bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Transfer Leadership — {transferTargetGuild.name || transferTargetGuild.guildId}
                </h3>
                <p className="font-mono text-xs text-shell-muted">Current Admin: {transferTargetGuild.adminPlayerUid}</p>
              </div>
              <button
                type="button"
                onClick={() => setTransferTargetGuild(null)}
                className="text-xs text-shell-muted hover:text-shell-ink"
              >
                Close
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>New Admin Player UID</span>
                <input
                  type="text"
                  placeholder="e.g. 00000000000000000000000000000001"
                  value={newAdminUid}
                  onChange={(e) => setNewAdminUid(e.target.value)}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
              <button
                type="button"
                onClick={() => setTransferTargetGuild(null)}
                className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!newAdminUid.trim()}
                onClick={() => void handleTransferAdminPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px] disabled:opacity-50"
              >
                Preview & Transfer
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
