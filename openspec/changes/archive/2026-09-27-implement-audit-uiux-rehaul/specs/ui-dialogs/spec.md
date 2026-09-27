## ADDED Requirements

### Requirement: Every dialog uses the shared scaffold and focus contract
Every dialog SHALL use a consistent header, optional explanation, content region, divider, and footer; secondary action SHALL precede the primary action, destructive confirmation SHALL be isolated and explicitly styled, Escape SHALL safely dismiss, focus SHALL be trapped while modal, and focus SHALL return to the invoking control.

#### Scenario: Legacy editor dialog is opened
- **WHEN** any existing picker, editor, repair, transfer, assignment, or confirmation dialog opens
- **THEN** it uses the shared layout, minimum rather than rigid sizing, theme tokens, accessible names, and predictable keyboard behavior

### Requirement: Complex workflows use drawers or workspaces instead of oversized modals
The system SHALL present quick contextual details in an inspector or drawer and multi-step, data-dense workflows in a dedicated workspace. A complex workflow SHALL expose source, target, review, progress, result, and recovery state without nested or screen-filling legacy dialogs.

#### Scenario: Character or guild transfer is configured
- **WHEN** a user starts a complex transfer or assignment workflow
- **THEN** the UI provides clear source and target context, review before mutation, visible progress, and a result state in a drawer or workspace appropriate to its complexity

## REMOVED Requirements

### Requirement: Incremental migration with deferred monoliths
**Reason**: The audit requires application-wide completion with zero legacy UI islands, including formerly deferred monolithic tabs and dialogs.
**Migration**: Migrate behavior in bounded phases, but do not mark the audit complete until every existing dialog and workflow uses the shared system.

