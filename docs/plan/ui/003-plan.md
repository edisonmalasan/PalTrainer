# Plan 003 — Shared Component Library

## Objective

Build the reusable PyQt6 component layer that every screen migration consumes:
buttons, fields, panels, cards, tables/trees, chips/badges/status, dialogs,
empty/loading/error states, pickers, and toasts — all token-driven, all states
defined.

## Scope

- New: `src/palworld_aio/ui/chrome/components.py` (factories + widget classes).
- Migrate/upgrade: `src/palworld_aio/widgets/` (search_panel, stats_panel,
  empty_state, toggle_check, loading_popup, scrollable_context_menu, menu_popup,
  player_select_popup, hover overlays).
- Update: `chrome/styles.py` shared QSS constants to delegate to the builder tokens.

## Dependencies

Plan 002 (tokens, QSS builder, fonts).

## Components to deliver

### Buttons & controls
- `make_button(text, kind='default'|'primary'|'danger'|'ghost'|'tool', icon=None)`
  — 32px height (36 for primary CTA), Nerd Font icon support, full state set via QSS
  (default/hover/pressed/focus/disabled), `QPainter`-icon pattern reused from NerdBtn.
- `ToggleCheckBtn` restyle: token colors, token icon, 20px knob box, focus state.
- `styled_combo` restyle: popup = raised surface, item hover/selected states.

### Fields
- `make_search_input(placeholder, on_change)` — bordered field, inline search glyph,
  clear button, focus ring, disabled state.
- Field helpers for `QLineEdit/QSpinBox/QDoubleSpinBox/QComboBox` that only set
  properties (`error`, `compact`) — styling lives in QSS.

### Surfaces
- `make_panel(object_name, padding=16)` — level-1 raised surface (1px border).
- `make_card(...)` — panel + title row helper; used sparingly per anti-slop rules.
- `SectionHeader` — 13/600 label + optional trailing action; replaces ad-hoc headers.
- `HPolicy`/layout helpers respecting 4px grid (`SPACING` from tokens).

### Data views
- `DataTable(QTableWidget)` — dense 28px rows, no grid, hover row, accent left-border
  selected state, uppercase micro headers, sortable, per-column alignment, empty-state
  hook. Column widths: Interactive + last stretch.
- `SearchPanel` restyle (keep API/signals): search field via make_search_input,
  tree restyle, add `set_empty_state(title, hint)`; keep numeric-sort behavior;
  remove dead `search_requested` signal.
- `StatsPanel` restyle (keep API): tokenized labels, mono values, copy button variant.

### Status & feedback
- `Badge(text, level)` and `StatusDot(level)` — semantic colors from tokens.
- `Toast` (success/warning/error/info), bottom-right, parent-owned, auto-dismiss
  QTimer, removed on close (dialog-lifecycle rule).
- `EmptyState` upgrade: tokenized (already good), optional icon from registry,
  optional action button; used everywhere via one factory.
- `LoadingOverlay`/`LoadingPopup` consolidation: token colors, mono elapsed timer,
  phrase cycling kept; delete orphaned `LoadingOverlay` if unused by plan 018
  (kept until then).

### Dialogs
- `BaseDialog(QDialog)` — shared scaffold: title bar (title + close), content area,
  button row (Cancel / primary / danger), Esc-cancel, Enter-confirm, `no-modal`-safe
  sizing (`adjustSize()` + min sizes, never fixed frame sizes), parent-owned.
- `confirm(parent, title, message, kind='info'|'danger', confirm_text) -> bool` —
  replaces ad-hoc `QMessageBox.question` call sites across plans 006–016.
- `ErrorBanner` — inline, dismissible error surface for form/validation states.

### Popups
- `ScrollableContextMenu` restyle to token palette (behavior unchanged, incl.
  cursor-tracking hover and blocking exec pattern).
- `show_player_select_popup` restyle; keep API; keep blocking loop (documented
  fragility, change forbidden by invariants until a dedicated plan).

### Delegates
- Shared `RarityBorderDelegate` moved to components (single implementation;
  inventory/base_inventory duplicates converge on it in plans 009/010).

## Implementation tasks

1. Implement components.py factories/classes with type annotations.
2. Restyle widgets/ modules (API-compatible; consumers untouched this plan).
3. Extend unit tests: token-driven styles resolve, factory defaults, dialog
   scaffold behavior (offline instantiation where Qt allows).
4. Keep scanner green: no raw colors in components.py (whitelist chrome/ files only).

## Behavior-preservation requirements

- All existing public APIs and signals preserved (SearchPanel, StatsPanel, EmptyState,
  ToggleCheckBtn, ScrollableContextMenu, player_select_popup, SkillPicker untouched
  except token usage).
- No workflow changes; components are presentation only.

## Tests and verification

- `uv run python -m compileall -q src tests`
- `uv run pytest -c tests/pytest.ini`
- Launch app; exercise: search filtering, stats copy, context menus, empty states
  (load nothing → tools tab), a save load with loading popup.

## Visual QA requirements

Screenshot each component in isolation (test harness or manual): buttons all kinds
and states, fields normal/focus/error/disabled, table empty + populated, badges,
toast, empty state, dialog scaffold, context menu.

## Completion criteria

- No screen-specific QSS needed for buttons/fields/tables/dialogs in later plans.
- Scanner green; old QSS constants consumers still work (they now resolve to
  builder-generated values or remain until plan 018).

## Known risks

- Widget restyling can shift layouts (heights/padding); mitigation: keep exact
  heights from tokens, verify consumers at 1200×750 minimum window size.
- Blocking-loop popups restyled but behavior preserved — re-entrancy issues are
  pre-existing; do not "fix" here.
