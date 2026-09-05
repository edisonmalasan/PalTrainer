# PalTrainer UI System Reference

The implementation guide for the Deck Operations UI (plans 019–025). Read
`docs/plan/ui/000-design-context.md` for the design thesis and decision log;
this page is the *how to build* companion.

## 1. Palette & tokens

Single source: `src/palworld_aio/ui/chrome/tokens.py`.

- `PALETTES['dark']` — warm-dark surfaces (`#141312` canvas), amber accent
  `#F59E0B` (interactive only), teal success `#2DD4BF`, warm-gray text.
- `resolve(theme)` → palette dict. `TYPE` (px/weight per role), `SPACING`
  (4px grid), `RADIUS (3/5/8/pill)`, `HEIGHT`, `ROW` scales.
- Transitional aliases (`ACCENT_BG`, `SURFACE`, …) derive from the palette —
  do not add new hard-coded hex outside the chrome modules whitelisted by
  `scripts/scrs/check_theme_violations.py` (`tokens/qss_builder/fonts/icons/
  styles/nexus_band/instrument_tray`).
- `palworld_aio/constants.py` is a compatibility layer (values mirror the
  palette; pinned by `tests/unit/palworld_aio_tests/test_constants.py`).
- Game-data colors (rarity 1–5, elements, rank) are a **data contract** —
  never restyle them.

## 2. Typography

- Bundled TTFs in `resources/assets/fonts`: Hanken Grotesk (display/headings/
  nav; stack `['Hanken Grotesk','Segoe UI']`), Inter (body; the shipped file
  registers as family **“Inter 28pt”** — stack
  `['Inter 28pt','Inter','Segoe UI']`), Hack Nerd Font (icons).
- Registered **once** by `chrome/fonts.py::load_app_fonts()` (every TTF in
  the folder); per-widget font loading is banned.
- QSS receives stacks via `font_family_qss()`; weights come from `TYPE`.
- Minimum sizes: 10px micro / 12px body; Hanken ≥ 13px for headings.

## 3. QSS pipeline

`chrome/qss_builder.py::build_qss(theme)` generates the global stylesheet →
`scripts/scrs/build_theme.py` concatenates it with the transitional extras in
`resources/ui/themes/legacy-dark.qss` → writes `resources/ui/themes/darkmode.qss`
(loaded at runtime by `ThemeManager.apply_global()`).

Rules of the road:

1. Never edit `darkmode.qss` by hand; edit `qss_builder.py` (or the extras)
   and run `uv run python scripts/scrs/build_theme.py`.
2. Widgets style themselves with **objectNames + dynamic properties only**;
   the builder turns properties into states
   (`QPushButton#x[active="true"]:hover {…}`). No `setStyleSheet` with hex.
3. Every interactive control defines default/hover/pressed/focus/disabled.
4. PyQt6 enums are scoped: `Qt.TextFlag.TextWordWrap`, `Qt.AlignmentFlag…`.
   Unscoped access inside `paintEvent` aborts the process natively.

## 4. Shell anatomy (v2)

`ui/main_window.py::_setup_ui_v2` builds:

- **Page canvas** — `QStackedWidget` (12 lazy pages, `_TAB_SETUP`,
  `_ensure_tab`, `_on_nav_changed` mapping unchanged from the legacy app).
- **NexusBand** (`chrome/nexus_band.py`, right edge, 76px): masthead (menu +
  dirty dot + update pulse) → 12 nav destinations grouped into zones →
  InstrumentTray → utilities (console / guide / warnings / about).
- **InstrumentTray** (`chrome/instrument_tray.py`): save-state row (click =
  save; spinner on loading/saving), selection rows (player/guild/base),
  metrics row, expand affordance.
- **TrayDrawer** (canvas-local overlay child of the stacked widget): full
  `StatsPanel` before/after/result grid; opened by band expand or metrics;
  closed by X or Esc (`_on_global_escape`).
- **WindowControls** (`chrome/window_controls.py`): floating min/max/close
  pinned top-right; repositioned in `resizeEvent`.
- **Page ribbon** (`components.create_page_ribbon`): per-page title + zone
  label + actions; right padding reserved for the window controls.
- Frameless window drag: top 52px of the canvas (`_hit_window_drag_zone`).

Keyboard: band Up/Down/Enter; `Ctrl+1..9`/`Ctrl+0` jump pages; `Esc` closes
the drawer (no-op while a modal is active).

## 5. Dialog grammar (022)

`components.BaseDialog`: kicker (micro, upper) → title (Hanken) → hairline →
content zone → footer with **danger actions isolated left**
(`add_confirm_button(danger=True)` / `add_danger_button`) and
cancel/primary right. QMessageBox-family stays for standard dialogs.

## 6. Table grammar (023)

`widgets/search_panel.py`: filter row (title + `#searchInput` + live
`#searchCount`) → full-bleed dense `QTreeWidget` (28px rows, token zebra) →
`#tableFooter` context strip (hint text left, actions right via
`footer_slot`). Sorting, `add_item`, selection signals unchanged. Exclusions
use a segmented `#pageSwitchBtn` control over one stack.

## 7. Settings keys

Active: `language, show_icons, boot_preference, console_detached,
console_window_geometry, loading_screen_mode, tray_expanded`
(+ legacy keys tolerated in existing user.cfg files but no longer read:
`sidebar_collapsed, right_panel_visible, splitter_sizes, use_nexus_shell`).

## 8. Verification

- `uv run pytest -c tests/pytest.ini` (+ `-m slow`), `compileall`, `pyright`,
  theme scanner (`scripts/scrs/check_theme_violations.py`, baseline 1353).
- Offscreen smoke: `scripts/scrs/smoke_final.py` (writes `Logs/smoke_final.txt`;
  never `print()` — MainWindow redirects stdout) and
  `scripts/scrs/smoke_start_v2.py`.
- Screenshot-based visual QA is pending manual review — see
  `docs/plan/ui/000-visual-qa.md`.
