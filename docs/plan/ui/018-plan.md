# Plan 018 — Regression Testing, Cleanup, Documentation

## Objective

Close out the overhaul: remove obsolete styles/widgets, verify save-data invariants
and all workflows, run the full verification battery, and document the new UI system.

## Scope

- Cleanup: orphaned widgets (`SortableTreeWidget`, `CollapsibleSplitter`,
  `ScrollableMenu`, dead `LoadingOverlay` if still unused, dead
  `SearchPanel.search_requested`), old QSS constants in `chrome/styles.py` whose
  consumers are gone, scanner whitelist entries no longer needed
  (`edit_pals.py`, `editor/edit_pals.py`), literal 'Segoe UI' in
  loading_popup.py/menu_popup.py (now via fonts.py).
- Tests: new unit tests for tokens/qss builder; updated `test_constants.py`;
  registry updates; regression run.
- Docs: `docs/ui-system.md` (design system reference for future contributors).

## Dependencies

Plans 002–017 complete.

## Tasks

1. **Cleanup**: delete dead code (verify zero references first via grep + import
   graph validator); delete superseded QSS constants; tighten scanner whitelist;
   run scanner in ruthless mode and triage the remainder honestly (document any
   accepted violations in PROGRESS.md with reasons).
2. **Regression battery** (all must be run, results recorded in PROGRESS.md):
   - `uv run python -m compileall -q src tests`
   - `uv run pytest -c tests/pytest.ini` (full, non-slow)
   - `uv run pytest -c tests/pytest.ini -m slow` (save I/O roundtrips)
   - `uv run pyright src`
   - Scanner: `uv run python scripts/scrs/check_theme_violations.py` (and `--ruthless` report)
3. **Workflow regression walkthrough** (manual, fixture saves only): save load
   (Steam path + Game Pass path if available), conversion, backups, atomic replace,
   player/guild/base selection, map navigation, inventory editing, item selection,
   Pal creation/editing/placement, breeding calc, stat tooltips, JSON read-only +
   guarded import, exclusions, slot injection, results/stats updates, modal dialogs,
   background workers (DPS scan), error reporting, console detach.
4. **Documentation**: `docs/ui-system.md` — tokens, fonts, components, QSS builder
   usage, rules for new screens ("never setStyleSheet; use properties + builder"),
   theme extension guide.
5. **Final report**: changed-files list, intentionally-unchanged list, screenshots
   index, known limitations — into PROGRESS.md + final session summary.

## Behavior-preservation requirements

- Save serialization/roundtrip untouched; filesystem/backup/atomic behavior
  untouched; if any check fails, fix before declaring completion.

## Tests and verification

- Everything in task 2; plus re-run of every focused suite touched by plans 004–016.

## Visual QA requirements

- Final screenshot set for every screen (light: N/A dark-only), stored under
  `docs/plan/ui/screenshots/` (gitignored if real save data visible — fixture data
  only).

## Completion criteria

- All checks green (or failures honestly documented with root cause + decision).
- Docs complete; scanner clean outside whitelist; dead code removed.

## Known risks

- Slow tests require native save deps — if environment lacks them, record as
  blocked verification rather than skipping silently.
- Screenshot files must never contain real save data (AGENTS security rule).
