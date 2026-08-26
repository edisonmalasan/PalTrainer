# PalTrainer Complete Remake Roadmap

This is the authoritative feature roadmap. Every implementation maps to a phase in `docs/plan/`. If a future task introduces new behavior, update the phase file first.

PalTrainer is a TypeScript + Tauri remake of `docs/PalworldSaveTools` — same scope, cleaner architecture, safer writes, polished workbench.

## Source Coverage

`README.md` (feature list), `src/palsav/` (SAV/GVAS, compression PLZ/PLM/CNK), `src/palobject.py` (dispatch, skip profile), `palworld_aio/*` (main window, 12 tabs, managers, inventory, editor), `palworld_toolsets/` (9 tools), `palworld_xgp_import/` (UWP ver14), `palworld_coord/` (Sakurajima + treemap + Z threshold), `resources/` (17 JSON, icons, maps, i18n, guides), `tests/` (206 `pytest`).

Skills: `tauri-development`, `design-taste-frontend-v1`, `pal-trainer-save-pipeline`, `pal-trainer-binary-schemas`, `pal-trainer-pal-editor`, `pal-trainer-stat-formula`, `pal-trainer-breeding`, `pal-trainer-cli-tools`.

## Principles

Complete scope staged, improve not clone, Rust owns files/parse/write/backup/stale/atomic, TypeScript owns UI/routing/filters/previews, typed `load_save`/`preview_*`→`commit_*` contracts, roundtrip sacred byte preservation, preview+backup+confirm for every destructive op.

## Architecture

- **Frontend:** `src/app/` + `src/features/{save-session,players,guilds,bases,pals,inventory,map,breeding,tools,diagnostics,docs}` + `src/shared/{components,hooks,types,utils}` — workbench `lg:grid-[240px_1fr]`, command palette, progress, diagnostics.
- **Backend:** `src-tauri/src/{commands,domain/pal_save,security,storage,tasks,resources}` — dialogs, path policy, GVAS, rawdata codecs, `SaveSession`, backup, audit.
- **Contracts:** Intent-named commands, DTOs privileged, projections paged, audit `{entities, files, backup, warnings}`.

## Phases (detail in `docs/plan/`)

| # | File | Title |
|---|------|-------|
| 01 | `phase-01-project-foundation.md` | Project Foundation |
| 02 | `phase-02-save-engine-core.md` | Save Engine & Roundtrip Core |
| 03 | `phase-03-sessions-backups-safety.md` | Sessions, Backups & Safety |
| 04 | `phase-04-readonly-workbench.md` | Read-Only Workbench & Resources |
| 05 | `phase-05-core-world-editing.md` | Core World Editing |
| 06 | `phase-06-pal-inventory.md` | Pal, Inventory & Containers |
| 07 | `phase-07-diagnostics-cleanup.md` | Diagnostics, Cleanup & Repair |
| 08 | `phase-08-conversion-transfer-xgp.md` | Conversion, Transfer & XGP |
| 09 | `phase-09-ui-refinement.md` | UI/UX Refinement |
| 10 | `phase-10-hardening-packaging.md` | Test Hardening, Packaging & Release |
| 11 | `phase-11-drag-drop-recent-gps.md` | Drag-Drop, Recent Paths & GPS |
| 12 | `phase-12-rust-pipeline-hardening.md` | Rust Pipeline Hardening |
| 13 | `phase-13-resource-bundling.md` | Resource Bundling |
| 14 | `phase-14-inventory-containers.md` | Inventory & Dynamic Containers |
| 15 | `phase-15-pal-editor-parity.md` | Pal Editor Parity |
| 16 | `phase-16-map-canvas.md` | Map Canvas |
| 17 | `phase-17-diagnostics-real.md` | Diagnostics Realization |
| 18 | `phase-18-tooling-ux.md` | Tooling UX |
| 19 | `phase-19-shell-polish.md` | Shell Polish (14 screenshots) |
| 20 | `phase-20-docs-i18n.md` | Docs & i18n |
| 21 | `phase-21-perf-a11y.md` | Perf, A11y & Command Palette |
| 22 | `phase-22-release-updater.md` | Release & Updater |

See `docs/plan/README.md` for branch prefixes and Definition of Done.
