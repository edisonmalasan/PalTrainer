import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { EmptyState } from "../../shared/components/EmptyState";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  AddItemDto,
  BulkAddKeyItemsDto,
  ClearContainerDto,
  InventoryProjection,
  InventorySlotProjection,
  MutationPreview,
  ResizeContainerDto,
  UpdateInventorySlotDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const SINGLETON_TYPE_A = "SingletonA";

const EQUIPMENT_LANES: readonly {
  readonly id: string;
  readonly label: string;
  readonly slotIndex: number;
  readonly category: string;
}[] = [
  { id: "W1", label: "Weapon 1", slotIndex: 0, category: "Weapon" },
  { id: "W2", label: "Weapon 2", slotIndex: 1, category: "Weapon" },
  { id: "W3", label: "Weapon 3", slotIndex: 2, category: "Weapon" },
  { id: "W4", label: "Weapon 4", slotIndex: 3, category: "Weapon" },
  { id: "W5", label: "Weapon 5", slotIndex: 4, category: "Weapon" },
  { id: "H1", label: "Head", slotIndex: 5, category: "Armor" },
  { id: "B1", label: "Body", slotIndex: 6, category: "Armor" },
  { id: "S1", label: "Shield", slotIndex: 7, category: "Armor" },
  { id: "A1", label: "Accessory 1", slotIndex: 8, category: "Accessory" },
  { id: "A2", label: "Accessory 2", slotIndex: 9, category: "Accessory" },
  { id: "A3", label: "Accessory 3", slotIndex: 10, category: "Accessory" },
  { id: "A4", label: "Accessory 4", slotIndex: 11, category: "Accessory" },
  { id: "G1", label: "Glider", slotIndex: 12, category: "Glider" },
  { id: "F1", label: "Food 1", slotIndex: 13, category: "Food" },
  { id: "F2", label: "Food 2", slotIndex: 14, category: "Food" },
  { id: "F3", label: "Food 3", slotIndex: 15, category: "Food" },
  { id: "F4", label: "Food 4", slotIndex: 16, category: "Food" },
  { id: "F5", label: "Food 5", slotIndex: 17, category: "Food" },
  { id: "SM", label: "Shield Module", slotIndex: 18, category: "Module" },
];

function isEquipmentContainer(containerType: string): boolean {
  return containerType === SINGLETON_TYPE_A || containerType.toLowerCase().includes("equipment") || containerType.toLowerCase().includes("singleton");
}

function isSlotLocked(slotIndex: number, containerCapacity: number): boolean {
  return slotIndex >= containerCapacity;
}

