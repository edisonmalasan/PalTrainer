# Plan 001 — Repository & UI Architecture Audit

## Objective

Record the evidence base for the overhaul: a complete screen-to-code map, widget /
component inventory, and stylesheet audit of the current UI, so that every later plan
targets real files and no screen is missed.

## Scope

Read-only documentation of the current state. No code changes.

## Screen-to-code map (verified 2026-09-03)

| # | Screen / area | Primary code | Shared widgets used |
|---|---------------|--------------|---------------------|
| 1 | Application shell (frameless window, header, sidebar, splitter, console) | `src/palworld_aio/ui/main_window.py` (2547 ln) | `chrome/header_widget.py`, `chrome/sidebar_widget.py`, `widgets/menu_popup.py`, `widgets/loading_popup.py`, `tools_tab.DropOverlay` |
| 2 | Dashboard (Tools tab, save card, tool grids) | `src/palworld_aio/ui/tabs/tools_tab.py` (562 ln) | ToolCard (local), save_manager signals |
| 3 | Results Panel (right dock) | `src/palworld_aio/ui/chrome/results_widget.py` | `widgets/stats_panel.py` |
| 4 | Statistics Panel | `src/palworld_aio/widgets/stats_panel.py` | — |
| 5 | Search Players / Guilds / Bases | `main_window._setup_players_tab / _setup_guilds_tab / _setup_bases_tab` | `widgets/search_panel.py` (7 instances + 2 in guild dialog) |
| 6 | Base Inventory | `src/palworld_aio/ui/tabs/base_inventory_tab.py` (4176 ln, 123 inline styles) | InventoryGridWidget, ItemPickerDialog, StatsPanel, EmptyState |
| 7 | Player Inventory | `src/palworld_aio/ui/tabs/inventory_tab.py` (4132 ln, 153 inline styles) | InventoryGridWidget, EmptyState, player_select_popup |
| 8 | Pal Editor | `ui/tabs/pal_editor_tab.py` + `src/palworld_aio/editor/edit_pals.py` + `editor/pal_editor/*` (15 modules) | EmptyState, SkillPicker, ScrollableContextMenu |
| 9 | Map Viewer | `ui/tabs/map_tab.py` (2646 ln) + `ui/map_view/` (map_view, map_markers, map_items, map_effects) | Base/PlayerHoverOverlay |
| 10 | Breeding | `ui/tabs/breeding_tab.py` (554 ln) | editor/pal_editor helpers, create dialogs |
| 11 | JSON Editor | `ui/tabs/json_editor_tab.py` (426 ln) | — |
| 12 | Exclusions | `main_window._setup_exclusions_tab` | SearchPanel (2 lists) |
| 13 | Wiki / Docs | `ui/tabs/docs_tab.py` + `ui/tabs/docs/wiki_tab.py` (1506 ln) | TabGuideDialog |
| 14 | Item / Pal / Tech / Guild dialogs | `ui/dialogs/` (player_item 778 ln, player_pal 541 ln, player_technology 395 ln, guild_assign 410 ln, fix_illegal_pal 254 ln, fix_illegal_player 125 ln, skill_picker 333 ln, tab_guide 257 ln) | ToggleCheckBtn, SearchPanel, PICKER_* styles |
| 15 | Editor dialogs & pickers | `editor/dialogs.py`, `editor/pal_editor/create_dialogs.py`, `editor/gps_editor.py`, `editor/worldoption_editor.py` | PalFrame, PalCreateDialog |
| 16 | Conversion / transfer / repair flows | `palworld_toolsets/*` (domain), dispatched from tools_tab; `main_window` menu wiring | editor/dialogs.py inputs |
| 17 | Boot splash & loading states | `src/bootup.py` (splash), `widgets/loading_popup.py`, `import_libs.run_with_loading` | — |

## Widget / component inventory

Shared (reused): `ToggleCheckBtn` (~12 consumers), `ScrollableContextMenu` (~15),
`SearchPanel` (9), `StatsPanel` (3), `EmptyState` (4 tabs), `SkillPicker` (5),
`MenuPopup` (header), `NerdBtn`/`NerdLabel` (chrome), `show_player_select_popup` (2),
styled combo (`chrome/styled_combo.py`).

