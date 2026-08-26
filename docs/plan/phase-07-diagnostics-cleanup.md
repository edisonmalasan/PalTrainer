# Phase 07 — Diagnostics, Cleanup & Repair Suite

**Goal:** Server/admin tools complete, auditable, recoverable.

**Source:** `managers/func_manager.py` 56 exports (`delete_*`, `fix_*`, `reset_*`), `save_diagnostic.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 07.1 | `feat/diagnostic-report-models` | `diagnostics/mod.rs` 22 `DiagnosticCategory`, `DiagnosticIssue`, `ReportDto` | diagnostic model tests |
| 07.2 | `feat/diagnostic-scan-commands` | `inspect::run_save_diagnostics` + `run_targeted_diagnostic` | scanner tests |
| 07.3 | `feat/diagnostics-dashboard-view` | `DiagnosticsView` 6 metric cards + scrollable findings list | `DiagnosticsView` |
| 07.4 | `feat/cleanup-commands` | `cleanup::preview/commit` 11 `CleanupTarget` | cleanup preview |
| 07.5 | `feat/repair-commands` | `repair::preview/commit` 12 `RepairTarget` | repair preview |
| 07.6 | `feat/reset-and-gameday-commands` | `reset::preview/commit` 7 `ResetTarget` + `PalDefender` | reset tests |
| 07.7 | `feat/cleanup-repair-tools-view` | `CleanupPanel/RepairPanel/ResetPanel/PalDefenderPanel` 5-tab workbench | panels e2e |

**Skills:** Use `deleteLater` guard notes from PST `AGENTS.md`.

**Outcome:** Every delete/repair/reset has preview, scoped selection, backup, audit.
