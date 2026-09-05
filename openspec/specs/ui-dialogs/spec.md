# ui-dialogs Specification

## Purpose

Defines the consolidation of PalTrainer's many dialogs onto one dialog scaffold with consistent headers, footers, and selection presentation, migrated incrementally one dialog at a time while monolith internals stay explicitly deferred.

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

### Requirement: Incremental migration with deferred monoliths

The system SHALL allow dialogs to migrate one at a time in the order guild-assign first, then player-item, player-pal, player-technology, fix-illegal, tab-guide, and GPS editor last, and the large tab internals (player inventory ~4125 lines, base inventory ~4169 lines, map ~2639 lines, wiki ~1506 lines) SHALL remain behaviorally unchanged by this change beyond their outer page frames.

#### Scenario: Partial migration is shippable

- **WHEN** only the guild-assign dialog has migrated and all other dialogs are untouched
- **THEN** the application builds, all dialogs still open and complete their existing operations (assign, fix, pick, edit), and no unmigrated dialog regresses because the scaffold exists
