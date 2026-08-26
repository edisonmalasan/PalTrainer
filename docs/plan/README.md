# PalTrainer Plan Index

This folder is the authoritative breakdown of `docs/PLAN.md`.

* `docs/PLAN.md` — overview + principles + architecture (the *why*, keeps <80 lines).
* `docs/plan/phase-*.md` — one file per phase (the *what* and *how*, broken into tasks).

One feature branch per task, one merge commit per PR: `Merge pull request for <branch> into main`.

## Phase Map

| Phase | Title | Status | Branch Prefix |
|-------|-------|--------|---------------|
| 01 | Project Foundation | Done | — |
| 02 | Save Engine & Roundtrip Core | Partial | `feat/save-*`, `feat/gvas-*` |
| 03 | Sessions, Backups & Safety | Done | `feat/save-session-*` |
| 04 | Read-Only Workbench & Resources | Partial | `feat/read-only-*` |
| 05 | Core World Editing | Scaffolded | `feat/player-*`, `feat/guild-*`, `feat/base-*` |
| 06 | Pal, Inventory & Containers | Scaffolded | `feat/pal-*`, `feat/inventory-*` |
| 07 | Diagnostics, Cleanup & Repair | Scaffolded | `feat/diagnostics-*` |
| 08 | Conversion, Transfer & XGP | Scaffolded | `feat/conversion-*`, `feat/xgp*` |
| 09 | UI/UX Refinement | In progress | `feat/ui-*`, `feat/navigation-*` |
| 10 | Test Hardening, Packaging & Release | 10.1-10.8 Done | `test/*`, `feat/windows-packaging`, `ci/*` |
| 11 | Drag-Drop, Recent Paths & GPS | Next | `feat/session-*` |
| 12 | Rust Pipeline Hardening | Planned | `feat/save-*`, `feat/rawdata-*` |
| 13 | Resource Bundling | Planned | `feat/resources-*` |
| 14 | Inventory & Dynamic Containers | Planned | `feat/inventory-*` |
| 15 | Pal Editor Parity | Planned | `feat/pal-*` |
| 16 | Map Canvas | Planned | `feat/map-*`, `feat/zone-*` |
| 17 | Diagnostics Realization | Planned | `feat/diagnostics-*` |
| 18 | Tooling UX | Planned | `feat/tools-*` |
| 19 | Shell Polish (14 screenshots) | In progress | `feat/ui-*`, `feat/design-system-*` |
| 20 | Docs & i18n | Planned | `feat/docs-*` |
| 21 | Perf, A11y & Command Palette | Planned | `feat/a11y-*`, `feat/keyboard-*` |
| 22 | Release & Updater | Planned | `feat/packaging-*` |

## How to Use

1. Pick next unchecked task in current phase file.
2. `git switch -c <type>/<short-description>` (kebab, `feat/`, `fix/`, `docs/`, `test/`, `ci/`).
3. Implement one task, run `pnpm lint typecheck test` + `cargo fmt clippy test`, Conventional Commit, push, open PR.

## Source Coverage

All phases map to `docs/PalworldSaveTools` areas in `docs/PLAN.md` § Source Coverage (`README.md`, `src/palsav/`, `palobject.py`, `palworld_aio/`, `palworld_toolsets/`, `palworld_xgp_import/`, `palworld_coord/`, `resources/`, `tests/`).

## Definition of Done

Architecture + security rules, tests per risk, backup/stale/path/preview coverage for mutating behavior, `pnpm lint/typecheck/test` + `cargo fmt/clippy/test` pass.
