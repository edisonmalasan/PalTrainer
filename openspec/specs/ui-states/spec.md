# ui-states Specification

## Purpose

Defines how PalTrainer presents prerequisite, empty, loading, error, success, and operation feedback states across workspaces so users know what is happening and what to do next.

## Requirements

### Requirement: Empty states cover table and canvas pages

The system SHALL render the shared empty-state presentation (icon, message, hint, applicable action) on table and canvas pages when no save is loaded or no results match: Players, Guilds, Bases, Exclusions, JSON Editor, and Map (no-save condition), in addition to the existing selection-driven empty states.

#### Scenario: Players page with no save loaded

- **WHEN** the Players page is shown with no save loaded
- **THEN** the table area shows the shared empty state with a load-save hint instead of a blank table

#### Scenario: Filtered table with no matches

- **WHEN** a table search filter matches no rows
- **THEN** the table area shows an explicit no-results empty state rather than silence

### Requirement: Empty states guide with icon, message, and action
The system SHALL render empty and prerequisite states with a consistent icon, headline, one-line explanation, and applicable primary action. Copy SHALL distinguish no save, no selection, configured-empty, no results, unknown data, and unavailable capability conditions rather than reusing generic load guidance.

#### Scenario: Pal Editor with no player selected
- **WHEN** the Pal Editor page is shown with no player chosen
- **THEN** the user sees the required player context, a concise explanation, and a Choose Player action that opens the shared context selector

#### Scenario: Breeding with no pal selected
- **WHEN** the Breeding page is shown with no pal chosen
- **THEN** the user sees a shared empty state with one Select a Pal action and a concise explanation of the resulting workflow

#### Scenario: Base pals placeholder uses shared presentation
- **WHEN** Base Inventory shows Base Pals without the required context or with no matching Pals
- **THEN** the page uses the shared prerequisite or empty presentation with accurate copy and an applicable action

#### Scenario: Search has no matches
- **WHEN** a populated list is filtered to zero matching records
- **THEN** the state identifies the active search or filters and offers clear/reset actions without implying that the underlying collection is empty

### Requirement: Map page keeps title and legend usable

The system SHALL keep the Map page title visible at all times, present the map legend as a docked card that scrolls internally when the window is short, and position map overlays (toggle cluster, legend, calibration labels) so they never collide with the workspace header or window controls at any supported window size.

#### Scenario: Short window map legend

- **WHEN** the Map page is shown in a 750px-tall window
- **THEN** the page title remains visible and the legend card remains fully reachable via internal scroll rather than clipping off-screen

#### Scenario: Overlay toggles at minimum width

- **WHEN** the Map page is shown at minimum window width
- **THEN** the map overlay toggle cluster stays inside the canvas bounds and does not underlap the workspace header or window controls

### Requirement: Every asynchronous surface defines a complete state model
Every asynchronous page, editor, table, inspector, and tool SHALL distinguish initial, prerequisite, loading, populated, zero-result, failure, retry, and completed-operation states. Loading SHALL use local skeletons or progress for the affected region and SHALL NOT present a blank panel.

#### Scenario: Base containers are loading
- **WHEN** a base has been chosen and its containers are still resolving
- **THEN** the affected content region shows meaningful loading progress while navigation and unrelated context remain usable

### Requirement: Activity records meaningful operations
The system SHALL provide a live Activity workspace showing timestamp, operation, entity or save context, status, and undo or detail actions when supported. Empty Activity SHALL explain what will appear, and the visible list SHALL remain bounded and manageable.

#### Scenario: Backup and save operations complete
- **WHEN** a backup is created and pending changes are saved
- **THEN** Activity records both operations with their context and success state in chronological order

### Requirement: Feedback uses the appropriate channel
The system SHALL use inline validation for field errors, local banners for page-scoped issues, progress surfaces for long work, transient notifications for concise confirmations, and Activity/details for durable diagnostics. Raw exceptions and byte/stat payloads SHALL remain in diagnostics rather than user-facing status text.

#### Scenario: Save completes successfully
- **WHEN** a save operation completes
- **THEN** save state becomes Saved, a concise confirmation is shown, Activity records the operation, and raw implementation output is available only in diagnostics
