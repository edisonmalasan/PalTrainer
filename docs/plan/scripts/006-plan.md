# 006-plan — Decompose mutation, repair, cleanup, and diagnostics

## Objective

Replace the monolithic function manager with intent-named, independently testable operations.

## Tasks

- Split cleanup, illegal-data repair, diagnostics, death-bag handling, exclusions, resets, and world-index maintenance.
- Introduce structured operation results with changed entities, warnings, deleted files, and confirmation requirements.
- Separate preview from commit for destructive operations.
- Move thread and process coordination to infrastructure.
- Preserve current algorithms, fallback behavior, and user-visible errors until each operation is covered.

## Files and areas

`src/palworld_aio/managers/func_manager.py`, diagnostic helpers, exclusion handling, and `src/palworld_toolsets/save_diagnostic.py`.

## Dependencies

`004-plan`, `005-plan`.

## Acceptance

Each operation has a narrow interface, predictable result, and focused regression coverage.

