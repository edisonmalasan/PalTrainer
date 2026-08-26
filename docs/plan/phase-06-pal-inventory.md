# Phase 06 — Pal, Inventory & Container Editing

**Goal:** High-frequency editing exceeds PST capability with safer validation.

**Source:** `palworld_aio/editor/pal_editor/**` 15 files, `inventory/{inventory,base_inventory,dynamic_item}_manager.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 06.1 | `feat/pal-mutation-models` | `domain/pals/mutation.rs` DTOs (`IV 0-100`, `soul 0-30`, `rank 0-4`, `cheatMode` cap logic) | `pals/mutation` tests |
| 06.2 | `feat/pal-backend-commands` | `pal::preview/commit_update/create/import/clone/delete` | `pal.rs` preview |
| 06.3 | `feat/pal-editor-view` | `PalsView` 6 location tabs, 11-col table, drawers, pills | `pnpm test` PalsView |
| 06.4 | `feat/pal-bulk-operations` | `bulk_max/bulk_sync/delete-by-species` | `PalsView` bulk bar |
| 06.5 | `feat/inventory-mutation-models` | `inventory/mutation.rs` 6 DTOs + `clear/resize/bulk` | inventory tests |
| 06.6 | `feat/inventory-backend-commands` | `inventory::update/add/remove/clear/resize/bulk` | `inventory.rs` |
| 06.7 | `feat/inventory-editor-view` | `InventoryView` dual panel + drawers + grid | `InventoryView` |

**Skills:** `pal-trainer-pal-editor`, `pal-trainer-stat-formula`.

**Outcome:** Create/clone/export Pals across party/palbox/base/DPS/GPS; edit inventory slots.