Single-screen: ResultsWidget, MapGraphicsView + markers/items/effects, hover overlays,
LoadingPopup, ToolCard, InventoryGridWidget, InventoryLoadoutDialog, PalEditorWidget.

Orphaned (exported, never instantiated — plan 018 removes): `SortableTreeWidget`,
`CollapsibleSplitter`, `LoadingOverlay`, `ScrollableMenu`; dead signal
`SearchPanel.search_requested`; `PlayerHoverOverlay` ~90% duplicated by
`BaseHoverOverlay.show_for_player`.

## Stylesheet / theme audit

- Single hand-written theme: `resources/ui/themes/darkmode.qss` (1463 lines, 38 KB),
  loaded by `ThemeManager.load_qss_content()` from `boot_paths.GUI_DIR`; bootup splash
  loads the same file pattern (`{theme}mode.qss`).
- Token layers: `palworld_aio/constants.py` (colors, spacing, radius, font sizes,
  fonts) → `ui/chrome/tokens.py` (rgba composites, gradients) → `ui/chrome/styles.py`
  (ThemeManager + QSS string constants DIALOG_STYLE, MENU_STYLE, STATS_PANEL_STYLE,
  PICKER_*, TREE_WIDGET_QSS, slot styles).
- ~390 `.setStyleSheet(` call sites in `src/palworld_aio` bypass the token layer
  (worst: inventory_tab 153, base_inventory_tab 123, pal_info_widget 103,
  create_dialogs 94, wiki_tab 34, map_tab 32).
- Duplicated palette clusters: menu popup palette (6+ files), amber/green/red status
  buttons (5+ files), hover overlay pair, tab_guide's private off-token palette.
- Decorative color noise in QSS: gold version chip, purple menu chip, green game chip,
  blurple discord chip, gradient title, glass gradients.
- `scripts/scrs/check_theme_violations.py` scanner + unit tests; whitelist covers
  chrome/styles.py, chrome/tokens.py, chrome/icons.py, constants.py, edit_pals.py,
  editor/edit_pals.py, `data/gui/` prefix.
- Fonts: `FONT_FAMILY='Segoe UI'`, `FONT_FAMILY_NERD='Hack Nerd Font'` (bundled, only
  loaded in header), `FONT_FAMILY_MONO='Consolas'`; literal 'Segoe UI' also appears in
  loading_popup.py / menu_popup.py. Hanken Grotesk / Inter are NOT installed.
- No High-DPI attribute settings; `QApplication.setStyle('Fusion')` in main.py.

## Architecture facts that constrain the overhaul

- Lazy tab creation via `_lazy_tab_map` (indexes 0–11) — page ids are stable.
- Tabs read `constants.loaded_level_json` + `save_manager` (QObject singleton with
  signals); newer `save_session` (plain object) owns path approval/backup/atomic write.
- Shell state model exists (`palworld_aio/shell_state.py`) but is not surfaced in the UI.
- Tests: structural harness + `test_constants.py` (pins exact hex) +
  `test_main_window.py` (Qt lifecycle) + scanner unit tests; no pytest-qt.
- pyright configured with specific reports disabled; no ruff/black.

## Dependencies

None (first plan).

## Implementation tasks

None — this plan is the audit record. Its "tasks" are the inventory above, verified
against the working tree on branch `feat/ui-overhaul`.

## Behavior-preservation requirements

N/A (no changes).

## Tests and verification

N/A.

## Visual QA requirements

N/A.

## Completion criteria

- Every screen in the sidebar has an owning file recorded above.
- Every shared widget's consumer list is recorded.
- Orphaned code and worst duplication offenders are named.

## Known risks

- Line counts drift as other branches merge; counts are indicative, files are the truth.
- Two audit areas were read at medium depth (editor/pal_editor internals, palworld_toolsets
  GUI surfaces); plans 010 and 016 must re-verify details before editing those files.
