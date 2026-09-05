# UI modernization — inline-style audit (Phase 0, task 1.4)

Generated 2026-09-05 from a regex census over
`src/palworld_aio/ui/**`, `src/palworld_aio/widgets/**`,
`src/palworld_aio/editor/**`, `src/palworld_toolsets/**`.
Columns: `ss` = `.setStyleSheet(` calls, `fixed` = `.setFixed*(`,
`minmax` = `.setMinimum*/.setMaximum*(`, `retired` = retired-palette
occurrences (`#7DD3FC`, `#4A90E2`, `rgba(125,211,252,...)` — case-insensitive,
includes comments/HTML strings, so triage before editing).

Raw phrase counts, not violations: `fixed`/`minmax` include legitimate uses
(e.g. rail geometry, icon sizes). Baseline scanner run for reference:
`check_theme_violations.py --root src` reports 1390 violations across 43 files,
of which **95 are `retired-palette` errors** (new category, task 1.1).

## Shell (Phase 1 queue)

| File | ss | fixed | minmax | retired | Notes |
|---|---|---|---|---|---|
| ui/main_window.py | 0 | 2 | 5 | 1 | retired = `_show_about` rich-text `#4a90e2` (L975); recolor with rail/about work |
| ui/chrome/nexus_band.py | 0 | 5 | 0 | 0 | fixed = BAND_W/ITEM_H geometry; custom BandItem paint (labels/icons) |
| ui/chrome/instrument_tray.py | 0 | 6 | 0 | 0 | fixed row heights; absolute `_StateRow` icon geometry |
| ui/chrome/window_controls.py | 0 | 3 | 0 | 0 | 3x 30x24 buttons; now covered by builder `#windowControlBtn` (task 1.2) |
| ui/chrome/styled_combo.py | 3 | 2 | 2 | 4 | OUTLIER: pre-Deck-Ops cyan inline; replace with QComboBox + builder rules, do not re-theme |
| ui/chrome/components.py | 1 | 5 | 3 | 0 | ss = `make_status_dot` radius (acceptable); fixed = icon/avatar sizes |
| widgets/empty_state.py | 4 | 1 | 0 | 0 | token-based; review only |
| widgets/loading_popup.py | 6 | 3 | 0 | 2 | retired cyan L24/L94; re-theme with Phase 3 states work |
| widgets/menu_popup.py | 5 | 0 | 4 | 13 | retired cyan cluster; rebuild on builder menu rules |
| widgets/player_select_popup.py | 3 | 1 | 2 | 0 | blocking `processEvents` loop — do not touch loop, chrome only |
| widgets/scrollable_context_menu.py | 8 | 1 | 7 | 7 | duplicate `exec()` def; nested event loop — chrome only |
| widgets/stats_panel.py | 0 | 1 | 0 | 0 | clean |
| widgets/search_panel.py | 0 | 1 | 0 | 0 | shared table widget; keep API stable |
| widgets/toggle_check.py | 2 | 1 | 0 | 0 | BUG: `_label` never added to layout (invisible label) — fix with Phase 2 |
| widgets/tree_widgets.py | 1 | 0 | 0 | 2 | retired cyan L20 |
| widgets/collapsible_splitter.py | 0 | 3 | 0 | 0 | hardcoded 16px handle / 380px width |
| widgets/base_hover_overlay.py | 1 | 0 | 0 | 2 | retired cyan L71 |
| widgets/player_hover_overlay.py | 1 | 0 | 0 | 0 | inline green `#00C878` (not retired, still hardcoded) |

## Table pages (Phase 2 queue)

| File | ss | fixed | minmax | retired | Notes |
|---|---|---|---|---|---|
| ui/tabs/base_inventory_tab.py | 111 | 29 | 16 | 0 | outer frame only in this change; grid/dialog internals deferred (Phase 5) |
| ui/tabs/inventory_tab.py | 145 | 61 | 10 | 0 | outer frame only; `ItemSlotWidget` manual layout deferred (Phase 5) |
| ui/tabs/map_tab.py | 23 | 5 | 3 | 30 | legend/overlay chrome; scene internals deferred (Phase 5) |
| ui/tabs/json_editor_tab.py | 1 | 2 | 0 | 0 | toolbar/footer reframe |
| ui/tabs/breeding_tab.py | 6 | 9 | 1 | 0 | RichText HTML colors `#F59E0B/#A69F94` in cards |
| ui/tabs/docs_tab.py | 0 | 1 | 0 | 0 | single-button switch bar |
| ui/tabs/docs/wiki_tab.py | 34 | 21 | 1 | 33 | module QSS constants `_BASE/_SEARCH_S/...`; card virtualization deferred (Phase 5) |
| ui/tabs/pal_editor_tab.py | 1 | 0 | 1 | 0 | `CONTENT_PANEL_STYLE` inline; ribbon action via helper (task 1.3) |
| ui/tabs/tools_tab.py | 0 | 6 | 3 | 0 | Phase 3 card grouping target |

