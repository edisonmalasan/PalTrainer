## Context

See `proposal.md` for motivation and the delta specs for observable behavior. The present branch already contains a tokenized dark theme, an app bar, two-tier top navigation, page ribbons, shared empty/table/dialog primitives, a shell-state model, and partial audit remediation. Coordination and many World operations remain concentrated in `ui/main_window.py`; the Player Inventory, Base Inventory, Map, Docs, and Pal Editor implementations are large stateful widgets with embedded styling and dialogs. Existing managers own save behavior and must remain authoritative.

The redesign must remain usable on Windows with PyQt6, preserve localization and all current page IDs/handlers, avoid new save-format behavior, and remain testable in the project's offscreen Qt unit suite. `AUDIT.md` is the product brief and checkpoint ledger; OpenSpec artifacts are the implementation contract.

## Goals / Non-Goals

**Goals:**

- Establish a shell and routing boundary that can host every current and future workflow without duplicating navigation or context logic.
- Move recurring presentation and state behavior into focused, testable components while preserving manager calls and mutation semantics.
- Provide a phased route from the current large widgets to the final workspace without shipping a second permanent component system.
- Make save risk, context, progress, and failure observable at the presentation layer.
- Keep progress auditable through phase checkpoints and verification evidence in `AUDIT.md`.

**Non-Goals:**

- Rewriting `palsav`, changing Palworld schemas, changing entity semantics, or inventing autosave.
- Replacing Qt, adding a web runtime, or introducing a third-party design framework.
- Optimizing save parsing or mutation algorithms except where UI responsiveness requires moving existing work off the GUI thread.
- Implementing optional audit ideas that depend on unreliable platform detection (for example game-process warnings) unless reliable support already exists; such decisions are recorded as deliberate deviations.

## Decisions

### D1. Use a workspace shell with a metadata-driven route registry

Replace `AppBar + NavStrip + page ribbon` composition with a `WorkspaceShell`: collapsible sidebar, compact drag/window-control region, workspace header, context/breadcrumb bar, page host, inspector/drawer host, and notification host. A route descriptor is the single source for page ID, group, label/icon keys, shortcut, prerequisites, accepted context, and optional risk/help metadata. Existing page IDs and activation signals are adapted at the boundary during migration.

This avoids hardcoding requirements and navigation in each tab. Re-skinning the existing top strip was rejected because it cannot satisfy the sidebar hierarchy, context persistence, Overview/System destinations, or future tool discovery requirements.

### D2. Separate navigation state from widget lifetime

A workspace router owns current route, back/forward entries, last route per group, and serializable view-state tokens. Page adapters expose capture/restore hooks for search, filter, sort, selected identifiers, scroll position where practical, and editor context. Routes carry stable IDs, not widget references or full save objects. Invalid entity context resolves to a prerequisite/empty state.

Destroying and rebuilding every page on navigation was rejected because it loses filters and selection and is expensive for the large editors. Keeping navigation state inside `MainWindow` was rejected because it would deepen the current coordinator monolith.

### D3. Make context and prerequisites typed presentation state

Extend the existing shell-state direction into a `WorkspaceContext` containing save identity/state, platform, selected player/guild/base/container, pending-change summary, backup state, and current route. Route descriptors declare `requires_save` and entity requirements. Selectors and smart defaults update this shared state; pages observe it rather than reading one-off label state from other widgets.

Context stores identifiers and display summaries only. Managers and page controllers continue resolving authoritative data, which prevents stale UI objects from becoming the save source of truth.

### D4. Build one component library and migrate call sites, not behavior

Expand the existing token, icon, `DataTable`, `BaseDialog`, `InspectorPanel`, `EmptyState`, and search work into a documented component layer. Add sidebar items/groups, workspace header/context chips, command palette, search/filter toolbar, entity browser, responsive inspector drawer, operation progress/result, notification, inventory slot/grid, Pal card, and standard picker/confirmation scaffolds. Components expose Qt properties/object names for QSS and accessibility; individual widgets do not swap inline styles.

