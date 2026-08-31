# 001-plan — Freeze migration behavior and refactor contracts

## Objective

Define the behavior that every later structural change must preserve.

## Tasks

- Confirm the current Python/PyQt6 tree is the sole implementation baseline.
- Inventory GUI actions, CLI actions, save types, exports, imports, and tool workflows.
- Record load, reload, dirty, stale-file, backup, deletion, and save behavior.
- Restore `tests/save_test` when available, or create equivalent sanitized fixtures.
- Characterize current fallback and error behavior before changing control flow.
- Define compatibility checks for frozen builds and resource lookup.

## Files and areas

`README.md`, `AGENTS.md`, `pyproject.toml`, `tests/`, `start.py`, `src/bootup.py`, `src/palworld_aio/main.py`.

## Dependencies

None. This plan is a prerequisite for all others.

## Acceptance

A behavior matrix and fixture policy exist, and baseline fast tests, import checks, compilation, and available integration tests are recorded without modifying application behavior.

