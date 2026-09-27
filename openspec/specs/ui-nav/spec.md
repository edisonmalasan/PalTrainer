# ui-nav Specification

## Purpose

Defines how PalTrainer's grouped sidebar, route history, command palette, global search, and contextual links make every workspace and related entity reachable.

## Requirements

### Requirement: Sidebar groups destinations by user workflow
The system SHALL organize navigation into Workspace, World, Editors, Tools, Reference, and System groups. Overview SHALL be the loaded-save home; Tool Center MAY group numerous utilities, but every existing page and hidden or save-gated tool SHALL remain discoverable and reachable.

#### Scenario: User surveys navigation without a save
- **WHEN** no save is loaded
- **THEN** the user can identify the current location, open Overview or load-capable utilities, and discover every destination with save prerequisites explained rather than silently disabled

### Requirement: Navigation preserves route and view state
The system SHALL maintain back and forward history, last relevant destination, list search/filter/sort state, selected entity, and editor context when navigating through related entity and reference links. Invalid restored context SHALL fall back to a clear prerequisite state.

#### Scenario: Return from a linked guild
- **WHEN** the user opens a player's guild and then navigates back
- **THEN** the Players page restores its prior filter, scroll position where practical, and selected player

### Requirement: Command palette and global search expose actions and entities
The system SHALL provide a keyboard-invoked command palette for navigation and application commands and, when save data is loaded, search across relevant players, guilds, bases, Pals, items, and reference records. Results SHALL identify their type and preserve current unsaved-work protections.

#### Scenario: Open an editor from command navigation
- **WHEN** the user invokes the command palette and selects Player Inventory
- **THEN** the application navigates to that editor and retains or requests the required player context

### Requirement: Contextual links connect world entities and references
The system SHALL provide direct links among related players, guilds, bases, map locations, inventories, Pals, items, skills, and technologies without exposing raw identifiers as the primary navigation mechanism.

#### Scenario: Open base from map marker
- **WHEN** the user activates a base marker's Open Base action
- **THEN** the Bases workspace opens with that base selected and the prior map state remains in history
