# 020 — Shell v2: NexusBand, Page Ribbons, InstrumentTray

> **Status: ACTIVE — implements the shell portion of the 019 design reset.**
> Supersedes plan 004 (shell & navigation), which is REJECTED as a design
> decision (it preserved sidebar/header/dock topology). Reusable infra from
> 004: save-state chip logic, keyboard nav pattern, splitter persistence idea
> (now obsolete), QSS generation contract.

## 1. Objective

Replace the old shell — persistent left sidebar + global header + right
Results dock — with the Deck Operations shell: full-bleed page canvas + right
**NexusBand** instrument rail + per-page **ribbons**. Functionality of the old
sidebar, header, results dock, and console must remain reachable.

## 2. Scope

**In scope:** `chrome/nexus_band.py` (new), `chrome/instrument_tray.py` (new),
`ui/main_window.py` shell rewiring, `chrome/qss_builder.py` shell rules,
retirement of `sidebar_widget.py`/`results_widget.py`/`header_widget.py` from
the live tree (kept during transition via setting), page-ribbon component.

**Out of scope:** page content layouts (021+), dialog strategy (022).

## 3. Functionality inventory to preserve (from audit)

Old sidebar: 12 nav destinations (page ids `tools, map, base_inventory,
player_inventory, pal_editor, players, guilds, bases, exclusions, json_editor,
breeding, docs`), collapse toggle, console toggle, results toggle, keyboard
nav (Up/Down/Enter), `refresh_labels()`, `set_lock_state()` no-op,
`set_active()` deep-link target (`tools_tab.py:338`, `main_window.py:249,1922,2438`).

Old header: menu popup (`MenuPopup` with full action tree), version chip
(GitHub link + update pulse), game-version chip, save-state chip (ShellState
lifecycle), warn button, toolbox button (TabGuide), save button, dirty
emphasis, loading spinner, discord link, min/max/close window controls,
frameless drag.

Old results dock: `set_player/set_guild/set_base/clear_selection`,
`update_stats`, `refresh_stats_before/after`, `refresh_labels`,
`hide_requested` → visibility toggle persisted in settings; stats
before/after deltas (`StatsPanel`).

Console: detach/attach lifecycle (`StatusBarStream`), settings persistence,
`set_console_visible` sync.

## 4. Component design

### 4.1 NexusBand (`chrome/nexus_band.py`) — right edge, 76px fixed

Vertical rail, one column, altitudes top→bottom:

1. **Masthead (28px):** app monogram glyph (Nerd Font) + dirty dot (amber,
   property `dirty="true"` when `constants.dirty`).
2. **Navigate zone:** 12 destination buttons, icon (16px) over micro-label
   (9px Inter, `t()`), grouped by mission zones with 6px gap + 1px rule
   between zones: Load/Inspect (`tools`, `map`), World (`base_inventory`,
   `players`, `guilds`, `bases`, `exclusions`), Edit (`player_inventory`,
   `pal_editor`, `json_editor`), Reference (`breeding`, `docs`).
   Active state: amber text/icon + 2px amber **corner-notch** on the right
   edge pointing inward (painted, replaces left accent bar). Hover: warm
   surface. Tooltip = full label (for narrow rail).
3. **Tray altitudes (stretch area):** InstrumentTray embeds here (see 4.2).
4. **Utilities (bottom):** console toggle (inline log pane toggles as overlay
   drawer), guide (TabGuide), about.

API (compat with old callers):
`nav_changed(str)`, `console_toggled()`, `tray_expanded_changed(bool)`,
`collapsed_changed` (kept, always False, for settings compat),
`set_active(id)`, `set_console_visible(bool)`,
`set_right_panel_visible(bool)` (maps to tray expanded),
`refresh_labels()`, `set_lock_state()` no-op.

### 4.2 InstrumentTray (`chrome/instrument_tray.py`)

Rail sections between nav and utilities:

- **Save altitude:** compact state row (icon + micro label; LOADING spinner /
  LOADED teal check / DIRTY amber dot / SAVING spinner / ERROR danger x) —
  click = save action (replaces header save button; dirty pulses).
- **Selection altitude:** three micro rows PLAYER / GUILD / BASE with values
  from `set_player/set_guild/set_base` (same call sites), em-dash placeholder,
  2-line ellipsis.
- **Statistics altitude:** 4 mini metrics (players/guilds/bases/pals) with
  delta arrows after operations; **Expand** opens the **TrayDrawer**.
- **TrayDrawer:** canvas-local overlay frame (child of central widget, right
  side, 360px, over scrim; NOT a separate window) with full `StatsPanel`
  (before/after deltas), copied on Copy. Close: X / Esc / scrim click.

### 4.3 Header retirement → distributed chrome

- Window controls (min/max/close) + frameless drag: thin 34px **canvas-top
  strip** integrated in each page ribbon (drag area = ribbon; controls at
  window top-right, owned by a small `WindowControls` widget reused per page).
- Menu popup: `NexusBand` masthead click opens `MenuPopup` (same widget).
- Version chip + update pulse: **Start page masthead** (021); warn/guide/about:
  band utilities; save state: tray altitude.
