# UI Overhaul Progress

## Current Status

Current phase: 008 - Base Inventory
Status: NOT STARTED (007 complete; session ended after 007)

## Completed

- [x] Plans 001-018 + 000-index + 000-design-context
- [x] 002 - Design system foundation (tokens, fonts, qss_builder, generated darkmode.qss,
      legacy extras split, ThemeManager theme-aware; 8 token tests)
- [x] 003 - Component library (components.py; toggle_check tokenized; 7 tests)
- [x] 004 - Shell & navigation (header save-state chip; sidebar sections+keyboard; console)
- [x] 005 - Dashboard (Tools tab fully tokenized, 0 inline styles)
- [x] 006 - Results Panel & Statistics Panel (placeholder states, copy/close buttons)
- [x] 007 - Search screens + GuildAssignDialog + pal-name settings + console title

## In Progress

- (none - next session starts plan 008)

## Next Task

Plan 008 per docs/plan/ui/008-plan.md (base_inventory_tab.py, 4176 ln, 123 inline
styles): container list pane -> item grids (shared RarityBorderDelegate) -> pickers on
BaseDialog -> economy stats. Migrate pane-by-pane with compile+launch between panes.
Then 009 (Map), 010 (Pal Editor), 011 (Player Inventory), 012-015, 016 (dialogs),
017 (a11y), 018 (regression/cleanup/docs).

## Important Notes

- Do not redesign established decisions in 000-design-context.md without documenting.
- Existing save workflows must remain unchanged (see §9 invariants).
- Use centralized tokens; avoid per-screen QSS duplication.
- darkmode.qss is a build artifact: edit qss_builder.py + legacy-dark.qss, then run
  `uv run python scripts/scrs/build_theme.py`.
- QSS contract: builder owns GLOBAL element rules + migrated screen chrome;
  legacy-dark.qss owns remaining objectName-specific rules (~111 blocks) until
  screens migrate (extras shrink per plan; delete file in plan 018).
- MainWindow redirects sys.stdout/stderr (StatusBarStream) - smoke-test scripts must
  write results to a file, not print.
- Smoke test recipe: insert src + src/<subpkg> paths like main.py does; offscreen Qt;
  i18n.init_language('en_US') before MainWindow; write results to a file.
- Scanner baseline on main: 1442; branch: 1390 (falls per migrated file).
- pyright: 523 errors on main, 524 on branch - the delta is line-shift noise in the
  pre-existing reportIncompatibleMethodOverride convention (verified by error-set
  diff: no new error classes). Do not mass-rename override params during migration.
- Session continuity: read 000-index.md + 000-design-context.md + this file first.

## Last Verified State (end of session 1, 2026-09-03)

- `uv run pytest -c tests/pytest.ini` -> 463 passed, 20 deselected
- `uv run pytest -c tests/pytest.ini -m slow` -> 20 passed (save I/O roundtrips)
- `uv run python -m compileall -q src tests scripts` -> OK
- `uv run pyright src` -> 524 (main baseline 523; delta = shifted-line noise of
  pre-existing errors; zero new error classes; new chrome files: 0 errors)
- Theme-violation scanner -> 1390 (main baseline 1442)
- Smoke tests (offscreen): shell build + sections + save-state chip; tools tab
  (7 tools, stat deep-links, status property transitions); results/stats panels
  (placeholder semantics, copy button); search screens (filter machinery, guild
  dialog assign-gating); fonts registered (Hack Nerd Font); theme applied (45 kB QSS)

Known issues:
- 15 baseline screenshots supplied by user could not be read by this session
  (model has no image input); analysis relies on code/QSS audit instead. Visual QA
  must be performed by launching the app (test.cmd / uv run start.py).
- QStackedWidget legacy 2px accent border replaced by flat transparent surface.