export function InventoryView() {
  const [reloadKey, setReloadKey] = useState(0);

  const state = useAsync(
    useCallback(
      () => invokeCommand<readonly InventoryProjection[]>("get_inventory"),
      [],
    ),
    [reloadKey],
  );

  const inventories = state.status === "ok" ? state.data : [];
  const [selectedOwner, setSelectedOwner] = useState<string | null>(null);

  const activeInv =
    inventories.find(
      (inv) => inv.ownerId === selectedOwner || inv.ownerUid === selectedOwner,
    ) ??
    inventories[0] ??
    null;

  const activeOwnerId = activeInv ? activeInv.ownerId || activeInv.ownerUid || "" : "";
  const activeContainerId = activeInv ? activeInv.containerId || "main_inventory" : "main_inventory";

  const { query, setQuery, filtered } = useSearchFilter(
    activeInv ? activeInv.slots : [],
    (s, q) => s.itemId.toLowerCase().includes(q) || String(s.slotIndex).includes(q),
  );

  // Edit Slot Drawer state
  const [selectedSlot, setSelectedSlot] = useState<InventorySlotProjection | null>(null);
  const [editItemId, setEditItemId] = useState("");
  const [editCount, setEditCount] = useState(1);
  const [editDurability, setEditDurability] = useState<number | null>(null);

  // Add Item Drawer state
  const [showAddDrawer, setShowAddDrawer] = useState(false);
  const [newItemId, setNewItemId] = useState("PalSphere_Mega");
  const [newCount, setNewCount] = useState(100);
  const [newDurability, setNewDurability] = useState<number | null>(null);

  // Resize Modal state
  const [showResizeModal, setShowResizeModal] = useState(false);
  const [newCapacity, setNewCapacity] = useState(120);

  // Bulk Key Items state
  const [showKeyItemsModal, setShowKeyItemsModal] = useState(false);
  const [addEffigies, setAddEffigies] = useState(true);
  const [addTechManuals, setAddTechManuals] = useState(true);
  const [addAncientCores, setAddAncientCores] = useState(true);

  // Preview & Mutation commit state
  const [activePreview, setActivePreview] = useState<MutationPreview | null>(null);
  const [pendingCommit, setPendingCommit] = useState<(() => Promise<void>) | null>(null);
  const [committing, setCommitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function startEditSlot(slot: InventorySlotProjection) {
    setSelectedSlot(slot);
    setEditItemId(slot.itemId);
    setEditCount(slot.count);
    setEditDurability(slot.durability);
  }

  async function handleRequestEditSlotPreview() {
    if (!selectedSlot || !editItemId.trim()) return;
    const dto: UpdateInventorySlotDto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
      slotIndex: selectedSlot.slotIndex,
      itemId: editItemId.trim(),
      count: editCount,
      durability: editDurability ?? undefined,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_inventory_slot", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_inventory_slot", { dto });
        setActionMessage(`Updated slot ${selectedSlot.slotIndex} (${editItemId})`);
        setSelectedSlot(null);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestQuickMaxStack(slot: InventorySlotProjection) {
    const dto: UpdateInventorySlotDto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
      slotIndex: slot.slotIndex,
      itemId: slot.itemId,
      count: 9999,
      durability: slot.durability ?? undefined,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_update_inventory_slot", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_update_inventory_slot", { dto });
        setActionMessage(`Set slot ${slot.slotIndex} count to 9,999`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestAddItemPreview() {
    if (!newItemId.trim()) return;
    const dto: AddItemDto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
      itemId: newItemId.trim(),
      count: newCount,
      durability: newDurability ?? undefined,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_add_item", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_add_item", { dto });
        setActionMessage(`Added ${newCount}x ${newItemId} to inventory`);
        setShowAddDrawer(false);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestRemoveSlotPreview(slot: InventorySlotProjection) {
    const dto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
      slotIndex: slot.slotIndex,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_remove_item", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_remove_item", { dto });
        setActionMessage(`Removed item from slot ${slot.slotIndex}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestClearContainerPreview() {
    const dto: ClearContainerDto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_clear_container", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_clear_container", { dto });
        setActionMessage(`Cleared all items in container ${activeContainerId}`);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestResizePreview() {
    const dto: ResizeContainerDto = {
      ownerUid: activeOwnerId,
      containerId: activeContainerId,
      newCapacity,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_resize_container", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        await invokeCommand("commit_resize_container", { dto });
        setActionMessage(`Resized container capacity to ${newCapacity} slots`);
        setShowResizeModal(false);
        setReloadKey((k) => k + 1);
      });
    } catch (err: unknown) {
      setActionMessage(String(err));
    }
  }

  async function handleRequestBulkKeyItemsPreview() {
    const items: string[] = [];
    if (addEffigies) items.push("Relic_Lifmunk_100");
    if (addTechManuals) {
      items.push("TechnologyBook_G1_50");
      items.push("TechnologyBook_G2_50");
      items.push("TechnologyBook_G3_50");
    }
    if (addAncientCores) items.push("AncientTechnologyCore_20");

    const dto: BulkAddKeyItemsDto = {
      playerUid: activeOwnerId,
      keyItemIds: items,
    };

    try {
      const preview = await invokeCommand<MutationPreview>("preview_bulk_add_key_items", { dto });
      setActivePreview(preview);
      setPendingCommit(() => async () => {
        const count = await invokeCommand<number>("commit_bulk_add_key_items", { dto });
        setActionMessage(`Added ${count} key items / books to player ${activeOwnerId}`);
        setShowKeyItemsModal(false);
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
      title="Inventory"
      subtitle="Player inventories, base chests, and key items with slot editing, stack maxing, and container resizing."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-4 lg:flex-row">
        {/* Owner Selector Side Panel */}
        <aside className="shrink-0 border border-shell-line bg-shell-surface lg:w-56">
          <p className="border-b border-shell-line px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-shell-muted">
            Containers ({inventories.length})
          </p>
          <ul className="divide-y divide-shell-line">
            {inventories.map((inv) => {
              const id = inv.ownerId || inv.ownerUid || "Unknown";
              const isSelected = activeOwnerId === id;
              return (
                <li key={`${id}-${inv.containerId}`}>
                  <button
                    type="button"
                    onClick={() => setSelectedOwner(id)}
                    className={[
                      "w-full px-3 py-2 text-left font-mono text-xs transition",
                      isSelected
                        ? "bg-shell-accent-subtle font-semibold text-shell-accent"
                        : "text-shell-muted hover:bg-shell-panel hover:text-shell-ink",
                    ].join(" ")}
                  >
                    <div>{id.slice(0, 14)}…</div>
                    <div className="mt-0.5 text-[10px] text-shell-muted">
                      {inv.containerType || "Player"} · {inv.slots.length} / {inv.slotCapacity || 64} slots
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        {/* Main Content Area */}
        <div className="min-w-0 flex-1 flex flex-col gap-4">
          {/* Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border border-shell-line bg-shell-surface p-3">
            <div>
              <p className="text-xs font-semibold text-shell-ink">
                {activeInv?.containerType || "Player Inventory"} ({activeOwnerId.slice(0, 16)}…)
              </p>
              <p className="font-mono text-[11px] text-shell-muted">
                {activeInv?.slots.length ?? 0} filled slots (Capacity: {activeInv?.slotCapacity ?? 64})
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setShowAddDrawer(true)}
                className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-3 py-1.5 font-mono text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px]"
              >
                + Add Item
              </button>
              <button
                type="button"
                onClick={() => setShowKeyItemsModal(true)}
                className="border border-shell-line bg-shell-surface px-3 py-1.5 font-mono text-xs text-shell-ink hover:bg-shell-panel active:translate-y-[1px]"
              >
                Bulk Key Items
              </button>
              <button
                type="button"
                onClick={() => setShowResizeModal(true)}
                className="border border-shell-line bg-shell-surface px-3 py-1.5 font-mono text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
              >
                Resize
              </button>
              <button
                type="button"
                onClick={() => void handleRequestClearContainerPreview()}
                className="border border-shell-destructive/40 bg-shell-surface px-3 py-1.5 font-mono text-xs text-shell-destructive hover:bg-shell-destructive-subtle active:translate-y-[1px]"
              >
                Clear
              </button>
            </div>
          </div>

          {actionMessage && (
            <div className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-2 font-mono text-xs text-shell-accent">
              {actionMessage}
            </div>
          )}

          {/* Add Item Drawer */}
          {showAddDrawer && (
            <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
              <h3 className="text-base font-semibold">Add Item to Inventory</h3>
              <p className="mt-1 text-xs text-shell-muted">
                Specify item ID, stack quantity, and durability.
              </p>

              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <label className="grid gap-1 text-xs font-medium">
                  <span>Item ID</span>
                  <input
                    type="text"
                    value={newItemId}
                    onChange={(e) => setNewItemId(e.target.value)}
                    placeholder="e.g. PalSphere_Mega, Meat_Chicken"
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>

                <label className="grid gap-1 text-xs font-medium">
                  <span>Quantity</span>
                  <input
                    type="number"
                    min={1}
                    max={9999}
                    value={newCount}
                    onChange={(e) => setNewCount(Number(e.target.value))}
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>

                <label className="grid gap-1 text-xs font-medium">
                  <span>Durability (Optional)</span>
                  <input
                    type="number"
                    value={newDurability ?? ""}
                    onChange={(e) =>
                      setNewDurability(e.target.value ? Number(e.target.value) : null)
                    }
                    placeholder="e.g. 1000"
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>
              </div>

              <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddDrawer(false)}
                  className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!newItemId.trim()}
                  onClick={() => void handleRequestAddItemPreview()}
                  className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px] disabled:opacity-50"
                >
                  Preview Add
                </button>
              </div>
            </div>
          )}

          {/* Resize Container Modal */}
          {showResizeModal && (
            <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
              <h3 className="text-base font-semibold">Resize Container Slot Capacity</h3>
              <p className="mt-1 text-xs text-shell-muted">
                Expand or shrink the maximum number of inventory slots (current: {activeInv?.slotCapacity ?? 64}).
              </p>

              <div className="mt-4 max-w-xs">
                <label className="grid gap-1 text-xs font-medium">
                  <span>New Slot Limit (up to 500)</span>
                  <input
                    type="number"
                    min={10}
                    max={500}
                    value={newCapacity}
                    onChange={(e) => setNewCapacity(Number(e.target.value))}
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>
              </div>

              <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
                <button
                  type="button"
                  onClick={() => setShowResizeModal(false)}
                  className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void handleRequestResizePreview()}
                  className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px]"
                >
                  Preview Resize
                </button>
              </div>
            </div>
          )}

          {/* Bulk Key Items Modal */}
          {showKeyItemsModal && (
            <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
              <h3 className="text-base font-semibold">Bulk Add Key & Tech Items</h3>
              <p className="mt-1 text-xs text-shell-muted">
                Fast-track progression by adding full sets of progression items directly to inventory.
              </p>

              <div className="mt-4 flex flex-col gap-2.5 text-xs font-medium">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={addEffigies}
                    onChange={(e) => setAddEffigies(e.target.checked)}
                  />
                  <span>Lifmunk Effigies (x100 for max capture power)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={addTechManuals}
                    onChange={(e) => setAddTechManuals(e.target.checked)}
                  />
                  <span>High Quality & Ancient Technical Manuals (x150 total)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={addAncientCores}
                    onChange={(e) => setAddAncientCores(e.target.checked)}
                  />
                  <span>Ancient Technology Cores (x20)</span>
                </label>
              </div>

              <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
                <button
                  type="button"
                  onClick={() => setShowKeyItemsModal(false)}
                  className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void handleRequestBulkKeyItemsPreview()}
                  className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px]"
                >
                  Preview Add Key Items
                </button>
              </div>
            </div>
          )}

          {/* Equipment Lanes — PST parity for W1-5/H1/B1/S1/A1-4/G1/F1-5/SM */}
          {activeInv && isEquipmentContainer(activeInv.containerType) && (
            <div className="border border-shell-line bg-shell-surface p-3">
              <div className="flex items-center justify-between">
                <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                  Equipment — {activeInv.containerType}
                  <span className="ml-2 font-mono text-[10px] normal-case tracking-normal text-shell-muted">
                    Singleton: single item per slot with durability
                  </span>
                </p>
                <span className="font-mono text-[10px] text-shell-muted">
                  {activeInv.slots.length}/{activeInv.slotCapacity} equipped
                </span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
                {EQUIPMENT_LANES.map((lane) => {
                  const slot = activeInv.slots.find((s) => s.slotIndex === lane.slotIndex);
                  const locked = isSlotLocked(lane.slotIndex, activeInv.slotCapacity);
                  return (
                    <div
                      key={lane.id}
                      className={[
                        "relative flex flex-col gap-1 border p-2.5 transition",
                        locked
                          ? "border-shell-line bg-shell-panel opacity-40"
                          : slot
                            ? "border-shell-accent/40 bg-shell-accent-subtle hover:border-shell-accent"
                            : "border-shell-line bg-shell-panel hover:border-shell-line hover:bg-shell-surface",
                      ].join(" ")}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="rounded bg-shell-surface px-1.5 py-0.5 font-mono text-[10px] font-semibold tracking-wide text-shell-accent">
                          {lane.id}
                        </span>
                        {locked ? (
                          <span className="font-mono text-[9px] uppercase tracking-wide text-shell-muted">Locked</span>
                        ) : (
                          <span className="font-mono text-[9px] text-shell-muted">{lane.category}</span>
                        )}
                      </div>
                      <p className="truncate text-xs font-medium leading-tight">{lane.label}</p>
                      {locked ? (
                        <p className="font-mono text-[10px] text-shell-muted">Reach higher level</p>
                      ) : slot ? (
                        <div className="mt-1 min-w-0">
                          <p className="truncate font-mono text-xs font-semibold text-shell-ink">{slot.itemId || "—"}</p>
                          <p className="font-mono text-[10px] text-shell-muted">
                            x{slot.count.toLocaleString()}
                            {slot.durability !== null ? ` · ${slot.durability.toFixed(0)} dur` : ""}
                          </p>
                        </div>
                      ) : (
                        <p className="mt-1 font-mono text-[10px] text-shell-muted">Empty</p>
                      )}
                      {!locked && slot && (
                        <button
                          type="button"
                          onClick={() => startEditSlot(slot)}
                          className="mt-1 border border-shell-line bg-white px-2 py-1 text-center font-mono text-[10px] hover:bg-shell-panel active:translate-y-[1px]"
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Slot Table */}
          {activeInv ? (
            <DataTable<InventorySlotProjection>
              columns={[
                {
                  key: "slot",
                  header: "Slot",
                  sortable: true,
                  sortValue: (s) => s.slotIndex,
                  render: (s) => <span className="font-mono text-xs text-shell-muted">#{s.slotIndex}</span>,
                  width: "60px",
                },
                {
                  key: "item",
                  header: "Item ID",
                  sortable: true,
                  sortValue: (s) => s.itemId,
                  render: (s) => (
                    <div>
                      <span className="font-semibold text-shell-ink">{s.itemId || "—"}</span>
                      {s.durability !== null && (
                        <div className="font-mono text-[10px] text-shell-muted">
                          Durability: {s.durability.toFixed(0)}
                        </div>
                      )}
                    </div>
                  ),
                },
                {
                  key: "count",
                  header: "Count",
                  sortable: true,
                  sortValue: (s) => s.count,
                  render: (s) => (
                    <span className="font-mono font-semibold text-shell-ink">
                      x{s.count.toLocaleString()}
                    </span>
                  ),
                  width: "90px",
                },
                {
                  key: "actions",
                  header: "Actions",
                  render: (s) => (
                    <div className="flex gap-1.5">
                      <button
                        type="button"
                        onClick={() => startEditSlot(s)}
                        className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium hover:bg-shell-panel active:translate-y-[1px]"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleRequestQuickMaxStack(s)}
                        className="border border-shell-line bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                      >
                        Max (x9999)
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleRequestRemoveSlotPreview(s)}
                        className="border border-shell-destructive/40 bg-shell-surface px-2 py-1 text-[11px] font-medium text-shell-destructive hover:bg-shell-destructive-subtle active:translate-y-[1px]"
                      >
                        Remove
                      </button>
                    </div>
                  ),
                },
              ]}
              rows={filtered}
              rowKey={(s) => String(s.slotIndex)}
              searchValue={query}
              onSearchChange={setQuery}
              searchPlaceholder="Filter items by ID or slot index…"
              emptyHeadline="Container is empty"
              emptyDescription="This container currently holds no items. Use '+ Add Item' or 'Add Key Items Pack' to populate slots."
            />
          ) : (
            <EmptyState
              headline="No inventory container selected"
              description="Load a Palworld save directory in Save Session to view player or chest inventories."
            />
          )}

          {/* Edit Slot Drawer */}
          {selectedSlot && (
            <div className="border border-shell-line bg-shell-surface p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-shell-line pb-3">
                <h3 className="text-base font-semibold">
                  Edit Slot #{selectedSlot.slotIndex}
                </h3>
                <button
                  type="button"
                  onClick={() => setSelectedSlot(null)}
                  className="text-xs text-shell-muted hover:text-shell-ink"
                >
                  Close
                </button>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <label className="grid gap-1 text-xs font-medium">
                  <span>Item ID</span>
                  <input
                    type="text"
                    value={editItemId}
                    onChange={(e) => setEditItemId(e.target.value)}
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>

                <label className="grid gap-1 text-xs font-medium">
                  <span>Quantity</span>
                  <input
                    type="number"
                    min={1}
                    max={9999}
                    value={editCount}
                    onChange={(e) => setEditCount(Number(e.target.value))}
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>

                <label className="grid gap-1 text-xs font-medium">
                  <span>Durability (Optional)</span>
                  <input
                    type="number"
                    value={editDurability ?? ""}
                    onChange={(e) =>
                      setEditDurability(e.target.value ? Number(e.target.value) : null)
                    }
                    placeholder="e.g. 1000"
                    className="border border-shell-line px-3 py-1.5 font-mono text-xs"
                  />
                </label>
              </div>

              <div className="mt-4 flex justify-end gap-2 border-t border-shell-line pt-3">
                <button
                  type="button"
                  onClick={() => setSelectedSlot(null)}
                  className="border border-shell-line px-3 py-1.5 text-xs text-shell-muted hover:bg-shell-panel active:translate-y-[1px]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!editItemId.trim()}
                  onClick={() => void handleRequestEditSlotPreview()}
                  className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-4 py-1.5 text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px] disabled:opacity-50"
                >
                  Preview Changes
                </button>
              </div>
            </div>
          )}

          {/* Preview & Confirmation Modal */}
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
      </div>
    </ViewShell>
  );
}