- `header_widget.set_shell_state` call sites → `tray.set_shell_state`
  (main_window keeps a shim method so all existing call sites compile).

### 4.4 Page ribbon (shared, in `chrome/components.py`)

`create_page_ribbon(title_key, zone_key, actions=None) -> ribbon`:
19px Hanken title, micro zone label, stretch, page action slots, window
controls at far right (window-level, not per page — see implementation note:
a single `WindowControls` overlay pinned top-right above the canvas; ribbon
reserves right padding 150px).

## 5. main_window rewiring

- `_setup_ui`: `central` → page `stacked_widget` (full width) + `nexus_band`
  (right, 76px) in a QHBoxLayout. No splitter. No `ResultsWidget`.
  `status_bar` hidden-console behavior unchanged.
- Shim methods kept on MainWindow for all legacy call sites:
  `results_widget` → property returning tray facade implementing
  `set_player/set_guild/set_base/clear_selection/update_stats/
  refresh_stats_before/refresh_stats_after/refresh_labels/hide_requested`;
  `sidebar` → property returning band facade (`set_active`,
  `set_console_visible`, `set_right_panel_visible`, `refresh_labels`,
  `nav_changed` signal). Old widgets stay importable for tests but are not
  constructed.
- User settings: `sidebar_collapsed` ignored (kept in file); new
  `tray_expanded` (default False). `right_panel_visible` maps to
  `tray_expanded` on first run.
- Legacy construction path: if `user_settings['use_nexus_shell'] is False`,
  build the old shell (kept code path) — rollback hatch for 025 closeout.

## 6. QSS (qss_builder shell section rewrite)

New rules: `#nexusBand` (canvas tone, left hairline border), `#bandItem`
(states: hover surface, active amber text + painted notch, disabled),
`#bandZoneRule`, `#bandMasthead`, `#traySection`, `#trayLabel`, `#trayValue`,
`#trayMetric`, `#trayDrawer` (surface_raised + border_strong + shadow
token-allowed for floating), `#windowControls` buttons, page ribbon
`#pageRibbon` (transparent, bottom hairline). Old `#sideBar`,
`#resultsWidget`, header chip blocks deleted from builder; corresponding
legacy-dark.qss blocks pruned where they target retired objectNames
(`#sideBar` etc. remain only inside the legacy construction path guard —
verify scanner count falls).

## 7. Implementation tasks

1. `chrome/nexus_band.py` + `chrome/instrument_tray.py` (+ scanner whitelist).
2. `chrome/components.py`: `create_page_ribbon` + `WindowControls`.
3. `main_window.py` rewiring + facades + settings mapping + legacy path guard.
4. `qss_builder.py` shell section rewrite; prune retired blocks;
   `scripts/scrs/build_theme.py` rebuild.
5. Menu/keyboard: Up/Down/Enter nav on band (port from old sidebar);
   Ctrl+1..9/Ctrl+0 page jumps (new; documented in TabGuide later).
6. Remove `DropOverlay` re-parent assumptions if any (it parents to window;
   unchanged).

## 8. Behavior preservation checklist

- All 12 page ids + lazy `_ensure_tab` flow + `_on_nav_changed` map unchanged.
- `nav_changed` emitted on click and keyboard; deep links
  (`set_active('map')` etc.) work.
- Save lifecycle states reach the tray (same `ShellState` values).
- `set_dirty` → masthead dot + tray state.
- Menu popup identical (same `MenuPopup` widget, now masthead-triggered).
- Update pulse moves to Start masthead (021); interim: pulse property on
  masthead glyph in band.
- Console detach/attach flow unchanged; band button syncs via
  `set_console_visible`.
- Window drag: ribbon/empty-canvas drag (port existing mousePress logic,
  extended to ribbon), controls wired to same slots.
- TabGuide, about, warnings, discord reachable (band utilities; discord moves
  to MenuPopup row).
- Splitter persistence code removed; `splitter_sizes` setting ignored.

## 9. Tests

- Smoke (offscreen): window builds with band; 12 band items emit nav_changed
  in order; facades respond to `set_active`/`set_player`/`update_stats`;
  TrayDrawer opens/closes; Esc closes drawer; settings roundtrip
  (`tray_expanded`); legacy path still constructs when setting off.
- Unit: band keyboard nav; tray state mapping (ShellState → icon/property).
- Full suite + compileall + pyright delta + scanner ≤ 1390.

## 10. Visual QA

Code-based only (see 019 §11): structural assertions (no `#sideBar`,
no `#resultsWidget` in live tree; band rightmost; drawer is canvas child),
offscreen screenshots saved for manual review. Screenshot-based QA pending.

## 11. Risks

- Facade drift: legacy call sites use attribute access (`self.sidebar.x`,
  `self.results_widget.stats_panel.refresh_labels()` at main_window:2048) —
  facade must expose `stats_panel` too.
- Frameless drag over ribbon must not steal button clicks (hit-test text
  labels only).
- TrayDrawer over content must not grab focus from tables (non-modal,
  click-through scrim closes).

## 12. Rollback

Single setting (`use_nexus_shell=false`) restores legacy construction; band/
tray modules are additive files; main_window diff isolated to `_setup_ui` +
facades.
