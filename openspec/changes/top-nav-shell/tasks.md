# Tasks — Top Navigation Shell (Shell v3)

## 1. Phase 0 — Foundations: fonts, icons, status strip, bug fixes

- [x] 1.1 Register the newly bundled weight files in `chrome/fonts.py` (HankenGrotesk Medium/SemiBold, Inter_28pt Medium/SemiBold), add OFL license files beside the TTFs, and extend `TYPE` weight mapping to real weights; verify `load_app_fonts()` reports the new families and `uv run python -m compileall -q src tests` passes
- [x] 1.2 Point `constants.FONT_FAMILY` at the Inter stack (Segoe UI stays in fallbacks) and confirm dialog font resolution changes to Inter; verify with an offscreen `QFontInfo` probe and a screenshot of two representative dialogs (guild assign, player item)
- [x] 1.3 Build the SVG icon factory: `chrome/icons.py` gains a token-colored `QSvgRenderer`-based `get_qicon(name, role)` with per-(name,color,size) cache plus ~35 authored SVG assets under `resources/assets/icons/`; keep the glyph `get_icon()` path intact; verify unit test renders every registry key without missing-asset errors
- [x] 1.4 Migrate shell-visible icon call sites (window controls, tray state icons, empty states, menu popup) to the icon factory while keeping internal monolith code untouched; verify screenshots show no tofu/blank glyphs on a machine without any Nerd Font installed
- [x] 1.5 Restore a visible bottom status strip (~22-24px) hosting `StatusBarStream`, preserving detach/attach console behavior and transient message timeouts; verify streamed load/save messages appear in-window and the detached console round-trip still works
- [x] 1.6 Fix the folded-in bugs: global QSS rule giving scroll-area viewports/inner containers the dark palette (Breeding white rectangle), remove JSON Editor dead spacer row, add translated Tools world-section key (fix `TOOLS.SECTION.WORLD` leak), replace mojibake pagination glyphs in Base Inventory with icon-factory icons; verify each on screenshots and via `uv run pytest -c tests/pytest.ini` focused tests
- [x] 1.7 Phase gate: run `uv run pytest -c tests/pytest.ini` full suite, `uv run pyright src`, and capture before/after screenshots of Breeding, JSON, Tools, Base Inventory; verify no behavior regressions

## 2. Phase 1 — App bar + window controls + branding (reclaims the 170px gutter)

- [x] 2.1 Create `chrome/app_bar.py`: 44-48px bar with brand mark (circular logo crop + "PalTrainer" wordmark in Hanken 600), save-state chip (ShellState icon+label, spinner, click=save, dirty dot, update pulse), context indicator (PLAYER/GUILD/BASE elided values, placeholder state, click opens StatsPanel popover), utility buttons (console, guide, warnings with badge, about), and the re-hosted `WindowControls`; verify all existing signals (`console_toggled`, `guide_clicked`, `save_clicked`, `masthead_clicked` equivalents, warn slot) connect in `MainWindow` without contract changes
- [x] 2.2 Move the frameless drag zone from the 52px canvas strip to the app bar (empty-area drag only; interactive children exempt) and keep Esc/drop-overlay behavior intact; verify drag on empty app bar moves the window and clicks on children never drag
- [x] 2.3 Re-point `constants.header_loading_widget` and `shell_state` consumers to the save chip; verify no-save/loading/loaded/dirty/saving/error states render correctly during a real save load and save
- [x] 2.4 Remove `CONTROLS_RESERVE_WIDTH` usage from `create_page_ribbon`, `set_content_margins`, and `search_panel.py` so page rows span full width; update QSS builder rules for the new surfaces and regenerate `darkmode.qss` via `scripts/scrs/build_theme.py`; verify ribbon/toolbar/footer alignment at 1200x750 and maximized via screenshots
- [x] 2.5 Phase gate: full `uv run pytest -c tests/pytest.ini`, `uv run pyright src`, smoke script pass, and before/after screenshots of the app bar across min/max window sizes

## 3. Phase 2 — Nav strip (replaces the right rail)

