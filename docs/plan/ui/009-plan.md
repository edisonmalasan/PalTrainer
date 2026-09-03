# Plan 009 — Base Inventory

## Objective

Renovate the Base Inventory screen (guild/base selection → container list → item
grids → base pals) — the worst inline-QSS offender (123 sites) — onto shared
components without touching container/pal domain logic.

## Scope

- `ui/tabs/base_inventory_tab.py` (4176 ln), reusing `inventory_tab` shared helpers
  (InventoryGridWidget, ItemPickerDialog, InventoryLoadoutDialog — restyled in plan 011),
  `inventory/base_inventory_manager.py` untouched.

## Dependencies

Plans 002–005 (components, dialogs); coordinates with plan 011 for shared widgets
(InventoryGridWidget restyle lands in 011; this plan consumes it).

## Design

### Layout
- Header: title + guild/base selector combo (styled_combo) + economy stats tool button.
- Three-pane: container list tree (left, 260px default) | container info + item grid
  (center) | optional info panel (right, collapsible). Splitter sizes persist via
  existing mechanism if present; defaults from tokens.
- Base working-pals gallery: icon grid with hover tooltips; right-click menu restyle.

### Components
- ContainerListWidget: dense tree, badges for item counts, selected = accent.
- Item grids: rarity borders via shared `RarityBorderDelegate`; slot styles from
  `styles.slot_*` regenerated from tokens; hover raise (border+bg, no shadow).
- Pickers (GuildItemPickerDialog, GuildStructurePickerDialog): BaseDialog + shared
  grids; signals unchanged (`item_action_selected`, `structure_action_selected`).
- ReplaceStructureDialog (`replacement_confirmed`), ContainerSlotModificationDialog,
  EconomyStatsDialog: BaseDialog scaffold; forms via field helpers; validation state
  via ErrorBanner (same logic).

### States
- Empty: EmptyState per pane ("Select a Guild/Base", "No containers", "Container
  empty") — replaces mixed placeholder QLabels; loading: existing data paths are
  synchronous-fast; keep spinner header for slow ops only.

## Implementation tasks

1. Extract pane builders; delete ~123 inline styles; objectNames preserved where
   global QSS still matches them.
2. Wire shared delegates/pickers; token slot styles.
3. Keep direct WSD reads (read-only in UI) and manager mutations unchanged.

## Behavior-preservation requirements

- All container reads/mutations, slot modification, structure replacement, economy
  stats, base pals ops unchanged; right-click menus identical actions.

## Tests and verification

- compileall + pytest (incl. test_base_manager, test_read_models); launch with
  fixture save: select guild/base, open containers, edit item qty (QuantityDialog),
  replace structure, modify slots, view economy.

## Visual QA requirements

Screenshots: three-pane view, picker dialog, rarity grid hover/selected, empty state.
Density check at 100% zoom (many items).

## Completion criteria

- ≤5 inline setStyleSheet remaining in file (icon-path dynamic styles only).

## Known risks

- Largest file in repo — migrate pane-by-pane with compile+launch between panes.
- Shared widgets come from inventory_tab; sequence 011's grid restyle to avoid
  double churn (this plan styles containers/delegates, 011 the grids).
