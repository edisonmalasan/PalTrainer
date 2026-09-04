# 024 — Accessibility, States, Resize, High-DPI, Localization

> **Status: ACTIVE.** Replaces frozen 017 scope, adjusted to shell v2.

## 1. Objective

Close the non-visual QA loop for the v2 UI: keyboard navigation completeness,
state coverage, resize/min-size correctness, high-DPI rendering, and
localization safety across 9 languages.

## 2. Scope

- Keyboard: band Up/Down/Enter (done in 020) + Ctrl+1..9/Ctrl+0 page jumps
  (QShortcut on MainWindow), Esc closes TrayDrawer, focus-visible QSS audit.
- States audit: every interactive control has hover/pressed/focus/disabled
  (+selected/checked) — sweep qss_builder.
- Resize: min 1200×750 verified with band; ribbons reflow; mission columns
  collapse; no clipping at 1024×768 fallback.
- High-DPI: Qt6 automatic; verify offscreen render at DPR 1.0/2.0 grabs.
- Localization: switch language to zh_CN/ja_JP/de_DE offscreen; assert no
  layout exceptions, no truncation in ribbons/tray (elide allowed), labels
  via `t()` everywhere (grep audit for raw strings in new chrome).

## 3. Implementation tasks

1. `main_window.py`: Ctrl+1..9/0 shortcuts mapping to page ids order;
   Esc shortcut closing drawer.
2. Focus QSS sweep: ensure `:focus` exists for bandItem, bandUtility,
   tray controls, missionRow, campaignStep, searchInput, footer buttons.
3. `scripts/scrs/smoke_a11y_v2.py`: shortcuts fire nav_changed; language
   switch cycle does not raise; DPR2 grab succeeds.

## 4. Tests / QA

- Smoke above; full suite; scanner; pyright delta.
- Visual: PENDING manual review (captures at DPR2 in Logs).

## 5. Risks

- Shortcut conflicts inside text editors — scope shortcuts to
  `Qt.WindowShortcut` with context checks (skip when a modal is active).
