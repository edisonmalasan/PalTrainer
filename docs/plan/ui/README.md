# PalTrainer Production UI Redesign Roadmap

This is a separate product-design and presentation roadmap. It must not be mixed into the scripts/core migration plans in `docs/plan/scripts/`.

## Scope

The redesign may substantially improve navigation, layout, information hierarchy, components, styling, responsiveness, accessibility, and usability. It must preserve the application’s existing feature scope and save behavior. It may be implemented only after the migration exposes stable application commands and view-state contracts.

## Non-goals

- No new save-editing capabilities.
- No change to serialization, storage, backup, stale-file, or mutation semantics.
- No requirement to preserve the current visual styling or exact widget arrangement.
- No direct coupling between visual components and raw save data.

## Design direction

Use a focused desktop workbench: clear navigation, a strong page header, compact but readable data views, contextual actions, predictable editing surfaces, and deliberate confirmation for destructive work. Retain familiar feature names and workflows while replacing the current dense, inconsistent presentation with a coherent visual language.

## Milestones

### UI-001 — Product and interaction inventory

Map every current route, action, dialog, selection model, loading state, error state, destructive action, keyboard path, and high-frequency workflow. Identify which workflows must remain one or two interactions away. Produce user-flow diagrams and a prioritized usability backlog.

### UI-002 — Information architecture and navigation

Design the primary navigation hierarchy, feature grouping, contextual subnavigation, recent-save entry points, global actions, search/command access, and responsive behavior for smaller windows. Validate that players, guilds, bases, Pals, inventory, map, diagnostics, tools, and documentation remain discoverable without adding navigation complexity.

### UI-003 — Workbench layout and responsive behavior

Define the application frame, page header, content canvas, inspector/results area, toolbars, split panes, minimum sizes, resizing rules, density modes, and empty/loading/error/dirty layouts. Establish behavior for narrow windows and high-DPI displays before styling individual screens.

### UI-004 — Component and interaction system

Create a reusable component specification for tables, cards, filters, segmented controls, form fields, entity pickers, stat blocks, tabs, command bars, banners, progress surfaces, confirmation flows, and inline validation. Specify keyboard focus, hover, pressed, disabled, loading, and error states for each component.

### UI-005 — Visual language and theming

Define typography, spacing, radii, elevation, icon sizing, semantic colors, contrast requirements, dark/light theme strategy if retained, and state colors. Replace scattered widget-local styling with one semantic token system and document component usage rules.

### UI-006 — Feature-by-feature redesign

Redesign the shell, save/session view, players, guilds, bases, Pal editor, inventory, map, breeding, diagnostics, tools, JSON view, and documentation in priority order. Keep domain commands and view-state contracts separate from visual composition. Use representative real and empty states for every screen.

### UI-007 — Accessibility, performance, and usability validation

Test keyboard-only workflows, focus order, text scaling, contrast, screen-reader labels where supported, hit targets, resize behavior, large inventories, large maps, long-running operations, and error recovery. Validate that visual polish does not introduce unnecessary animation, blocking work, or hidden state.

### UI-008 — Visual regression and release acceptance

Create stable screenshots or controlled visual checks for the shell and high-risk screens. Review all primary workflows against the interaction inventory, verify localization expansion, test frozen builds, and confirm that no UI change alters save behavior or safety confirmations.

## Dependencies

`UI-001` precedes all other UI milestones. `UI-002` and `UI-003` precede component implementation. `UI-004` and `UI-005` precede broad screen redesign. `UI-006` precedes final accessibility and regression validation. The scripts plans `004`, `005`, `006`, `010`, and `011` should be complete enough to provide stable session, command, and view-state boundaries before `UI-006` begins.

## Acceptance criteria

- Existing features and workflows remain available.
- Navigation is understandable without relying on undocumented placement.
- High-frequency screens have clear hierarchy, consistent spacing, and predictable actions.
- Destructive operations retain preview/confirmation behavior.
- Loading, empty, error, dirty, and success states are explicit and consistent.
- Keyboard navigation, focus visibility, text scaling, contrast, and localization are verified.
- Large datasets remain usable and long-running operations remain responsive.
- Visual regression checks cover the shell and representative feature screens.
- The redesign introduces no save-format, persistence, or business-rule changes.