- [x] 3.1 Create `chrome/nav_strip.py`: 38-40px strip with zone-grouped checkable tabs (Start: Tools; World: Map, Bases, Players, Guilds, Exclusions; Edit: Player Inventory, Base Inventory, Pal Editor, JSON Editor; Reference: Breeding, Docs), 1px zone separators, amber-underline active state, hover/focus treatments, tooltips with full i18n labels; verify all 12 nav IDs unchanged and `nav_changed`/`set_active` parity with the old band
- [x] 3.2 Add overflow behavior: compact labels (`nav.rail.*` keys reused) below a width threshold, then an overflow `»` menu for least-recently-relevant zones; verify at 1200px min width and with long locales (ru_RU, de_DE, pt_BR)
- [x] 3.3 Extend shortcuts: keep `Ctrl+1..0`, add Breeding and Docs shortcuts (`Ctrl+-`, `Ctrl+=`), update the tab guide dialog text to describe the new shell; verify all 12 destinations reachable by keyboard and the guide dialog matches reality
- [x] 3.4 Route tray content: selection updates (`set_player/set_guild/set_base`) to the context indicator, metrics to Tools field report + StatsPanel popover, console/warnings/about to app bar utilities; keep `NexusBand`/`InstrumentTray` classes present but unused behind facades; verify dirty-dot, pulse, and detach-state signals still fire through the new surfaces
- [x] 3.5 Phase gate: full test suite + `uv run pyright src` + screenshot pass of the shell with the rail hidden/removed and nav strip active; verify zero references to `nexus_band.set_active` outside facades

## 4. Phase 3 — Page skeleton adoption

- [x] 4.1 Add `create_page_footer` helper (status text left, actions right) and page-header grammar documentation in `chrome/components.py`; verify Players/JSON footers consolidate onto it with unchanged button wiring
- [x] 4.2 Migrate table pages (Players, Guilds, Bases, Exclusions) to the shared grammar: page header, toolbar with search+count, full-width table, footer; add shared empty states (no save / no results) to all four; verify context menus, bulk dialogs, and selection syncing unchanged
- [x] 4.3 Migrate JSON Editor toolbar/footer onto the grammar with token-colored search highlight and a no-save empty state; verify lazy-tree search, refresh, export/import round-trips still pass tests
- [x] 4.4 Move picker/switch rows (Base Inventory guild/base pickers, Pal Editor player picker, Breeding switches) from ribbon action slots into standard toolbar rows; verify pickers, view switches, and cross-tab selection sync unchanged
- [x] 4.5 Specialized-page alignment only: Map overlay toggles/legend insets respect the new chrome geometry (no app-bar/nav collision at min size), Tools columns stretch to fill and field report stays the single stats surface, Docs drops the single-item sub-tab bar; verify map interactions (markers, zones, calibration) unchanged
- [x] 4.6 Phase gate: full test suite, `uv run pyright src`, and full-page screenshot set (all 12 pages, empty + populated where feasible)

## 5. Phase 4 — Cleanup and retirement

- [ ] 5.1 Delete `nexus_band.py`, `instrument_tray.py`, glyph-icon backend for migrated surfaces, `FONT_FAMILY_NERD`/`FONT_ICON` constants, and remove the `nerdfont` dependency from `pyproject.toml`; verify `uv run python -m compileall -q src tests`, grep shows no residual references, and `uv sync` succeeds
- [ ] 5.2 Remove the legacy cyan QSS tail from the deployed theme (searchTree cyan selection, `#dfeefc`, `editPalsContainer` cyan gradient, `#A6B8C8` headers) and regenerate the theme; verify `scripts/scrs/check_theme_violations.py` retired-palette count drops accordingly and screenshots show Deck-Ops-only chrome
- [ ] 5.3 Update i18n files: add zone/chip/strip keys, retire obsolete rail keys, run the translation tooling (`scripts/scrs/add_translation_keys.py` / `update_translation_keys.py`); verify all 10 locales load without missing-key warnings at startup
- [ ] 5.4 Update smoke scripts (`smoke_shell_v2.py`, `smoke_start_v2.py`) for shell v3 and add focused regression tests for nav strip overflow, save chip states, and status strip streaming; verify `uv run pytest -c tests/pytest.ini` green
- [ ] 5.5 Final gate: full `uv run pytest -c tests/pytest.ini`, `uv run pyright src`, `uv run python -m compileall -q src tests`, fresh screenshot set, and manual save load → edit → save → exit pass; verify ui-nav/ui-shell/ui-states spec scenarios are demonstrably satisfied
