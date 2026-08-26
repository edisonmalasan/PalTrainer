import { useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import type { MutationPreview, RepairParams, RepairTarget } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const REPAIR_TARGETS: {
  id: RepairTarget;
  label: string;
  desc: string;
  category: "Pals" | "World" | "Players" | "Containers";
}[] = [
  {
    id: "structures",
    label: "Damaged Base Structures",
    desc: "Restore 100% HP and durability to damaged defense walls, work benches, and base structures.",
    category: "World",
  },
  {
    id: "items",
    label: "Equipment & Tool Durability",
    desc: "Restore max durability to weapons, armor, gliders, and shield items in all inventories.",
    category: "Containers",
  },
  {
    id: "pals",
    label: "Pal Sickness & Sanity",
    desc: "Clear fracture/depression sicknesses, restore sanity to 100, and max out fullness across party & base workers.",
    category: "Pals",
  },
  {
    id: "illegal_pals",
    label: "Normalize Illegal Pal Stats",
    desc: "Clamp out-of-bounds IVs (0..100), condenser rank (0..4), and soul bonuses to legal boundaries.",
    category: "Pals",
  },
  {
    id: "illegal_players",
    label: "Normalize Player Tech Points",
    desc: "Clamp unassigned stat points and illegal technology point balances to level caps.",
    category: "Players",
  },
  {
    id: "invalid_active_skills",
    label: "Clean Invalid Active Skills",
    desc: "Strip unobtainable, duplicate, or corrupted active skills from Pal loadouts.",
    category: "Pals",
  },
  {
    id: "overfilled_inventories",
    label: "Trim Overfilled Containers",
    desc: "Consolidate duplicate stacks and trim orphaned slot indices above container capacity.",
    category: "Containers",
  },
  {
    id: "guilds",
    label: "Rebuild Guild Member Indices",
    desc: "Re-index guild rosters against registered player files and fix broken admin GUID pointers.",
    category: "World",
  },
  {
    id: "timestamps",
    label: "Synchronize Desynced Timestamps",
    desc: "Reset out-of-order player login timestamps to match the current WorldSaveData clock.",
    category: "Players",
  },
  {
    id: "unassigned_pals",
    label: "Reassign Orphaned Base Workers",
    desc: "Restore missing BaseCampId linkages for worker Pals stationed in active base territories.",
    category: "Pals",
  },
  {
    id: "dynamic_containers",
    label: "Repair Dynamic Container Links",
    desc: "Re-establish broken DynamicItemId registrations for egg incubators and viewing cages.",
    category: "Containers",
  },
  {
    id: "private_chests",
    label: "Unlock Private Chests (Booth Locks)",
    desc: "Clear password byte hashes and private booth lock flags using valid binary semantics.",
    category: "Containers",
  },
];

export function RepairPanel() {
  const [selectedTarget, setSelectedTarget] = useState<RepairTarget>("structures");
  const [autoHeal, setAutoHeal] = useState<boolean>(true);
  const [clampStats, setClampStats] = useState<boolean>(true);
  const [scopeEntityId, setScopeEntityId] = useState<string>("");

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
      const params: RepairParams = {
        target: selectedTarget,
        scopeEntityId: scopeEntityId.trim() || undefined,
        autoHeal,
        clampStats,
      };

      const result = await invokeCommand<MutationPreview>("preview_repair", { params });
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
      const params: RepairParams = {
        target: selectedTarget,
        scopeEntityId: scopeEntityId.trim() || undefined,
        autoHeal,
        clampStats,
      };

      const committed = await invokeCommand<MutationPreview>("commit_repair", { params });
      setPreview(null);
      setAuditResult(
        `Repair successful. Created safety backup at '${committed.backupTarget ?? "automatic backup"}'. Modified ${committed.entitiesToModify.length} entity category record(s).`,
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
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs leading-relaxed text-emerald-300">
        <p className="font-semibold uppercase tracking-wider text-emerald-400">
          Save Integrity & State Restoration
        </p>
        <p className="mt-1 text-shell-muted">
          Repair operations restore corrupted data structures, normalize illegal stats, repair damaged base objects, and fix booth lock byte semantics while strictly preserving raw data tails.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-shell-destructive/20 bg-shell-destructive-subtle0/10 p-4 text-xs text-shell-destructive">
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
          Select Repair Operation:
        </p>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {REPAIR_TARGETS.map((t) => {
            const isSelected = selectedTarget === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setSelectedTarget(t.id)}
                className={`flex flex-col rounded-xl border p-4 text-left transition ${
                  isSelected
                    ? "border-shell-accent-solid bg-shell-accent-solid/10 shadow-sm"
                    : "border-shell-line bg-shell-card hover:border-shell-line/80 hover:bg-shell-bg/40"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-shell-ink text-xs">{t.label}</span>
                  <span className="rounded bg-shell-bg px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide text-shell-muted">
                    {t.category}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-shell-muted">{t.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Configuration Settings */}
      <div className="rounded-xl border border-shell-line bg-shell-card p-5">
        <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-shell-muted">
          Repair Parameters
        </h3>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <label htmlFor="scope-entity-input" className="block font-mono text-xs text-shell-muted">
              Scope Target / Entity ID (Optional):
            </label>
            <input
              id="scope-entity-input"
              type="text"
              placeholder="Leave empty for global save scope"
              value={scopeEntityId}
              onChange={(e) => setScopeEntityId(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-shell-line bg-shell-bg px-3 py-1.5 font-mono text-xs text-shell-ink placeholder:text-shell-muted/50 focus:border-shell-accent focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-3 pt-6">
            <input
              type="checkbox"
              id="autoHeal"
              checked={autoHeal}
              onChange={(e) => setAutoHeal(e.target.checked)}
              className="h-4 w-4 rounded border-shell-line text-shell-accent focus:ring-shell-accent"
            />
            <label htmlFor="autoHeal" className="text-xs text-shell-ink">
              Auto-Heal Sanity & Conditions
            </label>
          </div>

          <div className="flex items-center gap-3 pt-6">
            <input
              type="checkbox"
              id="clampStats"
              checked={clampStats}
              onChange={(e) => setClampStats(e.target.checked)}
              className="h-4 w-4 rounded border-shell-line text-shell-accent focus:ring-shell-accent"
            />
            <label htmlFor="clampStats" className="text-xs text-shell-ink">
              Enforce Strict Legal Thresholds
            </label>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            disabled={loading}
            onClick={handlePreview}
            className="flex items-center gap-2 rounded-lg bg-shell-accent-solid px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-shell-accent-solid-hover disabled:opacity-50 active:scale-[0.98]"
          >
            {loading ? "Preparing Preview..." : `Preview ${REPAIR_TARGETS.find((t) => t.id === selectedTarget)?.label}`}
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