## Dialogs (Phase 4 queue, migrate one at a time)

Order: guild_assign first (reference), then player-item/pal/technology,
then fix-illegal pair, tab-guide, skill-picker/popups, GPS editor last.

| File | ss | fixed | minmax | retired | Notes |
|---|---|---|---|---|---|
| ui/dialogs/guild_assign_dialog.py | 1 | 0 | 4 | 0 | most migrated; reference migration (task 5.1) |
| ui/dialogs/player_item_dialog.py | 17 | 3 | 2 | 2 | business logic reads `.sav` per player — do not move logic |
| ui/dialogs/player_pal_dialog.py | 21 | 4 | 2 | 1 | `passiveCard` inline rank tint; builder base rule added (task 1.2) |
| ui/dialogs/player_technology_dialog.py | 14 | 5 | 2 | 12 | retired cyan frames; `property('tech_asset')` dead check — fix during migration to `tech_selected` property |
| ui/dialogs/fix_illegal_pal_dialog.py | 23 | 4 | 1 | 5 | per-card `setStyleSheet` selection; no BaseDialog |
| ui/dialogs/fix_illegal_player_dialog.py | 8 | 0 | 1 | 0 | duplicates pal-dialog button CSS verbatim |
| ui/dialogs/tab_guide_dialog.py | 14 | 1 | 1 | 2 | worst outlier: blue `#4a90e2` module theme; final `setStyleSheet(QDialog)` wipes global |
| ui/dialogs/skill_picker.py | 3 | 0 | 2 | 0 | blocking `processEvents` loop + 33ms anim — chrome only |
| editor/dialogs.py | 25 | 1 | 37 | 0 | `ThemedDialog` base + per-dialog inline; converge on `BaseDialog` |
| editor/gps_editor.py | 18 | 11 | 3 | 0 | per-button CSS duplicates builder kinds; `#navBtn` now in builder (task 1.2) |
| editor/worldoption_editor.py | 1 | 0 | 2 | 0 | matches builder `dialogOption/dialogCancel` — near done |
| palworld_toolsets/*.py | 18 | 10 | 23 | 55 | tool dialogs (character_transfer 22, fix_host_save 22, slot_injector 11 retired); migrate with their tool surfaces |

## Monolith internals (Phase 5, DEFERRED — outer frames only in this change)

| File | ss | fixed | minmax | retired | Notes |
|---|---|---|---|---|---|
| editor/pal_editor/pal_info_widget.py | 103 | 63 | 2 | 56 | largest debt single file; `passiveCard` rank tint |
| editor/pal_editor/create_dialogs.py | 94 | 19 | 12 | 0 | `name_lbl.setFixedWidth(170)` unrelated to ribbon reserve — leave |
| editor/pal_editor/*.py (rest) | 161 | 74 | 12 | 38 | card/slot/party/bulk/display/handlers/widgets/legacy_frame |
| ui/tabs/inventory_tab.py (grids) | — | — | — | — | counted above; grid/delegate internals deferred |
| ui/tabs/base_inventory_tab.py (grids) | — | — | — | — | counted above; container/pals internals deferred |
| ui/tabs/map_tab.py (scene) | — | — | — | — | counted above; markers/effects/calibration rewrite deferred |

## Deliberately untouched

- `chrome/tokens.py` retired=5: the `RETIRED_COLORS` definitions themselves (whitelisted theme system).
- `chrome/styles.py` ss=5: legacy `DIALOG_STYLE`/`PICKER_*`/`SLOT_*` constants (transitional; converge in Phase 4).
- `map_view/map_items.py` hardcoded `RGBA(255,0,0)` scene colors: scene internals, Phase 5.
- Game-data colors (rarity/element/rank via `constants`): data contract, never "violations".
