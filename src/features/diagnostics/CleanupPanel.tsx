import { useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { WarningBanner } from "../../shared/components/WarningBanner";
import type { CleanupParams, CleanupTarget, MutationPreview } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const CLEANUP_TARGETS: {
  id: CleanupTarget;
  label: string;
  desc: string;
  danger: "low" | "medium" | "high";
}[] = [
  {
    id: "empty_guilds",
    label: "Empty Guilds",
    desc: "Disband guilds with 0 members and 0 active bases.",
    danger: "low",
  },
  {
    id: "inactive_players",
    label: "Inactive Players",
    desc: "Purge player save files and unbind character data inactive beyond threshold.",
    danger: "high",
  },
  {
    id: "duplicate_players",
    label: "Duplicate Player Saves",
    desc: "Canonicalize duplicate IndividualId entries and delete stale body clones.",
    danger: "medium",
  },
  {
    id: "unreferenced_data",
    label: "Unreferenced Records",
    desc: "Purge orphaned character maps and orphaned item containers.",
    danger: "low",
  },
  {
    id: "non_base_map_objects",
    label: "Non-Base Map Objects",
    desc: "Delete player-placed structures outside registered base territory radii.",
    danger: "medium",
  },
  {
    id: "invalid_structure_objects",
    label: "Invalid Structures",
    desc: "Purge corrupted structures with missing models or broken connector links.",
    danger: "medium",
  },
  {
    id: "all_skins",
    label: "All Character & Pal Skins",
    desc: "Clear custom skin attachments and revert all characters to default base models.",
    danger: "low",
  },
  {
    id: "imported_dna_pals",
    label: "Imported / DNA Pals",
    desc: "Delete Pals flagged with imported DNA metadata from external save transfers.",
    danger: "high",
  },
  {
    id: "invalid_items",
    label: "Invalid / Modded Items",
    desc: "Purge unrecognized StaticItemIds from all inventories and storage containers.",
    danger: "medium",
  },
  {
    id: "invalid_pals",
    label: "Invalid Pal Species",
    desc: "Delete Pals with unrecognized CharacterIds not matching base game species.",
    danger: "high",
  },
  {
    id: "invalid_passives",
    label: "Invalid Passives & Skills",
    desc: "Strip unindexed and invalid passive skill strings across all loaded Pals.",
    danger: "low",
  },
];

export function CleanupPanel() {
  const [selectedTarget, setSelectedTarget] = useState<CleanupTarget>("empty_guilds");
  const [inactivityDays, setInactivityDays] = useState<number>(30);
  const [protectDeathBags, setProtectDeathBags] = useState<boolean>(true);
  const [scopePlayerUid, setScopePlayerUid] = useState<string>("");

  const [preview, setPreview] = useState<MutationPreview | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [committing, setCommitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<string | null>(null);

  const handlePreview = async () => {
    setError(null);
    setAuditResult(null);
    setLoading(true);
    try {
      const params: CleanupParams = {
        target: selectedTarget,
        inactivityDaysThreshold:
          selectedTarget === "inactive_players" ? Number(inactivityDays) : undefined,
        protectDeathBags,
        scopePlayerUid: scopePlayerUid.trim() || undefined,
      };

      const result = await invokeCommand<MutationPreview>("preview_cleanup", { params });
      setPreview(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;
    setError(null);
    setCommitting(true);
    try {
      const params: CleanupParams = {
        target: selectedTarget,
        inactivityDaysThreshold:
          selectedTarget === "inactive_players" ? Number(inactivityDays) : undefined,
        protectDeathBags,
        scopePlayerUid: scopePlayerUid.trim() || undefined,
      };

      const committed = await invokeCommand<MutationPreview>("commit_cleanup", { params });
      setPreview(null);
      setAuditResult(
        `Cleanup successful. Backup created at '${committed.backupTarget ?? "automatic backup"}'. Modified ${committed.filesToModify.length} file(s) and deleted ${committed.filesToDelete.length} file(s).`,
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Alert banner */}
      <WarningBanner
        severity="warning"
        badge="SAFE SERVER & WORLD MAINTENANCE"
        title="Automated Pre-Mutation Backups"
        description="All cleanup actions automatically generate a full compressed backup before touching save data. Destructive operations require confirmation in the preview diff modal."
      />

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-xs text-red-400">
          {error}
        </div>
      )}

      {auditResult && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 font-mono text-xs text-emerald-400">
          {auditResult}
        </div>
      )}

      {/* Target Selector Grid */}
      <div>
        <p className="font-mono text-xs font-semibold uppercase tracking-wider text-shell-muted">
          Select Cleanup Target:
        </p>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {CLEANUP_TARGETS.map((t) => {
            const isSelected = selectedTarget === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setSelectedTarget(t.id)}
                className={`flex flex-col rounded-xl border p-4 text-left transition ${
                  isSelected
                    ? "border-shell-accent bg-shell-accent/10 shadow-sm"
                    : "border-shell-line bg-shell-card hover:border-shell-line/80 hover:bg-shell-bg/40"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-shell-ink text-xs">{t.label}</span>
                  <span
                    className={`rounded px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide font-bold ${
                      t.danger === "high"
                        ? "bg-red-500/20 text-red-400"
                        : t.danger === "medium"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-emerald-500/20 text-emerald-400"
                    }`}
                  >
                    {t.danger} risk
                  </span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-shell-muted">{t.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Configuration Parameters */}
      <div className="rounded-xl border border-shell-line bg-shell-card p-5">
        <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-shell-muted">
          Operation Settings
        </h3>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          {selectedTarget === "inactive_players" && (
            <div>
              <label htmlFor="inactivity-days-input" className="block font-mono text-xs text-shell-muted">
                Inactivity Threshold (Days):
              </label>
              <input
                id="inactivity-days-input"
                type="number"
                min={1}
                max={365}
                value={inactivityDays}
                onChange={(e) => setInactivityDays(Number(e.target.value))}
                className="mt-1.5 w-full rounded-lg border border-shell-line bg-shell-bg px-3 py-1.5 font-mono text-xs text-shell-ink focus:border-shell-accent focus:outline-none"
              />
            </div>
          )}

          <div>
            <label htmlFor="scope-player-uid-input" className="block font-mono text-xs text-shell-muted">
              Scope Player UID (Optional):
            </label>
            <input
              id="scope-player-uid-input"
              type="text"
              placeholder="Leave empty for all players"
              value={scopePlayerUid}
              onChange={(e) => setScopePlayerUid(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-shell-line bg-shell-bg px-3 py-1.5 font-mono text-xs text-shell-ink placeholder:text-shell-muted/50 focus:border-shell-accent focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-3 pt-6">
            <input
              type="checkbox"
              id="protectDeathBags"
              checked={protectDeathBags}
              onChange={(e) => setProtectDeathBags(e.target.checked)}
              className="h-4 w-4 rounded border-shell-line text-shell-accent focus:ring-shell-accent"
            />
            <label htmlFor="protectDeathBags" className="text-xs text-shell-ink">
              Protect Death Penalty Containers
            </label>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            disabled={loading}
            onClick={handlePreview}
            className="flex items-center gap-2 rounded-lg bg-shell-accent px-5 py-2.5 text-xs font-semibold text-shell-ink shadow-sm transition hover:bg-shell-accent/90 disabled:opacity-50 active:scale-[0.98]"
          >
            {loading ? "Preparing Preview..." : `Preview ${CLEANUP_TARGETS.find((t) => t.id === selectedTarget)?.label} Cleanup`}
          </button>
        </div>
      </div>

      {preview && (
        <PreviewModal
          preview={preview}
          committing={committing}
          onConfirm={handleCommit}
          onCancel={() => setPreview(null)}
        />
      )}
    </div>
  );
}
