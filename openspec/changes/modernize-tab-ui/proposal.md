## Why

Despite the completed top-nav shell (v3), the individual pages still exhibit the UX problems the shell was meant to frame: the Tools page duplicates its own tool list in two competing systems (campaign strip + mission columns), mission rows render as text-like rows with no icons or visible descriptions, the "World Tools" column leaves a large dead region, and loaded-state text (drag hint) lingers after a save is loaded. Each remaining tab (Base Inventory, Player Inventory, Pal Editor, Players, Guilds, Bases, Map, Exclusions, JSON Editor, Docs, Breeding) has unstudied layout, hierarchy, density, and precondition-state issues. Modernization must proceed tab-by-tab with explicit review gates rather than one speculative rewrite.

## What Changes

- Establishes a per-tab UI modernization program processed in review-gated order: Tools first, then Base Inventory, Player Inventory, Pal Editor, Players, Guilds, Bases, Map, Exclusions, JSON Editor, Docs, Breeding.
- **Tools page (first batch):**
  - Removes the OPS.CAMPAIGN quick-strip; all 7 tool entry points live in exactly one grouped list system.
  - Reorganizes tool groups into two balanced columns — Conversion (Convert Save Files, Convert GamePass ↔ Steam, Convert SteamID, Restore Map) and Management (Slot Injector, Character Transfer, Fix Host Save) — replacing the unbalanced 3-column grid whose "World Tools" column held a single row.
  - Gives every tool row a real action affordance: icon tile (bundled SVG set), tool title, and a one-line description restored from existing i18n description keys (no tooltip-only descriptions).
  - Merges the field-report metric chips (Players/Guilds/Bases/Pals, navigation-preserving) into the save-status masthead card as a metric row, eliminating the standalone strip and its horizontal dead space.
  - Replaces jargon kicker labels ("OPS.SAVE_LEDGER", "OPS.FIELD REPORT", "OPS.CAMPAIGN") with plain section labels; en_US values updated.
  - Shows the drag-and-drop hint only in the no-save state; loaded state shows the save path with an explicit reveal affordance.
  - Uses correct bundled Steam/GamePass SVG assets for load buttons (already `steam.svg`/`gamepass.svg` via the icon factory) — verified, no platform-logo substitutions.
- Later batches (Pal Editor density, inventory workspaces, map overlays, JSON editor, guild master/detail, breeding, docs, exclusions) will be added to this change's specs/design/tasks as each tab's review is completed; scope grows incrementally, never speculatively.
- **Non-changes (hard boundaries):** navigation page IDs, `_TAB_SETUP`/`_TAB_REFRESH` coupling, save/load behavior, `save_manager` contracts, i18n key structure (values may be corrected, keys preserved), shortcuts, drag-and-drop overlay behavior, tool handlers and their save-session reset behavior, window behavior, and save-state handling are preserved. No parallel styling system: chrome/tokens, qss_builder, components, icons, fonts remain the only styling sources.

## Capabilities

### New Capabilities
- `ui-pages`: per-page layout and hierarchy contracts for the modernized tabs (start/save-hub page now; dense editor and inventory workspaces as later batches land).

### Modified Capabilities
- `ui-states`: Tools page precondition behavior — the no-save/loaded states of the save hub (state visibility, drag-hint suppression when loaded, path reveal affordance) become specified behavior.

## Impact

- Touched (Tools batch): `src/palworld_aio/ui/tabs/tools_tab.py`, `src/palworld_aio/ui/chrome/qss_builder.py` (retire `fieldReport`/`campaignStep` rules, add masthead metric + tool-row styles), `resources/i18n/en_US.json` (label values for `ops.*`/`tools.*` keys only).
- Not touched: `src/palsav/*`, `src/palworld_aio/managers/*`, `palworld_toolsets/*`, tool handler logic, other tabs (until their batch), non-en locale files.
- Risk containment: visual/layout-only delta on one page with before/after populated screenshots at 1200x750 (`scripts/scrs/shot_populated.py` with the backup Level.sav as read-only fixture), `compileall` + focused tests gates.
