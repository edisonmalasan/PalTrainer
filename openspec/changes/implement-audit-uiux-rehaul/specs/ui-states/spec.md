## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Status strip surfaces streamed operation messages
**Reason**: The redesigned feedback model separates concise application state, transient confirmation, Activity history, and technical diagnostics instead of streaming all work through a persistent bottom strip.
**Migration**: Route human status to save state, page feedback, notifications, and Activity while preserving the detachable diagnostics console for technical logs.

### Requirement: Tools landing groups actions by purpose
**Reason**: Overview owns landing state and Tool Center owns grouped utilities.
**Migration**: Preserve all actions and prerequisite guidance across those two workspaces.
