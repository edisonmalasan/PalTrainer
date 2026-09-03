# Plan 016 — Dialogs & Pickers (Item / Pal / Tech / Guild / Fix / Conversion)

## Objective

Unify all modal surfaces on the shared dialog system: the five bulk-action dialogs,
editor dialogs/pickers (create dialogs, SkillPicker, GPS/worldoption editors),
and tool option dialogs — with danger flows visually distinct and lifecycles safe.

## Scope

- `ui/dialogs/`: player_item_dialog (778 ln), player_pal_dialog (541 ln),
  player_technology_dialog (395 ln), guild_assign_dialog (done in 007 — verify),
  fix_illegal_pal_dialog, fix_illegal_player_dialog, skill_picker, tab_guide_dialog (done in 015).
- `editor/dialogs.py` (InputDialog, DaysInputDialog, LevelInputDialog, RadiusInputDialog,
  PalDefenderDialog, GameDaysInputDialog, InactiveFilterDialog),
  `editor/pal_editor/create_dialogs.py` (94 inline styles), `editor/gps_editor.py`,
  `editor/worldoption_editor.py`.
- `ui/tabs/tools_tab.ConversionOptionsDialog` (verify from 005).
- `ui/tabs/inventory_tab` / `base_inventory_tab` dialogs (done in 009/011 — verify).

## Dependencies

Plans 002–005. Runs after 007/009/010/011 land their own dialogs.

## Design

- All dialogs: `BaseDialog` scaffold (title bar, content, footer buttons), min sizes
  preserved per dialog, Esc/Enter semantics, parent-owned; no frameless hacks except
  where popups need them (SkillPicker stays a QWidget popup, restyled only).
- Grid delegates (RarityBorderDelegate, PalSlotDelegate, tech tiles): token palettes;
  tech tile QSS pasted 4× in technology dialog → single class.
- Fix dialogs: severity-first design — result rows as Badge (illegal count), actions
  as danger primary; `fix_requested` signal flows unchanged; pal-fix dialog returns
  selection via a proper public method (add `selected_uids()` public accessor
  alongside `_get_selected_uids`, callers migrate — no behavior change).
- SkillPicker: restyle to tokens; keep rank gradients as game-contract colors;
  keep blocking `pick()` loop (documented; do not change control flow here).
- player_select_popup: restyle; keep blocking loop.
- Domain violations to fix while touching: `player_technology_dialog` performs
  `sav_to_gvasfile/gvasfile_to_sav` writes inside the dialog → move read/write into
  `managers/player_manager` (new function `add_technologies_for_players` /
  `remove_technologies_for_players`), dialog calls manager only. Same pattern check
  for `player_item_dialog` save reads on GUI thread → route through existing
  `run_with_loading` off-thread helper (behavior-preserving, no new workers design).

## Implementation tasks

1. Scaffold each dialog; replace 100+ inline styles across the group.
2. Extract technology write logic to player_manager with unit tests (behavior-preserving).
3. Token palettes for all delegates; passive-card font-size regex hack
  (`_shrink_passive_text` editing its own stylesheet) → property-based size variants.
4. Public accessor + caller updates for fix_illegal_pal selection.

## Behavior-preservation requirements

- Every dialog's result contract (signals/return values) unchanged; all manager
  mutations unchanged (except relocation of tech writes into the manager — same
  operations, same file formats, covered by new unit tests).
- No widget-tree mutation during `exec()` (defer refreshes).

## Tests and verification

- compileall + pytest incl. new player_manager tech tests; launch: run each dialog
  against fixture save copies — add/remove technology, item/pal bulk actions, guild
  assign, both fix flows, skill picker, all editor input dialogs.

## Visual QA requirements

Screenshots: each dialog populated + empty; danger confirmations; ru_RU/zh_CN labels.

## Completion criteria

- No dialog hand-builds its chrome; scanner violations reduced to whitelist files.

## Known risks

- Technology-write relocation is the only logic move in the overhaul — keep it
  surgical with tests; if it shows drift, revert to dialog-local calls and record
  the debt honestly in PROGRESS.md.
