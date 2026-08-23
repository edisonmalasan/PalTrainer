import { useCallback, useState } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  BreedingLookupResult,
  GameCatalog,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function BreedingView() {
  const catalogState = useAsync(
    useCallback(() => invokeCommand<GameCatalog>("get_game_catalog"), []),
    [],
  );

  const [parent1, setParent1] = useState("");
  const [parent2, setParent2] = useState("");
  const [result, setResult] = useState<BreedingLookupResult | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);

  const catalog = catalogState.status === "ok" ? catalogState.data : null;

  async function handleLookup() {
    if (!parent1.trim() || !parent2.trim()) return;
    setLooking(true);
    setLookupError(null);
    setResult(null);
    try {
      const res = await invokeCommand<BreedingLookupResult>("lookup_breeding", {
        parent1Id: parent1.trim(),
        parent2Id: parent2.trim(),
      });
      setResult(res);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String((err as { message: unknown }).message)
            : "Lookup failed";
      setLookupError(msg);
    } finally {
      setLooking(false);
    }
  }

  return (
    <ViewShell
      title="Breeding Calculator"
      subtitle="Look up the child Pal for any two parent species using the game formula."
      status={catalogState.status}
      errorMessage={
        catalogState.status === "error" ? catalogState.message : undefined
      }
    >
      <div className="flex flex-col gap-6">
        {/* Input area */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <PalSelect
            id="parent1"
            label="Parent 1"
            value={parent1}
            onChange={setParent1}
            catalog={catalog}
          />
          <PalSelect
            id="parent2"
            label="Parent 2"
            value={parent2}
            onChange={setParent2}
            catalog={catalog}
          />
          <button
            id="btn-breeding-lookup"
            type="button"
            disabled={looking || !parent1 || !parent2}
            onClick={() => void handleLookup()}
            className={[
              "border px-4 py-2 text-sm font-medium transition active:translate-y-[1px]",
              looking || !parent1 || !parent2
                ? "cursor-not-allowed border-shell-line text-shell-muted opacity-60"
                : "border-shell-accent bg-[#edf5f2] text-shell-accent hover:bg-[#d9ede7]",
            ].join(" ")}
          >
            {looking ? "Looking up…" : "Look up child"}
          </button>
        </div>

        {/* Error */}
        {lookupError && (
          <p className="border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {lookupError}
          </p>
        )}

        {/* Result */}
        {result && (
          <div className="border border-shell-line bg-white p-5">
            <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
              Result
            </p>
            <p className="mt-3 text-2xl font-semibold tracking-tight text-shell-ink">
              {result.childName || result.childPalId}
            </p>
            <p className="mt-1 font-mono text-xs text-shell-muted">
              {result.childPalId}
            </p>
            {result.isUniqueCombo && (
              <span className="mt-3 inline-block rounded-sm bg-amber-50 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-amber-700">
                Unique Combo
              </span>
            )}
            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-shell-line pt-4 font-mono text-xs text-shell-muted">
              <div>
                <p className="uppercase tracking-wide">Parent 1</p>
                <p className="mt-1 text-shell-ink">{result.parent1}</p>
              </div>
              <div>
                <p className="uppercase tracking-wide">Parent 2</p>
                <p className="mt-1 text-shell-ink">{result.parent2}</p>
              </div>
            </div>
          </div>
        )}

        {/* Catalog summary */}
        {catalog && (
          <div className="border-t border-shell-line pt-4">
            <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
              Game Catalog
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: "Pals", value: catalog.pals.length },
                { label: "Items", value: catalog.items.length },
                { label: "Passives", value: catalog.passives.length },
                { label: "Skills", value: catalog.activeSkills.length },
              ].map((entry) => (
                <div
                  key={entry.label}
                  className="border border-shell-line bg-white px-3 py-3"
                >
                  <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                    {entry.label}
                  </p>
                  <p className="mt-1 font-mono text-lg font-semibold text-shell-ink">
                    {entry.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ViewShell>
  );
}

function PalSelect({
  id,
  label,
  value,
  onChange,
  catalog,
}: {
  readonly id: string;
  readonly label: string;
  readonly value: string;
  readonly onChange: (v: string) => void;
  readonly catalog: GameCatalog | null;
}) {
  return (
    <label className="grid gap-2 text-sm" htmlFor={id}>
      <span className="font-medium">{label}</span>
      {catalog ? (
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="border border-shell-line bg-white px-3 py-2 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-shell-accent"
        >
          <option value="">— Select a Pal —</option>
          {catalog.pals.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.id})
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Pal ID (e.g. Lamball)"
          className="border border-shell-line bg-white px-3 py-2 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-shell-accent"
        />
      )}
    </label>
  );
}
