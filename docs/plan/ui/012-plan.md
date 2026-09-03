# Plan 012 — Breeding

## Objective

Restyle the breeding reference calculator (parents/children explorer) as a readable
reference screen; it reads no save data, so risk is low and it can showcase the
component system.

## Scope

- `ui/tabs/breeding_tab.py` (554 ln), `_SelectPalDialog(PalCreateDialog)` consumer,
  `editor/pal_editor/create_dialogs.py` (selection-dialog chrome only here).

## Dependencies

Plans 002–004.

## Design

- Header: title + mode switch (Parents/Children) as segmented control (QSS
  `QToolButton` group with `checked` state), hint text secondary.
- Selector: PalIconLabel + change button; filter input (search component).
- Results: list rows — parent pair (icon+name mono species ids) → result icon+name,
  hover raise, click opens detail (existing behavior); results in a scrollable
  panel; debounce timer behavior kept.
- Empty: EmptyState ("Select a pal to see breeding combinations" — existing copy).
- `_SelectPalDialog`: BaseDialog scaffold over PalCreateDialog chrome (create dialogs
  fully covered in plan 016).

## Implementation tasks

1. Tokenize 19 inline styles; segmented control via property-based QSS.
2. Results rows via component factory; keep static breedingdata.json read path and
   icon cache helpers unchanged.

## Behavior-preservation requirements

- Breeding lookup (resources/game_data/breedingdata.json), icon paths, selection
  dialog reuse: unchanged.

## Tests and verification

- compileall + pytest (test_resource_integrity covers breeding data determinism);
  launch: select pal → results render; filter; switch modes.

## Visual QA requirements

Screenshot: results list, empty state; long species names (en + zh).

## Completion criteria

- Breeding screen tokenized; zero inline styles.

## Known risks

- None significant (no save data, no mutations).
