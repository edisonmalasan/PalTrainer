## Purpose

Defines keyboard, focus, contrast, labeling, responsive, and motion behavior so PalTrainer remains understandable and operable across supported desktop layouts.

## ADDED Requirements

### Requirement: Every workflow is keyboard-operable
The system SHALL provide logical tab order, visible focus, keyboard activation, Escape dismissal for transient surfaces, focus containment in modal dialogs, and focus restoration after a dialog or drawer closes. Important operations SHALL NOT require a context menu or pointer-only gesture.

#### Scenario: Complete a dialog without a pointer
- **WHEN** a keyboard user opens and completes or cancels a dialog
- **THEN** focus stays within the dialog while open, every action is reachable and named, Escape cancels where safe, and focus returns to the invoking control

### Requirement: Meaning is not conveyed by color or icons alone
The system SHALL pair semantic color and iconography with text, shape, or state labels; icon-only controls SHALL have accessible names and tooltips; and text and focus indicators SHALL meet the application's contrast target.

#### Scenario: Destructive and selected states are perceived without color
- **WHEN** color cues are unavailable
- **THEN** destructive actions, selection, warnings, errors, and pending changes remain distinguishable through labels, icons, borders, or position

### Requirement: Workspace adapts to supported desktop sizes
The system SHALL use a 1024 by 700 logical minimum workspace, collapse the sidebar and convert fixed inspectors to drawers at narrower widths, preserve readable tables and actions, and avoid clipping or unreachable content. Resizable panel choices and collapsed navigation state SHALL persist.

#### Scenario: Window narrows below desktop layout width
- **WHEN** the workspace is resized from 1450 pixels wide toward the minimum
- **THEN** navigation and inspectors adapt without hiding save context, primary actions, or access to any destination

### Requirement: Motion respects user preference
The system SHALL keep functional feedback understandable when nonessential animations are reduced or disabled.

#### Scenario: Reduced motion is enabled
- **WHEN** the user or operating system requests reduced motion
- **THEN** navigation, dialogs, loading, selection, and progress remain clear without decorative movement

