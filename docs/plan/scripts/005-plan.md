# 005-plan — Separate read models from raw save traversal

## Objective

Make reads explicit, typed, and testable without exposing raw save dictionaries throughout the application.

## Tasks

- Define read projections for world metadata, players, guilds, bases, containers, inventories, and Pals.
- Move repeated raw traversal and indexing into named query functions.
- Separate cache construction from mutation and persistence.
- Make UUID normalization and display formatting explicit.
- Preserve raw values and unsupported data in the underlying document.

## Files and areas

`src/palworld_aio/managers/data_manager.py`, `player_manager.py`, `guild_manager.py`, `base_manager.py`, `src/palworld_aio/pal_ops.py`, and relevant utilities.

## Dependencies

`004-plan`.

## Acceptance

UI-facing reads are testable without importing the full main window or directly navigating raw JSON.

