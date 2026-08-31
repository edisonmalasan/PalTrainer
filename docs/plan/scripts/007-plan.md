# 007-plan — Extract feature-domain services

## Objective

Make player, guild, base, inventory, Pal, stats, and breeding behavior independent of PyQt6.

## Tasks

- Separate validation and mutation from widget construction.
- Define services for player, guild, base, inventory, and Pal operations.
- Centralize Pal level, IV, souls, condenser, passive, active-skill, and placement rules.
- Centralize stat recalculation and breeding formulas.
- Preserve Palbox dimensions, UUID behavior, formulas, exclusions, and placement semantics.

## Files and areas

`base_manager.py`, `guild_manager.py`, `player_manager.py`, `inventory/`, `editor/edit_pals.py`, `editor/pal_editor/`, and stat/breeding helpers.

## Dependencies

`005-plan`, `006-plan`.

## Acceptance

Domain services can be tested with save documents or test doubles without importing PyQt6.

