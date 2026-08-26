# Phase 14 — Inventory & Dynamic Containers

**Goal:** PST inventory parity (your Images 4-7).

**Source:** `palworld_aio/inventory/*` 6 files, `ui/tabs/{inventory,base_inventory}_tab.py`, `data/configs/inventory_loadouts.json`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 14.1 | `feat/inventory-equipment` | `W1-5 H1 B1 S1 A1-4 G1 F1-5 SM` lanes + `SINGLETON_TYPE_A` + locked states | `InventoryView` equipment panel |
| 14.2 | `feat/inventory-dynamic` | `DynamicItemManager UUID + durability`, `generate_dynamic_item_uuid`, `delete_orphaned_dynamic_items` | `dynamic_item` tests |
| 14.3 | `feat/inventory-slot-injector` | `modify_all_player_slots` `SlotNum` + `_SortableTableItem` + preview orphan sweep | slot injector preview |
| 14.4 | `feat/inventory-cross-guild` | `find_item_locations_efficient`, `remove_item_from_players` pct + rarity border `get_container_image_path` | cross-guild bulk dialog |

**Images:** 4 empty `Select a Guild/Base`, 5 container list `CommonDropItem3D`, 6 6×6 grid `Wood`, 7 full `Player Inventory Editor` 6-col + equipment.

**Outcome:** `CommonDropItem3D` fallback `?` with `ring-teal`, grid `Loadouts/Sort/Clear` polished.
