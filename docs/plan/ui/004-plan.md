> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 004 — Application Shell & Navigation

## Objective

Renovate the shell: header (save-state aware), sidebar (grouped, keyboard-navigable),
splitter layout, drop overlay, status/console chrome — the frame every screen lives in.

## Scope

- `ui/chrome/header_widget.py`, `ui/chrome/sidebar_widget.py`,
  `ui/main_window.py` (shell parts only: chrome wiring, splitters, drop overlay),
  `widgets/menu_popup.py`, `ui/chrome/results_widget.py` (chrome only),
  `tools_tab.DropOverlay`.

## Dependencies

Plans 002, 003.

## Design

### Header (48px, level-1 surface, 1px bottom outline)
- Left: logo (44px→28px scaled) + app name; menu chip (neutral, accent on hover).
- Center-right: **Save State chip** driven by `ShellStateModel` via save_manager
  signals — NO_SAVE (muted dot), LOADING (spinner glyph, existing animation),
  LOADED (success dot + path tooltip), DIRTY (warning dot + "unsaved"),
  SAVING (spinner), ERROR (danger dot). Chip is a `Badge`, property-driven.
- Right: warnings, guide, about, save (primary kind, `dirty` property already
  supported), update pulse (warning-color on version chip), discord, loading spinner;
  then a 1px separator; then window controls (minimize/maximize/close as neutral
  chips; close uses danger hover). Version/game-version chips become neutral
  (accent only on update pulse).
- Heights/padding from tokens; all glyphs from `chrome/icons.py`.

### Sidebar (200px expanded / 48px collapsed)
- Sections with micro-uppercase labels (expanded only):
  **Load & Inspect**: Tools, Map Viewer; **World Data**: Base Inventory, Players,
  Guilds, Bases, Exclusions; **Editing**: Player Inventory, Pal Editor, JSON Editor;
  **Reference**: Breeding, Docs.
  (Sidebar entry order preserved: same page ids, same indexes — grouping is labels.)
- Items: 36px rows, icon 16px + 11px label, hover surface, active = accent left bar
  (existing paintEvent indicator, token color) + tinted bg; focus outline visible
  with keyboard focus (Tab navigation added: `setFocusPolicy(Qt.StrongFocus)` +
  arrow-key handling in the group).
- Bottom: console toggle, results-panel toggle (existing signals unchanged).
- Widths become token constants; `set_expanded` display logic kept.

### Main area
- Splitter `stacked tabs | results dock` unchanged; results dock chrome restyled
  (SectionHeader, panels), min/max width behavior preserved.
- DropOverlay: token colors, dashed accent border, centered icon+text.
- Status bar (hidden) + detached console restyle: neutral surfaces, mono text,
  token close button.

## Implementation tasks

1. Header: implement Save State chip; connect `save_manager.load_started/
   load_finished/save_started/save_finished` + `shell_state`; restyle chips/buttons;
   keep all signals and pulse/loading APIs.
2. Sidebar: add section labels, restyle items, add keyboard navigation; keep
   `nav_changed`, `console_toggled`, `right_panel_toggled`, `collapsed_changed`,
   `set_active`, `refresh_labels`, `set_right_panel_visible`, `set_console_visible`.
3. MainWindow shell parts: margins/spacing from tokens; restyle DropOverlay;
   keep `_lazy_tab_map`, splitter persistence, drag-drop.
4. Results dock + MenuPopup + detached window: token restyle.
5. i18n: any new visible strings (section labels) added to all 9 resource files via
   `t()` with English fallbacks if keys missing.

## Behavior-preservation requirements

- Page ids/order, lazy creation, splitter persistence, drag-drop, console
  detach/attach, update checker, warnings flow: unchanged.
- `test_main_window.py` lifecycle tests must pass untouched.
- Do not mutate widget trees while dialogs are in `exec()` (AGENTS rule).

## Tests and verification

- Focused: `uv run pytest -c tests/pytest.ini tests/unit/palworld_aio_tests/test_main_window.py tests/unit/palworld_aio_tests/test_shell_state.py`
- `uv run python -m compileall -q src tests`
- Launch: click all 12 nav entries; collapse/expand sidebar; toggle results panel;
  detach/attach console; load a save (state chip transitions); drag a Level.sav onto
  the window; resize to 1200×750 and maximize.

## Visual QA requirements

Screenshots: header (idle / dirty / saving), sidebar expanded+collapsed, drop overlay.
Check long localized labels (zh_CN, ru_RU) don't clip at default widths.

## Completion criteria

- Shell fully tokenized; scanner green; all shell interactions work.

## Known risks

- Frameless-window hit areas are sensitive to header height changes — keep 48px.
- Sidebar custom paintEvent + QSS interplay: verify active indicator alignment at
  both widths.
