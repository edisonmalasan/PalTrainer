# 008-plan — Separate toolsets, maps, coordinates, and XGP infrastructure

## Objective

Split tool workflows into pure operations, platform adapters, and UI wrappers.

## Tasks

- Extract conversion, transfer, host repair, map restoration, and slot injection operations.
- Isolate Xbox/Game Pass discovery, container parsing, compression, cloud sync, firewall, and elevated operations.
- Keep coordinate transforms and UUID normalization in explicit modules.
- Make network and elevated behavior opt-in and visible.
- Preserve Steam/XGP payload equivalence, container metadata, map transforms, dynamic IDs, and legacy exports.

## Files and areas

`src/palworld_toolsets/`, `src/palworld_xgp_import/`, and `src/palworld_coord/`.

## Dependencies

`003-plan`, `004-plan`, `005-plan`, `007-plan`.

## Acceptance

Tool operations run independently of dialogs and have explicit platform, storage, and error boundaries.

