# ui-dialogs Specification

## Purpose

Defines consistent dialog layout, focus, keyboard, selection, and destructive-action behavior, and when a complex workflow belongs in a drawer or dedicated workspace.

## Requirements

### Requirement: Shared dialog scaffold with isolated danger actions

The system SHALL present migrated dialogs with a header (kicker plus title plus close), a divider, a content zone, and a footer where destructive actions live isolated at footer-left and the primary confirm action lives at footer-right, with minimum (never fixed) sizing and `Esc` dismissing the dialog.

#### Scenario: Confirmation dialog layout

- **WHEN** a migrated confirmation dialog is shown
- **THEN** the user sees the title header, the message content, a Cancel control, and a confirm control styled by kind (danger vs. primary), and pressing `Esc` dismisses without confirming

### Requirement: Selection state is property-driven and themeable

The system SHALL express selection/checked states in migrated dialogs via theme-aware state (not inline color stylesheet swaps), so selected and unselected controls remain legible under the dark Deck-Ops theme.

#### Scenario: Technology selection remains legible

- **WHEN** the user selects and deselects items in a migrated picker dialog
- **THEN** selected items are visually distinct from unselected ones and both states use the token palette with no residual cyan/blue selection chrome

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
