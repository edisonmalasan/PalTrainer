# Top Navigation Shell (Shell v3)

## Why

The current right-side NexusBand rail (76px) forces micro-labels and cramped tray text, wastes the right edge of a table-heavy application, and provides no home for branding or the save action. Combined with the floating window controls reserving a 170px dead gutter on every page, roughly 246px of horizontal space never reaches content. The user experience goal is a conventional, discoverable top navigation with an app bar that reclaims that space and gives save state, selection context, and branding an intentional home.

## What Changes

- **Replace the right NexusBand rail** with a two-tier top shell:
  - **App bar** (~48px): brand mark (logo + wordmark), save-state chip (state text, dirty indicator, click = save, spinner while loading/saving), utility buttons (console, tab guide, warnings, about), and the window min/max/close cluster. The app bar becomes the frameless-window drag strip.
  - **Nav strip** (~40px): the 12 page destinations grouped into four labeled zones — **Start** (Tools), **World** (Map, Bases, Players, Guilds, Exclusions), **Edit** (Player Inventory, Base Inventory, Pal Editor, JSON Editor), **Reference** (Breeding, Docs).
- **Remove the permanent right-side InstrumentTray.** Save state, dirty indicator, save action, loading/saving state move to the app-bar save chip. Player/Guild/Base selection context moves to a compact current-context indicator in the app bar, with details available on demand; per-page context lives in page headers. Statistics remain on the Tools page (field report) with the existing StatsPanel available in an optional popover.
- **Eliminate the 170px `CONTROLS_RESERVE_WIDTH` gutter** — window controls live in the app bar, so page content spans the full canvas width.
- **Regroup navigation user-facing labels** into Start / World / Edit / Reference while **preserving all internal navigation IDs** (`tools`, `base_inventory`, `player_inventory`, `pal_editor`, `players`, `guilds`, `bases`, `map`, `exclusions`, `json_editor`, `breeding`, `docs`), signal contracts, lazy tab creation, and refresh coupling unchanged.
- **Keep Exclusions a first-class, directly visible destination** under World.
- **Extend keyboard shortcuts** so all 12 destinations are reachable (breeding and docs currently have no shortcut).
- **Branding**: place the circular logo mark (from `resources/assets/branding/logo.png` art) plus "PalTrainer" wordmark at the app bar's left. Update-available pulse affordance moves to the brand/save-chip area.
- **Icon strategy**: replace the deleted Hack Nerd Font codepoint rendering with a bundled, token-colored SVG icon set rendered via `QSvgRenderer` (PyQt6 ships QtSvg; no new dependency). Remove `FONT_FAMILY_NERD` usage and the `nerdfont` dependency after migration.
- **Typography**: bundle the newly added real font weights (Hanken Grotesk Regular/Medium/SemiBold, Inter 28pt Regular/Medium/SemiBold), map the type scale to real weights, and eliminate synthetic bold for primary UI typography. Hack Nerd Font is never used or reintroduced.
- **Restore a visible status strip** (bottom) for streamed load/save messages, replacing the hidden zero-height status bar, with selection/context details available there or in page headers.
- **Page-skeleton standardization**: introduce shared page patterns (page header row, toolbar row, content zone, optional footer row) and adopt them per page; unify empty-state handling on the shared `EmptyState` component. Full per-page layout work is phased (see tasks) and specialized pages (Map canvas, inventory workspaces, Pal Editor, Tools masthead, Breeding cards) keep their specialized content layouts.
- **Bug fixes folded in**: Breeding scroll-container renders with the default light palette (white rectangle); JSON Editor has a dead spacer row above its ribbon; Tools page shows an untranslated `TOOLS.SECTION.WORLD` key; Base Inventory has mojibake pagination glyphs; stale cyan legacy QSS tail contradicts the ui-shell spec.

## Capabilities

### New Capabilities
- `ui-nav`: Top navigation behavior — app bar (brand, save chip, context indicator, utilities, window controls, drag zone) and nav strip (zone-grouped destinations, active/hover/selected/disabled/overflow/tooltip behavior, keyboard shortcuts).

### Modified Capabilities
- `ui-shell`: The right-rail navigation, per-page ribbon, instrument tray, and floating window-controls requirements are replaced by the top two-tier shell; ribbon requirement becomes a page-header requirement; theme-consistency requirement is restated against the new shell surfaces.
- `ui-states`: Empty-state and shell-state requirements extend to the new save chip, context indicator, status strip, and the Breeding/JSON/Tools/Base-Inventory state fixes.

## Impact

- **Code**: `src/palworld_aio/ui/main_window.py` (shell assembly, drag zone, status stream host, nav dispatch), `src/palworld_aio/ui/chrome/` (`nexus_band.py` and `instrument_tray.py` retired behind compatibility facades; new `app_bar.py`, `nav_strip.py`, icon factory; `window_controls.py` re-hosted; `components.py`, `tokens.py`, `fonts.py`, `qss_builder.py` extended), `src/palworld_aio/ui/tabs/*` (page header/footer adoption, bug fixes), `src/palworld_aio/widgets/search_panel.py` (gutter removal), `src/palworld_aio/constants.py` (`FONT_FAMILY_NERD` removal).
- **Contracts preserved**: navigation IDs, `nav_changed` signal, `set_active`/`_on_nav_changed` coupling, `ShellState` enum flow, `set_player/set_guild/set_base`, `update_metrics`, `set_dirty`, console detach/attach, `constants.header_loading_widget` (re-pointed), menu popup entry, drag-and-drop load, drop overlay.
- **Removed user-facing artifacts**: right rail + tray, 170px right gutter, ribbon-bound window-controls reserve.
- **Dependencies**: no new runtime dependencies (QtSvg ships with PyQt6); `nerdfont` pip dependency removed at the end of migration.
- **i18n**: new keys for nav zone groups (Start/World/Edit/Reference), save chip, context indicator, status strip; `nav.rail.*` keys retired; 10 locales updated.
- **Tests/tooling**: `scripts/scrs/smoke_shell_v2.py` and shell-related tests updated; theme scanner kept green; QSS regenerated via `scripts/scrs/build_theme.py`.
- **Out of scope**: monolith internals (inventory/base-inventory/map/wiki delegates, virtualization, direct `.sav` access) — deferred per the archived ui-modernization change; manager/data-layer behavior.
