## Why

PalTrainer works but its PyQt6 presentation lags behind its save-engine quality: the right-rail navigation truncates labels ("Search" x3, clipped "Exclusions"), tables are full-bleed with inconsistent headers, empty states are dead voids, and three styling generations (tokens+builder vs. legacy gradients vs. per-widget hardcoded hex/cyan/blue) coexist. A token-driven, incremental modernization restores hierarchy, spacing, and consistency without risking save behavior.

## What Changes

- **Phase 0 — Token freeze + audit (enabler, no visuals):** freeze `chrome/tokens.py` as the single source of truth; add missing `qss_builder.py` rules (`#windowControlBtn`, tech-frame selected state, `#navBtn`, `passiveCard`); replace the `170px` right-margin magic with a layout constant + overlay-aware ribbon; record retired colors (`#7DD3FC`/cyan, `#4a90e2`/blue) as violations.
- **Phase 1 — Shell / rail (main scope):** distinct nav labels/icons per destination, zone grouping readable at 76px, tray redesign (state row + selection + 2x2 metrics, details in drawer), masthead/dirty-dot/update-pulse preserved, `WindowControls` overlay styled via builder.
- **Phase 2 — Standard table pages (main scope):** one page frame for Players/Guilds/Bases/Exclusions/JSON Editor: ribbon (title+zone+actions) -> toolbar (search+filter+count) -> card-contained table (`SearchPanel`/`DataTable`) -> footer (status+actions). Standardize headers, counts, bulk-action placement.
- **Phase 3 — Empty/state pages (main scope):** `EmptyState`+CTA on Pal Editor/Breeding/Map/Docs/Tools empty conditions; Tools campaign grouped into cards; Map legend docked as card with scroll; JSON toolbar/footer separation.
- **Phase 4 — Dialog consolidation (incremental, per-dialog):** migrate dialogs onto `components.BaseDialog` (kicker+title+rule+content+danger-left footer) one at a time, starting with `guild_assign_dialog`; property-driven selection state instead of stylesheet-string swaps. No big-bang rewrite.
- **Phase 5 — Monolith detangling (explicitly DEFERRED, separate effort):** split/virtualize `inventory_tab` (~4125L), `base_inventory_tab` (~4169L), `map_tab` (~2639L), `wiki_tab` (~1506L) internals. This change only reframes their outer page chrome; internals are out of scope.
- **Non-changes (hard boundaries):** no business/manager logic moves; navigation page IDs, `_TAB_SETUP/_TAB_REFRESH` coupling, `save_manager` load/save fan-out, `Ctrl+1..0`/`Esc` shortcuts, `t()` i18n keys, auto-save/blocking-popup timers, frameless-drag behavior, and `sys.stdout` status-stream threading model are preserved.

## Capabilities

### New Capabilities
- `ui-shell`: right-rail navigation, page ribbon, window-controls overlay, instrument tray/drawer, and global dark Deck-Ops theme application.
- `ui-tables`: standard table-page frame (toolbar, card-contained table, footer) shared by Players/Guilds/Bases/Exclusions/JSON Editor.
- `ui-states`: empty/loading/error presentation including `EmptyState`+CTA usage and Tools/Map/Breeding/PalEditor empty conditions.
- `ui-dialogs`: dialog scaffold consolidation behind `BaseDialog`, per-dialog migration order, and property-driven selection state (Phase 4 incremental; Phase 5 monolith internals deferred).

### Modified Capabilities
- None. `openspec/specs/` is empty and this change preserves all existing behavioral contracts; deltas are new UI-presentation capabilities only.

## Impact

- Touched: `src/palworld_aio/ui/chrome/*` (tokens, qss_builder, components, nexus_band, instrument_tray, window_controls), `src/palworld_aio/ui/main_window.py` (ribbon/margins/overlays only), `src/palworld_aio/ui/tabs/*` (outer page frames), `src/palworld_aio/widgets/*` (SearchPanel/EmptyState), `src/palworld_aio/ui/dialogs/*` (Phase 4, per-dialog), `resources/ui/themes/darkmode.qss` (regenerated).
- Not touched: `src/palsav/*`, `src/palworld_aio/managers/*`, `src/palworld_aio/application/*`, save parsing/serialization, and monolith internals (Phase 5).
- Risk containment: visual-only deltas per phase with before/after screenshots at fixed window size; `compileall` + focused/full `pytest -c tests/pytest.ini` gates; no parallel styling systems introduced.