Existing managers, signals, and handler functions stay connected through thin page adapters. A wholesale rewrite of the large tabs was rejected as too risky; modifying each monolith without shared primitives was rejected because it would recreate the inconsistency identified by the audit.

### D5. Treat Overview, Tool Center, Activity, and Backups as distinct workspaces

The current Tools masthead is split by responsibility. Overview owns loaded/no-save orientation, metrics, recent activity, and quick actions. Tool Center owns searchable categorized tool metadata and launches. Activity owns durable user-readable operation events. Backups owns discoverability and restore flows. A shared operation descriptor declares prerequisites, risk, source/target fields, and progress/result presentation.

Duplicating quick actions and tool rows across a dashboard and Tools page was rejected. Overview links to workflows but does not become a second catalog.

### D6. Add a presentation-layer change and operation journal without replacing managers

A change journal records pending UI mutations with human summary, entity context, reversibility, and optional undo callback. An operation journal records load/save/backup/tool lifecycle events and diagnostics references. Existing manager entry points remain responsible for actual reads/writes. Save commands coordinate backup policy, journal snapshot, manager call, and result; failure explicitly records whether the manager reported a write.

Where existing edits mutate in-memory data immediately, they are recorded as pending changes rather than falsely represented as deferred transactions. Full transactional rollback is not assumed. Autosave remains off unless existing behavior requires immediate persistence, in which case the UI states that explicitly.

### D7. Migrate page families in dependency order

Foundation and shell land first, followed by Overview/Tool Center, World browsers/Map, inventory editors, Pal/JSON editors and bulk flows, remaining dialogs/tools/reference/system pages, then safety/accessibility/performance polish. Shared components must be stable before dependent page conversions. Large files are split only along tested presentation/controller boundaries discovered during the relevant phase; no speculative repository-wide reorganization is required.

Temporary adapters may host an old page inside the new page host during branch development, but acceptance forbids legacy chrome, styling, dialogs, or state treatment. There is one final shell, not a user-selectable legacy/new UI mode.

### D8. Use responsive rules based on available workspace width

The default desktop target is approximately 1450 by 800 with a 232–248 pixel sidebar, 24 pixel content padding, and an inspector around 340 pixels. At narrower widths labels compact, the sidebar collapses, optional toolbar actions overflow, and inspectors become drawers. Tables choose content-first sizing and horizontal scroll only when preserving required data is preferable to hiding it. The logical minimum becomes 1024 by 700.

Qt layout behavior and persisted splitter/sidebar settings are used rather than fixed pixel positioning. Arbitrary per-page breakpoints were rejected because they produce inconsistent transitions.

### D9. Standardize feedback channels and background work

Field validation is inline; page-scoped problems use banners; concise completion uses notifications; long work uses operation progress; durable summaries go to Activity; raw tracebacks and serialization statistics remain in diagnostics. Existing `run_with_loading` operations are adapted incrementally so GUI-thread blocking work receives progress/cancel semantics only where cancellation is actually safe.

A single streamed bottom status strip is removed from primary communication because it conflates technical logs and user state. The detachable diagnostics console remains available from System/About diagnostics.

### D10. Make dialogs a bounded migration inventory

Every `QDialog`, custom frameless dialog, popup, and context-only workflow is inventoried. Simple pickers and confirmations use the shared dialog scaffold; quick details use inspectors/drawers; multi-step transfer/repair/assignment work becomes a workspace flow. Each migration preserves signal/return contracts and gains focus, Escape, sizing, state, and risk tests. Completion is based on the inventory reaching zero legacy exceptions, not on a sample of dialogs.

### D11. Track checkpoints in `AUDIT.md`

