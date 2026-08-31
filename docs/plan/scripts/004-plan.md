# 004-plan — Introduce explicit save sessions and lifecycle state

## Objective

Replace implicit global save state with an explicit session that owns loaded data, snapshots, dirty state, and pending changes.

## Tasks

- Replace direct lifecycle mutation in `constants.py` with a session/application-state model.
- Unify `main.py` and `SaveManager` load, reset, reload, and save flows.
- Track file snapshots, stale inputs, pending deletions, and successful-write refreshes.
- Centralize path approval, backup creation, atomic replacement, and save errors.
- Move long-running operations behind an owned worker/task boundary.

## Files and areas

`src/palworld_aio/constants.py`, `src/palworld_aio/main.py`, `src/palworld_aio/managers/save_manager.py`, `src/loading_manager.py`, backup and path helpers.

## Dependencies

`003-plan`.

## Acceptance

CLI and GUI share one lifecycle implementation, and current dirty, stale, backup, deletion, reload, and save behavior is preserved.

