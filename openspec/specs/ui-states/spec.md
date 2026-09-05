# ui-states Specification

## Purpose

Defines how PalTrainer presents empty, loading, and guidance states on content pages (Pal Editor, Breeding, Map, Docs, Tools, table pages) and on the shell's status strip, so users always know what to do next instead of facing a blank canvas.

## Requirements

### Requirement: Status strip surfaces streamed operation messages

The system SHALL provide a visible bottom status strip that displays streamed load/save/log messages, replacing the hidden zero-height status bar, with the detachable console window behavior preserved.

#### Scenario: Save loads with visible feedback

- **WHEN** a save finishes loading
- **THEN** the status strip shows the load-result message without requiring the console to be detached

#### Scenario: Console detach still available

- **WHEN** the user toggles the console utility from the app bar
- **THEN** streamed messages route to the detached console window and the status strip remains functional afterwards

### Requirement: Empty states cover table and canvas pages

The system SHALL render the shared empty-state presentation (icon, message, hint, applicable action) on table and canvas pages when no save is loaded or no results match: Players, Guilds, Bases, Exclusions, JSON Editor, and Map (no-save condition), in addition to the existing selection-driven empty states.

#### Scenario: Players page with no save loaded

- **WHEN** the Players page is shown with no save loaded
- **THEN** the table area shows the shared empty state with a load-save hint instead of a blank table

#### Scenario: Filtered table with no matches

- **WHEN** a table search filter matches no rows
- **THEN** the table area shows an explicit no-results empty state rather than silence

### Requirement: Empty states guide with icon, message, and action

The system SHALL render every empty content page with an icon, a headline message, a one-line hint, and where applicable a primary action button (e.g. select a player, select a pal, load a save), reusing the shared empty-state presentation with no plain unstyled placeholder labels.

#### Scenario: Pal Editor with no player selected

- **WHEN** the Pal Editor page is shown with no player chosen
- **THEN** the user sees an icon, a "Select a player" message, a hint explaining the next step, and a select-player action that opens the existing player picker

#### Scenario: Breeding with no pal selected

- **WHEN** the Breeding page is shown with no pal chosen
- **THEN** the user sees an icon, a "Select a pal" message, a hint about breeding combinations, and a select-pal action that opens the existing pal picker, and the results container renders on the dark token palette

#### Scenario: Base pals placeholder uses shared presentation

- **WHEN** the Base Inventory page shows its base-pals view with no selection
- **THEN** the placeholder uses the shared empty-state presentation rather than a plain unstyled label

### Requirement: Tools landing groups actions by purpose

The system SHALL group the Tools page actions into labeled sections with translated, user-facing section titles (no untranslated key text), the save-load state visible above the action groups, and field-report metrics as the single statistics surface; redundant duplicate entry-point rows MAY be consolidated without removing any tool entry point.

#### Scenario: Tools with no save loaded

- **WHEN** the Tools page is shown with no save loaded
- **THEN** the save-ledger state ("No Save Loaded" plus load guidance), Steam/GamePass load actions, field-report metrics, and grouped tool sections are all visible in reading order without overlapping, and every visible section title is translated

### Requirement: Map page keeps title and legend usable

The system SHALL keep the Map page title visible at all times, present the map legend as a docked card that scrolls internally when the window is short, and position map overlays (toggle cluster, legend, calibration labels) so they never collide with the app bar, nav strip, or window controls at any supported window size.

#### Scenario: Short window map legend

- **WHEN** the Map page is shown in a 750px-tall window
- **THEN** the page title remains visible and the legend card remains fully reachable via internal scroll rather than clipping off-screen

#### Scenario: Overlay toggles at minimum width

- **WHEN** the Map page is shown at minimum window width
- **THEN** the map overlay toggle cluster stays inside the canvas bounds and does not underlap the app bar or window controls
