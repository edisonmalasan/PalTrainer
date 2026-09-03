# Plan 014 — Exclusions

## Objective

Restyle the Exclusions screen (deletion_exclusions / zone exclusion lists) as two
clear list management panes with add/remove flows intact.

## Scope

- `ui/main_window.py` `_setup_exclusions_tab` (uses two SearchPanels),
  `managers/zone_manager.py` persistence untouched, map-tab zone list interplay
  (visual only).

## Dependencies

Plans 002–004, 007 (SearchPanel restyle shared).

## Design

- Two stacked sections with SectionHeaders: "Deletion Exclusions" (protected entries
  from bulk deletes) and "Zone Exclusions" (map zones) — each a panel with its
  SearchPanel list, count badge, and footer actions (remove selected = danger ghost
  with confirm; add via existing flows).
- Empty states: "No exclusions configured" (neutral) — exclusions being empty is
  normal, not an error.
- Edits persist through `load_exclusions/save_exclusions` and `zone_manager`
  (files in user config dir) — untouched.

## Implementation tasks

1. Wrap panels; tokenize; wire count badges to list models (visual only).
2. Confirm dialogs via shared `confirm()`.

## Behavior-preservation requirements

- Exclusion persistence files, load/save timing, map-tab interplay unchanged.

## Tests and verification

- compileall + pytest; launch: add/remove a deletion exclusion (flow via search
  screens context menu) → appears here; zone exclusion roundtrip via map.

## Visual QA requirements

Screenshot: both sections populated + empty; long exclusion keys ellipsized.

## Completion criteria

- Exclusions tokenized; zero inline styles in the tab setup.

## Known risks

- Low; the tab is thin (built in main_window) — careful not to regress main_window
  import-time cost.
