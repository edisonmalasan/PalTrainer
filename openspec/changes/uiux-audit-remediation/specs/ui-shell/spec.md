# ui-shell Delta

## Purpose

Defines the observable behavior of PalTrainer's top two-tier application shell: the app bar and nav strip chrome around the full-bleed page canvas, per-page headers, the status strip, and application of the dark Deck-Ops theme from one token source.

## ADDED Requirements

### Requirement: Warning affordance has none, unread, and acknowledged states

The system SHALL provide the app-bar warning button with three states: none (hidden when there is nothing to report), unread (accent-highlighted), and acknowledged (dimmed but visible while the condition remains unresolved). Activating the button SHALL reveal the triggering condition (via the console/log or an explanatory popup) and marks the warning acknowledged. The button SHALL NOT remain permanently highlighted after the user has acknowledged it.

#### Scenario: Warning lifecycle

- **WHEN** a warning condition arises, the user activates the warning button to inspect it, and later the condition clears
- **THEN** the button transitions none → unread → acknowledged → none, and no state keeps it permanently accent-highlighted without user acknowledgment

### Requirement: Save path is truncated, monospaced, and copyable

The system SHALL render the loaded save file path as a truncated, monospaced value with the full path available via tooltip and a click-to-copy affordance (with visible copied feedback); the full raw path SHALL NOT render as large primary text.

#### Scenario: Loaded save path presentation

- **WHEN** a save is loaded and the Tools save-hub shows the path
- **THEN** the path renders truncated in a monospace font, hovering shows the full path, and activating the copy affordance copies the full path with visible feedback

### Requirement: Monospace typography for technical data

The system SHALL render technical data values — save paths, player/guild/base identifiers, coordinates, hashes — in a monospace font from the bundled font set, in tables, inspectors, chips, and status surfaces, while UI prose remains in the standard proportional families.

#### Scenario: Identifier cells are monospaced

- **WHEN** a table or inspector renders a Player UID, Guild ID, Base ID, or file path value
- **THEN** the value renders in the bundled monospace font rather than the proportional UI font
