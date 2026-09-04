# 025 — Regression, Cleanup, Documentation, Close-out

> **Status: ACTIVE.** Replaces frozen 018 scope.

## 1. Objective

Declare the overhaul complete only after regression coverage, transitional
debt removal, documentation, and the verification-vocabulary report.

## 2. Scope

1. **Regression:** full pytest (+slow), compileall, pyright delta vs main
   523 baseline, scanner ≤ 1390 and falling, all smoke scripts green.
2. **Cleanup:**
   - delete `use_nexus_shell=false` legacy construction path
     (`_setup_ui_legacy`), then `chrome/sidebar_widget.py`,
     `chrome/header_widget.py`, `chrome/results_widget.py` after facade
     call-site migration (`sidebar.*`/`results_widget.*`/`header_widget.*`
     → `nexus_band.*`/tray/controls across `src/`);
   - delete facades `_SidebarFacade/_ResultsFacade/_HeaderFacade`;
   - prune retired settings keys (`sidebar_collapsed`, `right_panel_visible`,
     `splitter_sizes`) read-sites;
   - delete `legacy-dark.qss` once empty; drop from build_theme;
   - remove remaining `glass`/`saveCard`-era objectName blocks.
3. **Documentation:** ui-system reference (README section or docs page):
   token usage, QSS pipeline, font loading, shell anatomy, dialog/table
   grammar; finalize 000-design-context (decision log completion).
4. **Completion report:** distinguish implementation / functional /
   code-based-structural / screenshot-based verification; visual QA marked
   pending until human or image-capable agent reviews `Logs/*.png` + live app.
5. **test_registry:** ensure moved/new modules registered.

## 3. Tests

Everything in §2.1; plus import-graph check (validate_imports) post-deletion.

## 4. Rollback

Closeout is one commit-range; revert restores transitional files.
