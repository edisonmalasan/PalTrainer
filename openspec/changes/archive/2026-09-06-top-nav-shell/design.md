# Design — Top Navigation Shell (Shell v3)

## Context

Shell v2 (plan 020/025) is a frameless window with a full-bleed `QStackedWidget` canvas plus a 76px right `NexusBand` rail (`nexus_band.py`, `instrument_tray.py`); `WindowControls` floats top-right and every ribbon/toolbar row reserves a 170px `CONTROLS_RESERVE_WIDTH` gutter (`window_controls.py:26`, `components.py:446,469-477`). Icons render as Nerd-Font codepoints, but the bundled Nerd Font was deleted — rendering now depends on a system-installed font. Fonts bundle only Regular weights while QSS requests 600/700 (synthetic bold). The ui-modernization change (archived 2026-09-05) froze the token palette, QSS builder flow (`tokens.py` → `qss_builder.py` → `build_theme.py`), and left monolith internals (inventory/base-inventory/map/wiki internals) explicitly deferred — this change keeps that boundary. The user confirmed: two-tier top nav; tray removed; Start/World/Edit/Reference grouping; internal nav IDs unchanged; Exclusions top-level; real font weights (now present in `resources/assets/fonts/`: HankenGrotesk Regular/Medium/SemiBold, Inter_28pt Regular/Medium/SemiBold); dark-only tokens; specs delta before replacing the shell.

## Goals / Non-Goals

**Goals:**
- Two-tier top shell (app bar + nav strip) with all v2 behaviors preserved behind the same signal contracts.
- Reclaim ~246px of horizontal space (76px rail + 170px gutter).
- Self-contained vector icon system; real font weights; visible status strip; page skeleton grammar.

**Non-Goals:**
- No manager/data-layer behavior changes; no business-logic edits.
- No monolith internals rework (delegates, virtualization, direct `.sav` access in `inventory_tab.py`, `base_inventory_tab.py`, `map_tab.py`, `wiki_tab.py` internals) — deferred debt stays deferred.
- No light theme, no palette changes, no third-party icon/Qt libraries.
- No change to dialog business logic (dialog chrome convergence remains separate debt).

## Decisions

### D1 — Two-tier top shell over alternatives
Top nav (flat single row) cannot fit 12 destinations + brand + chip + controls at 1200px; a kept/widened rail fails the brief; zone-tabs-plus-dropdowns hide high-traffic pages. Two tiers (48px app bar + 40px nav strip) match the confirmed direction. Zone captions become real labels: Start / World / Edit / Reference (existing `ZONES` regrouped: World gains Map from Inspect; Edit keeps the three editors; Reference keeps Breeding + Docs).

### D2 — Compatibility facades, then retirement
`MainWindow` keeps the call sites that today touch `nexus_band.*` / `sidebar.*` / `header_widget.*` facades. New `chrome/app_bar.py` (brand, save chip, context indicator, utilities, window controls) and `chrome/nav_strip.py` implement the same public surface (`set_active`, `nav_changed`, `set_dirty`, `set_console_visible`, pulse API, `set_player/set_guild/set_base`, `update_metrics`, `set_shell_state`, `tray.set_shell_state` re-pointing for `constants.header_loading_widget`). `nexus_band.py`/`instrument_tray.py` are deleted only after no call sites remain; the tray drawer (`TrayDrawer`/StatsPanel) survives as an on-demand popover anchored to the context indicator/save chip. Alternative considered: keep NexusBand class and restyle it — rejected: geometry, paint code, and tray are inseparable there.

