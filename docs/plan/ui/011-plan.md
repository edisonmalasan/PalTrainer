# Plan 011 — Player Inventory

## Objective

Renovate the Player Inventory screen (4132 ln; 153 inline styles): equipment, item
grids, stats/missions/technology/palpedia panels, and its dialogs — onto shared
components with real empty states, preserving every inventory behavior.

## Scope

- `ui/tabs/inventory_tab.py`: ItemSlotWidget, EquipmentSlotWidget, StatsPanelWidget,
  MissionPanelWidget, TechnologyPanelWidget, PalpediaPanelWidget, InventoryGridWidget,
  RarityBorderDelegate, ItemPickerDialog, ModifyInventorySlotsDialog, QuantityDialog,
  InventoryLoadoutDialog, PlayerInventoryTab.
- `widgets/player_select_popup.py` (consumer restyle only).

## Dependencies

Plans 002–005; plan 010 (cross-tab selection sync already exercised).

## Design

- Header: title + player select button + loadouts ghost button.
- Sub-tabs (main grid / equipment / stats / missions / technology / palpedia): restyled
  QTabBar (underline accent, token padding); content panes = panels.
- Item grid: 48px icon cells, 84px pitch, rarity border delegate (shared), hover
  raise, selection accent, qty badges mono micro; context menus restyled.
- Equipment slots: rarity border + unlock state icon; unlock flow unchanged.
- Stats/missions/technology/palpedia panels: SectionHeader + form rows; progress
  bars tokenized (existing green chunk → success token); stats_changed/
  missions_changed/tech_changed signal contracts unchanged.
- Dialogs (ItemPicker, ModifySlots, Quantity, Loadouts): BaseDialog; picker grid
  shared with base inventory pickers; qty input mono, error property on overflow
  (validation logic unchanged, MAX_QUANTITY contract kept).
- Empty: EmptyState with player-select action; action buttons row (Unlock All Map,
  Loadouts, Clear, Modify Slots) as footer with kind-appropriate variants
  (Unlock All Map stays primary; Clear = danger ghost w/ confirm).

## Implementation tasks

1. Migrate pane-by-pane: header+tabs → grid → equipment → panels → dialogs.
2. Replace 153 inline styles; keep objectNames used by global QSS until plan 018.
3. Preserve multi-select deletion flows' signals (`multi_delete_requested`, etc.).

## Behavior-preservation requirements

- All inventory mutations via inventory_manager/player_manager unchanged; direct WSD
  reads stay read-only in UI; save writes via player_manager; unlock_all_map_requested
  contract; loadouts (JSON in user config) untouched.

## Tests and verification

- compileall + pytest; launch with fixture save: select player, add/remove/qty-edit
  items, equipment swap, stats edit, missions, technology add/remove, palpedia view,
  loadout save/load, modify slots, unlock map.

## Visual QA requirements

Screenshots: grid populated/empty, equipment, dialogs; tooltip overflow (long item
names); 100% zoom density.

## Completion criteria

- ≤5 inline styles remaining (dynamic icon paths); all dialogs on scaffold.

## Known risks

- Largest inline-QSS count — highest regression surface; pane-by-pane with launch
  checks. Grid performance with many items: avoid per-cell widgets where possible.
