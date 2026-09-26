## ADDED Requirements

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

## REMOVED Requirements

### Requirement: App bar presents brand, save state, context, and utilities
**Reason**: The audit replaces the top app-bar navigation composition with a sidebar and workspace-header model.
**Migration**: Preserve brand, save, context, utility, and window-control functions in their new shell regions.

### Requirement: Context indicator summarizes current selection
**Reason**: A single compact app-bar indicator is insufficient for the new workspace context model.
**Migration**: Present context through the workspace header, context chips, breadcrumbs, and inspector while preserving selection propagation.

### Requirement: Nav strip groups all 12 destinations into four zones
**Reason**: The stacked top strip is replaced by persistent grouped sidebar navigation and a Tool Center.
**Migration**: Preserve page identities and shortcuts while mapping all destinations into the new hierarchy.

### Requirement: Nav strip interaction states
**Reason**: Interaction-state ownership moves to the sidebar and shared design system.
**Migration**: Retain active, hover, pressed, focus, compact, and overflow behavior in the new navigation components.

### Requirement: Keyboard shortcuts reach every destination
**Reason**: Fixed numeric shortcuts alone do not scale to the expanded workspace hierarchy.
**Migration**: Preserve nonconflicting existing shortcuts and expose all destinations through the keyboard-operable sidebar and command palette.

