# UI Overhaul Progress

## Current Status

Current phase: IMPLEMENTATION COMPLETE (plans 019–025 incl. geometry-r02
for the three heavy screens). Remaining: manual visual review by the user.

Status: COMPLETE (pending manual visual QA)

## Completed

- [x] Session startup protocol + evidence audits (sessions 2–3)
- [x] Mandatory Overhaul Reset (rejections, banners, design-context §0)
- [x] 019 — design reset (thesis v2, divergence matrix, palette v2, fonts v2)
- [x] 020 — shell v2 (NexusBand, InstrumentTray, TrayDrawer, WindowControls,
      page ribbons, QSS shell rewrite)
- [x] 021 — Start page v2 (masthead, field report, campaign strip, missions)
- [x] 022 — dialog strategy (sheet grammar, danger isolation, QSS)
- [x] 023 — table strategy (SearchPanel full-bleed, footer strips, counts)
- [x] 024 — a11y (Ctrl+1..9/0 jumps, Esc drawer, focus states)
- [x] Screen revisions: 007-r02 (via 023), 008-r02 (Map canvas-first +
      floating legend), 012-r02 (Breeding), 013-r02 (JSON desk), 014-r02
      (Exclusions segmented), 015-r02 (Docs shelf)
- [x] Palette migration of the three heavy screens (base 168, inventory 213,
      pal-editor family ~123 literals) + chrome/styles.py constants sweep
- [x] 025 — close-out: legacy chrome files deleted (sidebar_widget/
      header_widget/results_widget); NerdBtn/NerdLabel relocated to
      components; facades + `_setup_ui_legacy` + `use_nexus_shell` removed;
      all call sites direct to band/tray/controls; legacy-dark.qss purged
      (80 dead blocks, 16.3 kB → 5.0 kB); default settings pruned;
      docs/ui-system.md written; test_registry verified (dynamic loader)
- [x] 000-visual-qa.md ledger maintained

## In Progress

- (none)

## Rejected or Needs Revision

- 004–007 REJECTED; 002–003 infra-only; 008–018 originals FROZEN
  (superseded by -r02 revisions).
- Geometry-level r02 completed for Base Inventory (ribbon + segmented view
  switch + context row), Player Inventory (ribbon + tokenized action
  buttons), Pal Editor tab (ribbon). Residual: inner-zone workbench
  recomposition of pal_editor_widget (optional polish, palette done).

## Next Task

Manual visual review of `Logs/*.png` captures (shell_v2_shot, start_v2_shot,
page_*.png) by the user or an image-capable agent, per the checklist in
000-visual-qa.md. Any geometry-r02 passes the review calls for would then be
planned as new -r03 revisions.

## Important Notes

- Work only on `feat/ui-overhaul`; nothing committed (per instructions).
- `ib/image` screenshots and rendered captures are both unreadable here
  (no image input) — never claim screenshot-based visual QA
  (design-context §2).
- Fonts: Inter registers as "Inter 28pt" (stack ['Inter 28pt','Inter',
  'Segoe UI']); loading centralized in chrome/fonts.py.
- PyQt6 offscreen gotchas: scoped enums only (unscoped in paintEvent aborts
  natively); QStylePainter/QStyleOptionButton live in QtWidgets.
- Scanner baseline: 1352 (was 1390 at session start, 1353 before styles
  sweep).
- pyright: **522** — below the 523 main baseline (legacy-file deletion
  removed 4 errors).
- darkmode.qss is generated: edit qss_builder.py + legacy-dark.qss, run
  `uv run python scripts/scrs/build_theme.py`.
- Smoke recipe: `scripts/scrs/smoke_final.py` / `smoke_start_v2.py`
  (results to Logs/*.txt; stdout is redirected).
- Legacy settings keys tolerated but unread; `use_nexus_shell` removed.
- UI system reference: docs/ui-system.md.

## Last Verified State (end of session 3 close-out, 2026-09-04)

- `uv run pytest -c tests/pytest.ini` -> 464 passed, 20 deselected
- `uv run pytest -c tests/pytest.ini -m slow` -> 20 passed
- `uv run python -m compileall -q src tests scripts` -> OK
- `uv run pyright src` -> 522 (below main baseline 523)
- Theme scanner -> 1352 (44 files; down from 1390)
- validate_imports -> all 16 modules OK
- smoke_final -> PASS (12/12 pages, 10 shortcuts, search counts, exclusions
  switch, drawer Esc, 4-language cycle, DPR grab, 7 screenshots)
- smoke_start_v2 -> PASS (masthead/field report/campaign/missions wired)
- Deleted: ui/chrome/sidebar_widget.py, ui/chrome/header_widget.py,
  ui/chrome/results_widget.py (imports migrated; suite green)

Known issues:

- Screenshot-based visual QA pending manual review.
- 31 legacy-dark.qss blocks remain for screens awaiting geometry r02.
- chrome/styles.py constants are warm-palette now but remain a parallel
  styling path (QSS builder is canonical; long-term merge optional).
