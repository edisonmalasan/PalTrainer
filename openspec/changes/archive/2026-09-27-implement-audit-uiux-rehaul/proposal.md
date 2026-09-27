## Why

PalTrainer's current interface exposes powerful save-management features through a mix of top navigation, dense tables, large tab-specific monoliths, and inconsistent editor/dialog patterns. `AUDIT.md` defines a cohesive workspace-oriented product model; implementing it now gives every existing and currently inaccessible screen one shared navigation, context, safety, and component system without changing save-file semantics.

## What Changes

- **BREAKING (UI):** Replace the stacked top navigation model with a persistent, collapsible application sidebar and a consistent workspace header/context bar; page IDs and business operations remain compatible.
- Add an Overview/no-save home, grouped Tool Center, Activity and Backups workspaces, and visible global save/context state.
- Introduce a shared design system for typography, spacing, surfaces, semantic colors, buttons, inputs, search, tabs/chips, tooltips, data tables, inspectors, drawers, dialogs, empty/loading/error states, and inventory/Pal presentation.
- Recompose World pages (Map, Players, Bases, Guilds, Exclusions) around shared entity-browser, inspector, cross-linking, search/filter, and state-preservation patterns.
- Recompose Editors (Player Inventory, Base Inventory, Pal Editor, JSON Editor) around explicit context selection, standardized grids/toolbars, previewable bulk operations, clear editable/computed fields, and consistent pending-change behavior.
- Migrate conversion, repair, transfer, injection, restore, reference, settings, about/diagnostics, and every hidden or save-gated workflow onto the same shell and component library so no legacy UI islands remain.
- Add command navigation, keyboard/focus behavior, responsive desktop layouts, persistent navigation/editor state, and accessible labels that do not rely on color or icon-only meaning.
- Add save-safety UX for backups, unsaved changes, change review, confirmations, operation progress/results, reload/drop conflicts, and actionable failures while preserving the existing parsing, serialization, and mutation logic.
- Track implementation directly in a checkpoint block inserted before `1. Purpose of This Audit`, including completed phase, verification evidence, deviations, and next work.

## Capabilities

### New Capabilities

- `ui-design-system`: Centralized visual tokens and reusable desktop UI primitives used by every page, editor, dialog, and state.
- `ui-save-safety`: Observable backup, pending-change, review, confirmation, reload/conflict, operation-result, and recovery behavior for save-changing workflows.
- `ui-accessibility`: Keyboard navigation, focus management, accessible names, contrast/state semantics, responsive behavior, and motion preferences across the application.

### Modified Capabilities

- `ui-shell`: Replace the top two-tier shell with the audit's sidebar, workspace header, context bar, inspector/drawer regions, minimum-size, and responsive workspace behavior.
- `ui-nav`: Change navigation from top zone tabs to persistent sidebar destinations, Tool Center grouping, command palette/global search, internal history, and context-preserving links.
- `ui-pages`: Add the Overview, Activity, Backups, Settings, and diagnostics surfaces and redesign every World, Editor, Tool, and Reference page described by the audit.
- `ui-states`: Standardize no-save, prerequisite, empty, no-result, loading, progress, success, warning, and error states throughout the full application.
- `ui-tables`: Expand the shared table frame into reusable entity browsers with labeled counts, filters/sorts, technical-ID disclosure, inspectors, contextual bulk actions, and preserved list state.
- `ui-dialogs`: Complete migration of all dialogs and complex modal workflows to shared dialogs, drawers, or full workspaces with consistent focus and destructive-action handling.

## Impact

- Primary UI code under `src/palworld_aio/ui/`, `src/palworld_aio/widgets/`, and `src/palworld_aio/editor/`, plus shell coordination currently concentrated in `src/palworld_aio/ui/main_window.py`.
- Localization resources, bundled SVG/image assets, user-settings persistence, and focused Qt tests under `tests/unit/palworld_aio_tests/`.
- May require presentation/application adapters around existing managers for summaries, operation metadata, change tracking, backups, and entity links; save parsing/serialization formats and Palworld data semantics remain unchanged.
- The active `uiux-audit-remediation` change overlaps some current code and specs. This new change is intentionally planned from the present branch baseline and does not depend on completing or reusing that change's unchecked tasks.