### D3 — Nav strip implementation
QSS-styled checkable `QPushButton` tabs (existing `pageSwitchBtn` grammar generalized) in an HBox with 1px zone separators — no custom paint code (avoids the BandItem overlap class of bugs); elide policy per tab; overflow via compact labels (`nav.rail.*` shorts survive as compact forms) then an overflow `»` menu. Keyboard: existing `Ctrl+1..0` unchanged; Breeding = `Ctrl+-`, Docs = `Ctrl+=` (both free; arrow-key focus movement via the strip's focus chain). Active state = amber text + 2px amber underline; hover = `surface_hover`; focus ring = `accent_border_focus`.

### D4 — Save chip and context indicator
`SaveStateChip` binds `ShellState` (no-save/loading/loaded/dirty/saving/error): icon + label, spinner during loading/saving, click = save (existing `_save_changes`), dirty dot for unsaved changes; update pulse moves here. `ContextIndicator` shows PLAYER/GUILD/BASE selection (elided, tooltip full text) and opens the StatsPanel popover on click. Both feed from the existing `shell_state` model and manager signals — no new state store.

### D5 — Status strip restoration
The zero-height `QStatusBar` becomes a 22-24px visible strip showing `StatusBarStream` messages (today invisible unless the console is detached); detach/attach console flow unchanged. Transient messages keep the existing timeout behavior.

### D6 — Icon system without new dependencies
`chrome/icons.py` keeps its string-key API; a new vector backend renders a curated ~35-icon SVG set (self-authored, 16px grid, 1.5px stroke) via `QSvgRenderer` into token-colored `QIcon`/`QPixmap` (normal/hover/active), cached per (name, color, size). Legacy `get_icon()` (glyph strings) stays temporarily for unmigrated internals; new shell surfaces use `get_qicon(name, color_role)`. `FONT_FAMILY_NERD`/`FONT_ICON` and the `nerdfont` dependency are removed once the last codepoint call site is migrated. Rationale: QStyle standard icons are too limited; another icon font repeats the tofu failure mode; QPainterPath-in-code is a maintenance burden for ~35 glyphs.

### D7 — Typography: real weights, two families + mono
Bundled weights (already added): HankenGrotesk Regular/Medium/SemiBold, Inter_28pt Regular/Medium/SemiBold. `tokens.TYPE` maps roles to real weights (display/title 600, section 600, body 400, secondary 400); QSS font stacks updated to prefer these; OFL license files ship beside the TTFs. `constants.FONT_FAMILY` migrates from `'Segoe UI'` to the Inter stack so the ~400 ad-hoc `QFont(constants.FONT_FAMILY, …)` call sites land on Inter without individual edits (Segoe UI stays in the fallback stack). Mono (Cascadia Mono → Consolas) unchanged. Nerd font references deleted.

### D8 — Page skeleton grammar (shared, non-invasive)
`PageShell`-style helpers formalize the already-emergent pattern: page header row (title + zone caption + action slot), toolbar row (pickers/filters/switches), content zone, optional footer row (status + persistent actions). Implemented as extensions of `create_page_ribbon` + a new `create_page_footer`; existing `SearchPanel` footer slot merges into it. Adoption is per-page and incremental; specialized content zones (map canvas, splitters, grids, cards) are untouched. The 170px reserve and `set_content_margins` gutter parameter are removed (header/footer rows span full width).

### D9 — Bug fixes ride along where the touched surface coincides
Breeding white rectangle → global QSS rule for scroll-area viewports/inner containers (dark palette for `QScrollArea > QWidget > QWidget` + viewport background), not a Breeding-only patch. JSON dead spacer row removed. `TOOLS.SECTION.WORLD` key leak fixed with a real key + fallback. Mojibake arrows replaced by icons from the new set. Legacy cyan tail of the deployed QSS removed (spec alignment).

### D10 — i18n and settings compatibility
New keys: zone groups (`nav.zone.start/world/edit/reference`), save chip states (reuse `tray.state.*`), context indicator labels (reuse `deletion.selected_*_label`), status strip. `nav.rail.*` compact-label keys are kept as the overflow compact forms. `user_settings` keys unchanged (`tray_expanded` becomes unused; kept read-tolerant). Window drag zone moves from the 52px canvas strip to the app bar.

## Risks / Trade-offs

- [Shell signal rewiring regressions (dirty dot, pulse, detach, loading spinner)] → Keep `ShellState` enum and facade signatures; port the existing smoke scripts (`smoke_shell_v2.py`) to assert chip/nav behaviors; run full pytest + manual screenshot pass per phase.
- [Vertical space cost (~88px chrome + ~24px status strip) on 750px min height] → App bar 44px + nav strip 38px; page header row absorbs the old ribbon (no double header); tables keep current row density.
- [12 tabs + brand + chip at 1200px min width] → Compact labels first, overflow menu second; i18n locale length verified for ru_RU/de_DE/pt_BR during tasks.
- [SVG icon rendering color/DPI mismatches] → Token-colored rendering with cache; screenshot gate per icon batch; keep glyph fallback path until the final cleanup task.
- [`constants.FONT_FAMILY` migration touching hundreds of dialogs] → It is a one-constant change with the fallback stack absorbing differences; verify dialog screenshots sample (guild assign, player item/pal/tech, fix-illegal pair) rather than all.
- [Removing the 170px reserve changes every page's alignment] → Landing together with the page-header grammar so rows realign once, not per-page ad hoc.
- [Frameless drag/resize regressions] → App-bar drag mirrors existing `_hit_window_drag_zone` logic; maximize/restore and Esc behaviors covered by smoke pass.

## Migration Plan

Phased, each phase shippable: (1) foundations — fonts/weights, icon factory, bug-fix batch, status strip; (2) app bar + window controls + branding, gutter removal; (3) nav strip + zone regrouping, retire rail/tray behind facades; (4) page-skeleton adoption across pages; (5) cleanup — delete NexusBand/InstrumentTray, glyph backend, `nerdfont` dependency, legacy QSS tail. Rollback: each phase is a separate commit set; Phase 2-3 can revert to the v2 shell via the feature branch.

## Open Questions

None blocking. Compact-label cutoff widths and the exact app-bar heights (44/48px) are tuned during implementation with screenshots, per the spec's state requirements rather than fixed numbers here.