Insert one generated-looking but manually maintained `Implementation Checkpoint` block immediately before `# 1. Purpose of This Audit`. It contains change name, current phase, last completed task, verification commands with outcomes, deliberate deviations with rationale, and next task. Update it after each coherent task group and before every handoff; do not rewrite the audit body or mark acceptance checkboxes independently of verified OpenSpec tasks.

### D12. Verify behavior and appearance at multiple layers

Each phase adds focused component/page tests for signal contracts, route reachability, state transitions, keyboard/focus behavior, and manager-handler preservation. An offscreen visual harness renders representative no-save, loaded, selected, empty, loading, error, dialog, and narrow-width states to artifacts for human inspection; deterministic structural assertions protect dimensions, object roles, accessible names, and absence of legacy components. Run focused tests while iterating, full pytest, compileall, and pyright before completion.

Pixel-perfect golden screenshots were rejected as the only visual regression mechanism because platform font rendering is unstable. Rendered evidence plus stable structural assertions provides useful regression coverage without brittle false failures.

### D13. Preserve localization and asset boundaries

All user-facing copy and accessible names use localization keys with English fallback during development, then receive locale entries before a task is complete. Icons come from the bundled vector/icon pipeline; optional new imagery must be bundled and licensed. No network dependency is added for fonts, icons, or runtime UI assets.

## Risks / Trade-offs

- [Large scope can create a permanently half-migrated interface] → Gate completion by page/dialog inventory, phase acceptance checks, and the zero-legacy requirements; update the audit checkpoint at every handoff.
- [Current active remediation change overlaps files and specs] → Treat the checked-out branch as baseline, do not replay its unchecked tasks, and resolve behavioral conflicts in favor of this change's approved specs.
- [Large stateful tab modules are fragile] → Preserve handlers and manager calls, add characterization tests first, and split only at verified seams.
- [Change journal could imply rollback guarantees the backend lacks] → Label in-memory pending edits accurately, advertise Undo only when a real inverse exists, and never claim transactional safety without manager support.
- [Background conversion may change thread-affinity behavior] → Adapt one operation at a time, keep all Qt mutations on the GUI thread, and test completion/error/cancel paths.
- [1024-pixel layouts can become crowded] → Define priority/overflow rules centrally and test every workspace family at minimum and default sizes.
- [Broad dialog migration can regress specialized workflows] → Maintain a concrete dialog inventory and preserve each existing return/signal contract in focused tests.
- [Visual QA is subjective] → Tie review to audit acceptance items, shared tokens, representative rendered states, and explicit deviation records.
- [Performance may degrade when shared context triggers refreshes] → Use identifier-based change notifications, lazy page initialization, cached read models, and the audit's interaction budgets as profiling targets.

## Migration Plan

1. Baseline the current branch, inventory routes/pages/dialogs/styles, add characterization tests, and insert the first `AUDIT.md` checkpoint.
2. Complete tokens and shared components, then introduce route/context/operation models behind adapters while the current shell still runs in tests.
3. Switch the application once to the new sidebar/workspace shell and land Overview plus Tool Center so the primary navigation model is established early.
4. Migrate World, editor, bulk, tool, reference, and system families in order, removing each legacy component only after its replacement preserves existing handlers.
5. Complete save-safety, activity/backups, accessibility, responsive, persistence, and performance work; close the legacy inventory and cross-check every audit acceptance item.
6. Run full verification, capture representative visual artifacts, record deliberate deviations, update the checkpoint to complete, and only then sync/archive the change.

Rollback during development is ordinary Git reversion of the incomplete phase. There is no runtime legacy-UI fallback: if a phase cannot meet its contracts, the new default shell is not released until corrected.

## Open Questions

- A reliable Palworld-running warning remains optional and will be omitted with a recorded deviation if process detection cannot be made dependable without a new platform dependency.
- Raw JSON editing remains conditional on a safe validation/apply boundary in the existing JSON tooling; the structured editor, path navigation, validation of supported edits, and import/export behavior are mandatory.
