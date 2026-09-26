## ADDED Requirements

### Requirement: Overview explains the loaded save and next actions
The system SHALL use Overview as the default workspace after loading a save and SHALL summarize save identity, platform, modification time, backup/safety state, unsaved state, key entity counts, recent activity, and direct quick actions. With no save, it SHALL instead present focused open/drop guidance, recent saves, and utilities that genuinely require no loaded save.

#### Scenario: Save loads successfully
- **WHEN** a save finishes loading
- **THEN** Overview answers what is loaded, whether it is safe, what it contains, whether it has pending changes, and which primary workflows can be opened next

### Requirement: Tool Center declares purpose, prerequisites, and risk
The system SHALL group all conversion, repair, recovery, transfer, injection, restore, and additional utilities by purpose. Each tool SHALL show a title, concise explanation, prerequisite state, risk level where relevant, and visible launch or prerequisite action, and SHALL report operation progress and result.

#### Scenario: Tool requires a loaded save
- **WHEN** a user views a tool whose declared requirements are not met
- **THEN** the card explains the missing requirement and offers a relevant action instead of appearing mysteriously disabled

### Requirement: World pages share entity browser and inspector behavior
Players, Bases, Guilds, and Exclusions SHALL prioritize names and meaningful metadata, use common search/filter/sort/table behavior, open structured detail inspectors, expose direct links to related entities and editors, and show bulk actions only when selection makes them applicable. Exclusions SHALL provide a persistent Add Exclusion action in addition to context-menu entry points.

#### Scenario: Player is selected
- **WHEN** the user selects a player row
- **THEN** the inspector shows structured identity, guild, activity, platform, technical details on demand, and direct Inventory, Pal Editor, and Guild actions

#### Scenario: Empty exclusions list
- **WHEN** a loaded save has no exclusions of the selected type
- **THEN** the page explains the empty state and offers Add Exclusion without requiring right-click discovery

### Requirement: Map is a first-class explorer workspace
The Map page SHALL devote the majority of the workspace to the map, provide a structured explorer and contextual inspector, offer understandable layers and filters, consolidate zoom and coordinate controls, and keep selected markers linked to their World entities. Controls SHALL be labeled or have tooltips and accessible names.

#### Scenario: User selects a map marker
- **WHEN** the user selects a player, base, or other supported marker
- **THEN** structured details and relevant entity actions appear without obscuring the primary map workspace

### Requirement: Inventory editors share context and grid primitives
Player Inventory and Base Inventory SHALL show explicit player or guild/base/container context, distinguish context selectors from inventory-category tabs, share inventory slot, quantity, rarity, selection, hover, preview, menu, search, filter, sort, and keyboard behavior, and provide meaningful empty/loading/unknown-structure states. Base containers SHALL be grouped with storage before dropped-item debris.

#### Scenario: User opens Base Inventory with one valid guild and base
- **WHEN** exactly one valid guild and base exist
- **THEN** the editor selects them automatically, exposes change-context controls, and presents available storage containers before debris containers

### Requirement: Pal Editor separates sources, collection, and details
The Pal Editor SHALL clearly separate player/source context, party and Palbox collection, and the selected-Pal inspector; support efficient box navigation at large counts; distinguish editable values from computed statistics; use consistent Pal presentation; and separate safe, bulk, and destructive actions. Bulk actions SHALL appear only with applicable selection and destructive flows SHALL provide affected counts and preview.

#### Scenario: User selects multiple Pals
- **WHEN** multi-selection becomes active
- **THEN** a contextual bulk action surface shows the selection count, applicable operations, preview where supported, and a clearly isolated destructive action

### Requirement: JSON Editor supports understandable tree and raw workflows
The JSON Editor SHALL provide a persistent clickable path breadcrumb, explicit search and match navigation, readable Key/Value/Type tree presentation, clear import/export/refresh actions, validation for edited content, and a raw JSON mode when safe editing support is available.

#### Scenario: User navigates a nested JSON value
- **WHEN** a nested row is selected
- **THEN** its full path is visible, ancestor segments are navigable, and editable content is validated before application

### Requirement: Reference and system workspaces use the same product model
Items, Pals, Skills, Technologies, breeding, world/internal data, Activity, Backups, Settings, About, and Diagnostics SHALL use the same shell, search, cards/tables, inspectors, states, and linking conventions as save-editing pages.

#### Scenario: User opens a referenced item
- **WHEN** an inventory item links to its reference record
- **THEN** the Reference workspace opens that item with related context and navigation history preserved

### Requirement: Every existing and future screen adopts the shared workspace system
No existing, hidden, experimental, save-gated, context-menu-only, or currently inaccessible screen SHALL retain legacy navigation, dialog, table, button, spacing, or state styling. New screens SHALL declare navigation placement, prerequisites, context, risk, loading, empty, error, and result behavior using the shared system.

#### Scenario: Previously inaccessible tool becomes available
- **WHEN** an underlying loading bug is resolved and the tool can open
- **THEN** it appears within the Tool Center and renders entirely with the new shell and shared components

## REMOVED Requirements

### Requirement: Tools page presents a single save-hub with one grouped tool system
**Reason**: Overview and Tool Center become separate destinations with distinct roles.
**Migration**: Move save summary and metrics to Overview and move grouped utility discovery to Tool Center without removing any tool entry point.

### Requirement: Tool rows are visible actions with icon, title, and description
**Reason**: Tool discovery changes from rows to requirement-aware Tool Center cards.
**Migration**: Preserve icon, title, description, hover, and activation behavior in the richer card presentation.

### Requirement: Tools page state-dependent save-hub content
**Reason**: No-save and loaded-save landing behavior moves to Overview.
**Migration**: Preserve load, drop, recent-save, path, and reveal capabilities in the new Overview/save-context surfaces.

## MODIFIED Requirements

### Requirement: Page content uses available width without dead regions
Modernized pages SHALL size their content regions to use the available workspace at supported window sizes without reserved dead columns. Populated content SHALL not leave a dominant empty band, while maps and data-heavy editors SHALL prioritize their primary workspace rather than dashboard-card decoration.

#### Scenario: Populated Tool Center fills the workspace
- **WHEN** the Tool Center is shown at the default desktop size
- **THEN** categorized tool cards use a responsive layout, search and filters remain visible, and no empty region dominates the populated content

#### Scenario: Populated Tools page fills the canvas
- **WHEN** the Tool Center replaces the former populated Tools page at the default desktop size
- **THEN** tool discovery uses the available workspace without a reserved dead column or an empty band taller than the categorized tool content
