import { useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import type { MutationPreview, ResetParams, ResetTarget } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const RESET_OPTIONS: { id: ResetTarget; label: string; desc: string }[] = [
  {
    id: "dungeons",
    label: "Dungeon Timers & Lockouts",
    desc: "Clear active dungeon lockout timers and force immediate room re-generation.",
  },
  {
    id: "oil_rig",
    label: "Oil Rig Barriers & Chests",
    desc: "Reset high-tier loot chest locks, laser gate puzzles, and syndicate guard spawns.",
  },
  {
    id: "supply_drops",
    label: "Meteorite & Supply Drop Events",
    desc: "Trigger fresh supply drop and meteorite impact event cycles.",
  },
  {
    id: "invaders",
    label: "Base Raid & Invader Timers",
    desc: "Reset incoming enemy raid countdowns and enable immediate defense events.",
  },
  {
    id: "missions",
    label: "Boss & Tutorial Missions",
    desc: "Reset tutorial checklist steps, tower boss defeat flags, and daily mission progress.",
  },
  {
    id: "anti_air_turrets",
    label: "Anti-Air Defense Turrets",
    desc: "Reset missile battery targeting systems and cooldown flags on sanctuary turrets.",
  },
  {
    id: "lock_gimmicks",
    label: "Sanctuary & Door Lock Gimmicks",
    desc: "Reset sanctuary door lock switches, pressure plate puzzles, and keycard terminals.",
  },
];

export function ResetPanel() {
  const [selectedTargets, setSelectedTargets] = useState<Set<ResetTarget>>(
    new Set(["dungeons", "oil_rig", "supply_drops"]),
  );
  const [scopePlayerUid, setScopePlayerUid] = useState<string>("");

  const [preview, setPreview] = useState<MutationPreview | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<string | null>(null);

  const toggleTarget = (id: ResetTarget) => {
    setSelectedTargets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedTargets(new Set(RESET_OPTIONS.map((o) => o.id)));
  };

  const clearAll = () => {
    setSelectedTargets(new Set());
  };

  const handlePreview = async () => {
    if (selectedTargets.size === 0) {
      setError("Please select at least one world event or gimmick to reset.");
      return;
    }
    setError(null);
    setAuditResult(null);
    setLoading(true);
    try {
      const params: ResetParams = {
        targets: Array.from(selectedTargets),
        scopePlayerUid: scopePlayerUid.trim() || undefined,
      };

      const result = await invokeCommand<MutationPreview>("preview_reset", { params });
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
    setLoading(true);
    try {
      const params: ResetParams = {
        targets: Array.from(selectedTargets),
        scopePlayerUid: scopePlayerUid.trim() || undefined,
      };

      const committed = await invokeCommand<MutationPreview>("commit_reset", { params });
      setPreview(null);
      setAuditResult(
        `World events reset successfully. Created safety backup at '${committed.backupTarget ?? "automatic backup"}'. Updated ${committed.entitiesToModify.length} event subsystem(s).`,
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Alert banner */}
      <div className="rounded-xl border border-shell-line bg-shell-card p-4 text-xs leading-relaxed text-shell-ink">
        <p className="font-semibold uppercase tracking-wider text-shell-accent">
          World Event & Gimmick Reset Tool
        </p>
        <p className="mt-1 text-shell-muted">
          Select world events, dungeon lockouts, oil rig puzzles, or boss missions to reset back to their initial state. An automatic backup is created before saving changes.
        </p>
      </div>

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

      {/* Target Selector List */}
      <div className="rounded-xl border border-shell-line bg-shell-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-shell-line pb-3">
          <p className="font-mono text-xs font-semibold uppercase tracking-wider text-shell-muted">
            Select Events to Reset ({selectedTargets.size} selected)
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="font-mono text-xs text-shell-accent hover:underline"
            >
              Select All
            </button>
            <span className="text-shell-line">|</span>
            <button
              type="button"
              onClick={clearAll}
              className="font-mono text-xs text-shell-muted hover:text-shell-ink hover:underline"
            >
              Deselect All
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          {RESET_OPTIONS.map((opt) => {
            const isChecked = selectedTargets.has(opt.id);
            return (
              <label
                key={opt.id}
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition ${
                  isChecked
                    ? "border-shell-accent bg-shell-accent/10"
                    : "border-shell-line bg-shell-bg/40 hover:bg-shell-bg/70"
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleTarget(opt.id)}
                  className="mt-1 h-4 w-4 rounded border-shell-line text-shell-accent focus:ring-shell-accent"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-shell-ink">{opt.label}</span>
                  <span className="mt-1 text-xs text-shell-muted">{opt.desc}</span>
                </div>
              </label>
            );
          })}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-shell-line pt-4">
          <div className="w-full max-w-sm">
            <label htmlFor="scope-reset-player-uid" className="block font-mono text-xs text-shell-muted">
              Scope Player UID (Optional):
            </label>
            <input
              id="scope-reset-player-uid"
              type="text"
              placeholder="Leave empty for world-wide reset"
              value={scopePlayerUid}
              onChange={(e) => setScopePlayerUid(e.target.value)}
              className="mt-1 w-full rounded-lg border border-shell-line bg-shell-bg px-3 py-1.5 font-mono text-xs text-shell-ink placeholder:text-shell-muted/50 focus:border-shell-accent focus:outline-none"
            />
          </div>

          <button
            type="button"
            disabled={loading || selectedTargets.size === 0}
            onClick={handlePreview}
            className="flex items-center gap-2 rounded-lg bg-shell-accent px-5 py-2.5 text-xs font-semibold text-shell-ink shadow-sm transition hover:bg-shell-accent/90 disabled:opacity-50 active:scale-[0.98]"
          >
            {loading ? "Preparing Preview..." : `Preview Reset (${selectedTargets.size} Targets)`}
          </button>
        </div>
      </div>

      {preview && (
        <PreviewModal
          preview={preview}
          onConfirm={handleCommit}
          onCancel={() => setPreview(null)}
        />
      )}
    </div>
  );
}
