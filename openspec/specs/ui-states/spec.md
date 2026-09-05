# ui-states Specification

## Purpose

Defines how PalTrainer presents empty, loading, and guidance states on content pages (Pal Editor, Breeding, Map, Docs, Tools) so users always know what to do next instead of facing a blank canvas.

## Requirements

### Requirement: Empty states guide with icon, message, and action

The system SHALL render every empty content page with an icon, a headline message, a one-line hint, and where applicable a primary action button (e.g. select a player, select a pal, load a save), reusing the shared empty-state presentation.

#### Scenario: Pal Editor with no player selected

- **WHEN** the Pal Editor page is shown with no player chosen
- **THEN** the user sees an icon, a "Select a player" message, a hint explaining the next step, and a select-player action that opens the existing player picker

#### Scenario: Breeding with no pal selected

- **WHEN** the Breeding page is shown with no pal chosen
- **THEN** the user sees an icon, a "Select a pal" message, a hint about breeding combinations, and a select-pal action that opens the existing pal picker

### Requirement: Tools landing groups actions by purpose

The system SHALL group the Tools page actions into labeled sections (save loading, conversion tools, management tools, world tools) with the save-load state and field-report metrics visible above the action groups.

#### Scenario: Tools with no save loaded

- **WHEN** the Tools page is shown with no save loaded
- **THEN** the save-ledger state ("No Save Loaded" plus load guidance), Steam/GamePass load actions, field-report metrics, and grouped tool sections are all visible in reading order without overlapping

### Requirement: Map page keeps title and legend usable

The system SHALL keep the Map Viewer ribbon title visible at all times and present the map legend (search, bases/players switch, tree, info) as a docked card that scrolls internally when the window is short.

#### Scenario: Short window map legend

- **WHEN** the Map page is shown in a 750px-tall window
- **THEN** the ribbon title remains visible and the legend card remains fully reachable via internal scroll rather than clipping off-screen
