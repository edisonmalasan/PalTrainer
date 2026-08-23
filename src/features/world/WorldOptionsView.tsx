import { useCallback, useState } from "react";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  MutationPreview,
  WorldMetadataDto,
  WorldOptionsDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function WorldOptionsView() {
  const [reloadKey, setReloadKey] = useState(0);

  const optionsState = useAsync(
    useCallback(() => invokeCommand<WorldOptionsDto>("get_world_options"), []),
    [reloadKey],
  );

  const metaState = useAsync(
    useCallback(() => invokeCommand<WorldMetadataDto>("get_world_meta"), []),
    [reloadKey],
  );

  // Form states
  const [formOptions, setFormOptions] = useState<WorldOptionsDto | null>(null);
  const [formMeta, setFormMeta] = useState<WorldMetadataDto | null>(null);

  // Synchronize state once loaded
  if (optionsState.status === "ok" && formOptions === null) {
    setFormOptions(optionsState.data);
  }
  if (metaState.status === "ok" && formMeta === null) {
    setFormMeta(metaState.data);
  }

  // Preview & mutation state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  async function handleRequestOptionsPreview() {
    if (!formOptions) return;
    try {
      const preview = await invokeCommand<MutationPreview>("preview_save_world_options", {
        options: formOptions,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_save_world_options", { options: formOptions });
        setActionMessage("Updated WorldOption.sav");
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestMetaPreview() {
    if (!formMeta) return;
    try {
      const preview = await invokeCommand<MutationPreview>("preview_save_world_meta", {
        meta: formMeta,
      });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_save_world_meta", { meta: formMeta });
        setActionMessage("Updated LevelMeta.sav");
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
      title="World Options & Metadata"
      subtitle="Modify WorldOption.sav multipliers, death penalties, and LevelMeta.sav game days."
      status={optionsState.status === "loading" ? "loading" : optionsState.status}
      errorMessage={optionsState.status === "error" ? optionsState.message : undefined}
    >
      <div className="flex flex-col gap-6">
        {actionMessage && (
          <div className="border border-shell-accent bg-[#edf5f2] px-4 py-2 font-mono text-xs text-shell-accent">
            {actionMessage}
          </div>
        )}

        {/* World Metadata Section */}
        {formMeta && (
          <div className="border border-shell-line bg-white p-5">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">World Metadata (LevelMeta.sav)</h3>
                <p className="mt-0.5 text-xs text-shell-muted">World name and in-game day counter.</p>
              </div>
              <button
                type="button"
                onClick={() => void handleRequestMetaPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 font-mono text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Save Metadata
              </button>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-3">
              <label className="grid gap-1.5 text-xs font-medium">
                <span>World Name</span>
                <input
                  type="text"
                  value={formMeta.worldName}
                  onChange={(e) => setFormMeta({ ...formMeta, worldName: e.target.value })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>In-Game Days</span>
                <input
                  type="number"
                  min={1}
                  value={formMeta.gameDays}
                  onChange={(e) => setFormMeta({ ...formMeta, gameDays: Number(e.target.value) })}
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>

              <label className="grid gap-1.5 text-xs font-medium">
                <span>In-Game Time (Seconds)</span>
                <input
                  type="number"
                  min={0}
                  step={60}
                  value={formMeta.inGameTimeSeconds}
                  onChange={(e) =>
                    setFormMeta({ ...formMeta, inGameTimeSeconds: Number(e.target.value) })
                  }
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
            </div>
          </div>
        )}

        {/* World Option Multipliers Section */}
        {formOptions && (
          <div className="border border-shell-line bg-white p-5">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">Gameplay Multipliers (WorldOption.sav)</h3>
                <p className="mt-0.5 text-xs text-shell-muted">
                  Custom rates for EXP, Pal capture, egg incubation, and penalty settings.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleRequestOptionsPreview()}
                className="border border-shell-accent bg-[#edf5f2] px-4 py-1.5 font-mono text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px]"
              >
                Save World Options
              </button>
            </div>

            <div className="mt-4 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {/* EXP Rate */}
              <label className="grid gap-1.5 text-xs font-medium">
                <div className="flex justify-between">
                  <span>EXP Multiplier</span>
                  <span className="font-mono text-shell-accent">{formOptions.expRate.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="20"
                  step="0.1"
                  value={formOptions.expRate}
                  onChange={(e) =>
                    setFormOptions({ ...formOptions, expRate: Number(e.target.value) })
                  }
                  className="accent-shell-accent"
                />
              </label>

              {/* Pal Capture Rate */}
              <label className="grid gap-1.5 text-xs font-medium">
                <div className="flex justify-between">
                  <span>Capture Rate Multiplier</span>
                  <span className="font-mono text-shell-accent">
                    {formOptions.palCaptureRate.toFixed(1)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5"
                  step="0.1"
                  value={formOptions.palCaptureRate}
                  onChange={(e) =>
                    setFormOptions({ ...formOptions, palCaptureRate: Number(e.target.value) })
                  }
                  className="accent-shell-accent"
                />
              </label>

              {/* Pal Spawn Rate */}
              <label className="grid gap-1.5 text-xs font-medium">
                <div className="flex justify-between">
                  <span>Pal Spawn Number Multiplier</span>
                  <span className="font-mono text-shell-accent">
                    {formOptions.palSpawnNumRate.toFixed(1)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={formOptions.palSpawnNumRate}
                  onChange={(e) =>
                    setFormOptions({ ...formOptions, palSpawnNumRate: Number(e.target.value) })
                  }
                  className="accent-shell-accent"
                />
              </label>

              {/* Egg Hatching Time */}
              <label className="grid gap-1.5 text-xs font-medium">
                <div className="flex justify-between">
                  <span>Egg Default Hatching Time</span>
                  <span className="font-mono text-shell-accent">
                    {formOptions.palEggDefaultHatchingTime.toFixed(1)}h
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="72"
                  step="0.5"
                  value={formOptions.palEggDefaultHatchingTime}
                  onChange={(e) =>
                    setFormOptions({
                      ...formOptions,
                      palEggDefaultHatchingTime: Number(e.target.value),
                    })
                  }
                  className="accent-shell-accent"
                />
              </label>

              {/* Death Penalty */}
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Death Penalty</span>
                <select
                  value={formOptions.deathPenalty}
                  onChange={(e) =>
                    setFormOptions({ ...formOptions, deathPenalty: e.target.value })
                  }
                  className="border border-shell-line px-3 py-1.5 text-xs"
                >
                  <option value="None">None (No loss)</option>
                  <option value="Item">Item only (Keep equipment & Pals)</option>
                  <option value="ItemAndEquipment">Item & Equipment (Standard)</option>
                  <option value="All">All (Drop items, equipment & all Pals)</option>
                </select>
              </label>

              {/* Max Guild Players */}
              <label className="grid gap-1.5 text-xs font-medium">
                <span>Guild Max Player Count</span>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={formOptions.guildPlayerMaxNum}
                  onChange={(e) =>
                    setFormOptions({
                      ...formOptions,
                      guildPlayerMaxNum: Number(e.target.value),
                    })
                  }
                  className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                />
              </label>
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
