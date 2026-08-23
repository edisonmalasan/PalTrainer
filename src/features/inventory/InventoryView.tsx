import { useCallback, useState } from "react";
import { DataTable } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  InventoryProjection,
  InventorySlotProjection,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function InventoryView() {
  const state = useAsync(
    useCallback(
      () => invokeCommand<readonly InventoryProjection[]>("get_inventory"),
      [],
    ),
    [],
  );

  const inventories = state.status === "ok" ? state.data : [];
  const [selectedOwner, setSelectedOwner] = useState<string | null>(null);

  const activeInv =
    inventories.find((inv) => inv.ownerUid === selectedOwner) ??
    inventories[0] ??
    null;

  return (
    <ViewShell
      title="Inventory"
      subtitle="Item inventory per player character. Select an owner to browse slots."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4 lg:flex-row">
        {/* Owner selector */}
        <aside className="shrink-0 border border-shell-line bg-white lg:w-48">
          <p className="border-b border-shell-line px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-shell-muted">
            Owners ({inventories.length})
          </p>
          <ul>
            {inventories.map((inv) => (
              <li key={inv.ownerUid}>
                <button
                  type="button"
                  onClick={() => setSelectedOwner(inv.ownerUid)}
                  className={[
                    "w-full px-3 py-2 text-left font-mono text-xs transition",
                    activeInv?.ownerUid === inv.ownerUid
                      ? "bg-[#edf5f2] text-shell-ink"
                      : "text-shell-muted hover:bg-shell-panel",
                  ].join(" ")}
                >
                  {inv.ownerUid.slice(0, 14)}…
                  <span className="ml-1 text-[10px]">({inv.slots.length})</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* Slot table */}
        <div className="min-w-0 flex-1">
          {activeInv ? (
            <DataTable<InventorySlotProjection>
              columns={[
                { key: "slot", header: "Slot", render: (s) => s.slotIndex, width: "60px" },
                { key: "item", header: "Item ID", render: (s) => s.itemId || "—" },
                { key: "count", header: "Count", render: (s) => s.count, width: "70px" },
                {
                  key: "dur",
                  header: "Durability",
                  render: (s) =>
                    s.durability !== null ? s.durability.toFixed(1) : "—",
                  width: "100px",
                },
              ]}
              rows={activeInv.slots}
              rowKey={(s) => String(s.slotIndex)}
              emptyMessage="This inventory is empty."
            />
          ) : (
            <p className="border border-dashed border-shell-line p-6 text-center text-sm text-shell-muted">
              No inventory data. Load a save file first.
            </p>
          )}
        </div>
      </div>
    </ViewShell>
  );
}
