## 1. Phase 0 — Token freeze + audit (enabler, no visual changes)

- [x] 1.1 Freeze `chrome/tokens.py` as the single source of truth and document the retired palettes (cyan `#7DD3FC`, blue `#4a90e2`) as violations; verify `scripts/scrs/check_theme_violations.py` still passes on the tokens module.
- [x] 1.2 Add missing `qss_builder.py` rules for `#windowControlBtn`, tech-frame selected state, `#navBtn`, and `passiveCard` using token/property selectors only; verify regenerated `resources/ui/themes/darkmode.qss` contains the new rules and the app starts with `ThemeManager.apply_global()`.
- [x] 1.3 Replace the `170px` right-margin magic with one layout constant plus an overlay-aware ribbon helper wrapping `_ribbon_actions_slot`; verify Players/JSON/Breeding/BaseInventory ribbons render fully visible at 1200x750 with no logic changes.
- [x] 1.4 Audit and list all inline `setStyleSheet` hex and `setFixed*` call sites per screen (shell, tables, states, dialogs, monoliths) as the Phase 1–4 work queue; verify the list is recorded in the change and `uv run python -m compileall -q src tests` passes.

## 2. Phase 1 — Shell / rail (depends on Phase 0)

- [x] 2.1 Give each of the 12 rail destinations a distinct label/icon/zone grouping legible at 76px (fix Players/Guilds/Bases "Search" collision, Exclusions clipping, Pal/JSON overlap); verify all 12 pages are reachable by click and `Ctrl+1..0` with the correct active indicator and unchanged navigation IDs.
- [x] 2.2 Redesign the `InstrumentTray` rows (save state, PLAYER/GUILD/BASE selection, 2x2 metrics) and tray-drawer details for scanability; verify no-save, loading, loaded/dirty, saving, and error states all display correctly with live counts after a save load.
- [x] 2.3 Style `WindowControls` via builder rules and confirm ribbon/drag behavior (empty ribbon drags, interactive children never drag, controls clickable at min/max sizes); verify with before/after screenshots plus `Esc` closing only the tray drawer.
- [x] 2.4 Phase 1 gate: capture before/after screenshots of the shell at fixed size and run focused then full `uv run pytest -c tests/pytest.ini`; verify no navigation, shortcut, dirty-dot, pulse, console-toggle, or `refresh()` regression.

## 3. Phase 2 — Standard table pages (depends on Phases 0–1)

- [x] 3.1 Apply the standard frame (ribbon -> toolbar with search/filter/count -> card-contained `SearchPanel`/`DataTable` -> footer with status+actions) to Players (bulk actions in footer); verify filter/count sync and bulk-action entry points still open their existing dialogs.
- [x] 3.2 Apply the same frame to Guilds, Bases, and Exclusions (segmented players/guilds/bases switch with single selection); verify per-view search/table/count and existing context-menu operations are preserved.
- [x] 3.3 Apply the same frame to the JSON Editor (search+nav+match count above Key/Value/Type table; Refresh/Export/Import + save status in footer); verify lazy-tree search, refresh-from-save, and export/import round-trips still work.
- [x] 3.4 Phase 2 gate: capture before/after screenshots of all five pages and run `uv run python -m compileall -q src tests` plus full `uv run pytest -c tests/pytest.ini`; verify header treatment, selection, counts, and i18n labels are consistent.

## 4. Phase 3 — Empty/state pages (depends on Phases 0–1)

- [x] 4.1 Render shared `EmptyState`+CTA on Pal Editor (select player), Breeding (select pal), Docs/Wiki empty, and Map/Tools empty conditions; verify each CTA opens its existing picker/load flow with no manager changes.
- [x] 4.2 Group the Tools page into labeled card sections (save ledger + Steam/GamePass load, field-report metrics, conversion/management/world tools); verify load flows and tool-launch dispatch (`palworld_toolsets.*`) are unchanged.
- [x] 4.3 Dock the Map legend as a scrollable card and keep the Map Viewer ribbon title visible at all window sizes; verify overlay toggles, marker clicks, and zone operations still route to existing `zone_manager`/`base_manager` calls.
- [x] 4.4 Phase 3 gate: capture before/after screenshots of Tools/Breeding/PalEditor/Map/Docs empty and populated states and run the full test suite; verify no empty-state dead ends remain.

## 5. Phase 4 — Dialog consolidation, one dialog at a time (depends on Phases 0–1; runs incrementally alongside/after Phases 2–3)

- [x] 5.1 Migrate `guild_assign_dialog.py` onto `components.BaseDialog` with property-driven state as the reference migration; verify assign flow and member-tree behavior unchanged.
- [x] 5.2 Migrate player-item, player-pal, and player-technology dialogs one per commit (property-driven selection, token palette, no cyan/blue residuals, no event-loop changes); verify each dialog's existing operations (bulk items, pal delete/skills, tech add/remove) still complete.
- [x] 5.3 Migrate fix-illegal-pal, fix-illegal-player, tab-guide, skill-picker/popups chrome, and GPS editor last (largest blast radius); verify each still opens, completes, and dismisses via `Esc`, with `.sav` access paths untouched.
- [x] 5.4 Phase 4 gate per dialog: screenshot the migrated dialog, confirm partial migration stays shippable (unmigrated dialogs unaffected), and run focused tests plus `compileall` before the next dialog.

## 6. Phase 5 — Monolith detangling (EXPLICITLY DEFERRED, separate future change)

- [x] 6.1 Deferred: split/virtualize `inventory_tab.py`, `base_inventory_tab.py`, `map_tab.py`, and `docs/wiki_tab.py` internals (delegates, virtualization, timers, calibration rewrite, direct `.sav` access) under a new change; verify this UI-modernization change ships Phases 0–4 with monolith internals behaviorally unchanged beyond their outer page frames.
