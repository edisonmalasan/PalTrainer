## Purpose

Defines the shared visual language and reusable presentation primitives that make every PalTrainer surface feel like one desktop product.

## ADDED Requirements

### Requirement: All application surfaces use one tokenized visual system
The system SHALL derive typography, spacing, radii, surfaces, borders, brand accent, semantic colors, focus treatment, and motion from centralized tokens, and SHALL apply those tokens to every page, editor, dialog, menu, tooltip, overlay, and empty/loading/error state. Brand accent SHALL indicate selection or priority and SHALL NOT substitute for success, warning, information, or destructive semantics.

#### Scenario: Theme consistency across unrelated workflows
- **WHEN** the user opens a World page, an editor, a Tool workflow, and a dialog
- **THEN** each surface uses the same typography scale, spacing rhythm, component states, semantic colors, and icon family without legacy styling islands

### Requirement: Shared components express recurring interaction patterns
The system SHALL provide consistent presentation for primary, secondary, tertiary, warning, and destructive buttons; search fields; filters; chips; tabs; tooltips; cards; data tables; inspectors; drawers; dialogs; inventory slots; Pal cards; skeletons; progress; empty states; and notifications. Destructive actions SHALL be visually distinguishable before activation.

#### Scenario: Equivalent actions look and behave alike
- **WHEN** the same interaction pattern appears on two different pages
- **THEN** it has equivalent hierarchy, spacing, hover, pressed, selected, disabled, keyboard-focus, tooltip, and accessible-name behavior

### Requirement: Technical and content values use appropriate typography and disclosure
The system SHALL prioritize human-readable names, render technical identifiers in a readable monospace style, shorten long identifiers in primary layouts, and expose full values through a shared copyable detail affordance.

#### Scenario: Long identifier is presented progressively
- **WHEN** an entity has both a display name and a long internal identifier
- **THEN** the display name is primary, the shortened identifier is secondary, and the full identifier is available without expanding a table column

