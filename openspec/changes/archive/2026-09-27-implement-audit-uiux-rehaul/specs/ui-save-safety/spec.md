## Purpose

Defines visible, recoverable, and confidence-building behavior for loading, changing, saving, backing up, and restoring Palworld save data.

## ADDED Requirements

### Requirement: Save state and pending changes are explicit
The system SHALL show the loaded save identity, platform, save state, backup state, and pending-change count from every workspace. Save state SHALL distinguish saved, dirty, saving, failed, read-only, and backup-recommended conditions, and the user SHALL be able to open a summary of pending changes before saving.

#### Scenario: User edits save-backed data
- **WHEN** an edit creates one or more pending mutations
- **THEN** the workspace shows an explicit unsaved state and affected-change count until the changes are saved, reverted, or discarded

### Requirement: Risky operations are previewable and recoverable
The system SHALL identify an operation's risk and affected entity count before destructive or bulk mutation, require clear confirmation for irreversible actions, and report whether a failure changed the save. A current backup SHALL be created or explicitly offered before high-risk save mutation and before backup restoration.

#### Scenario: Bulk delete confirmation
- **WHEN** the user initiates deletion of multiple Pals or entities
- **THEN** the confirmation names the operation, target context, affected count, backup behavior, and destructive consequence before the confirm action is enabled

#### Scenario: Operation fails
- **WHEN** a save-changing operation fails
- **THEN** the result states whether the original save is unchanged, whether a backup exists, and what recovery or retry action is available

### Requirement: Save replacement and disk conflicts protect pending work
The system SHALL support load, global drop, recent-save selection, reload-from-disk, and detected external-change flows without silently replacing pending work. Missing recent paths SHALL offer locate and remove actions, and conflicting load/reload actions SHALL offer cancel, save-and-open/reload, or explicit discard as applicable.

#### Scenario: User drops another save while changes are pending
- **WHEN** a compatible save is dropped while the current save has unsaved changes
- **THEN** the application does not replace the current context until the user saves, explicitly discards, or cancels

### Requirement: Backups are visible and restorable
The system SHALL provide a Backups workspace listing timestamp, reason, source save, and size where available, with restore and reveal actions. Restoring a backup SHALL first preserve the current save and require confirmation.

#### Scenario: User restores a backup
- **WHEN** the user confirms a backup restoration
- **THEN** the current save is backed up first, restoration progress is visible, and completion or failure is reported with recovery details

