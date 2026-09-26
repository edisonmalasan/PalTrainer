## 1. Baseline, Inventory, and Checkpoint

- [x] 1.1 Insert the `Implementation Checkpoint` block before `# 1. Purpose of This Audit` with this change name, Phase 1 status, verification ledger, deviations, and next task; verify exactly one checkpoint block exists in `AUDIT.md`.
- [x] 1.2 Inventory every registered route/page, `QDialog`/frameless dialog/popup, context-menu-only workflow, inline stylesheet, and legacy shell component in a change-local migration checklist; verify the inventory is generated from current `src/palworld_aio` references and names an owner task for every entry.
- [x] 1.3 Add characterization tests for the existing page-ID activation signals, load/save entry points, entity selection propagation, and each current tool/dialog launch contract; run the focused characterization tests and record the command in the checkpoint.
- [x] 1.4 Record representative current no-save, loaded, selected-entity, editor, dialog, and 1024x700 render states with the offscreen Qt harness; verify artifacts can be generated without real save data or committed save files.

## 2. Design System Foundation

- [x] 2.1 Extend centralized tokens for the audit typography scale, 4px spacing scale, radii, layered surfaces, semantic success/warning/danger/info states, focus, density, inspector/sidebar dimensions, and reduced motion; verify token tests reject hardcoded legacy shell colors and undersized text roles.
- [x] 2.2 Consolidate bundled font and icon loading so every public component uses real bundled weights and the shared SVG pipeline; verify resource-integrity and font/icon unit tests pass with no network assets or glyph-font icons.
- [x] 2.3 Implement shared primary, secondary, tertiary, warning, destructive, icon, segmented, chip, tab, search, filter, and tooltip components with accessible state properties; verify hover/pressed/checked/focus/disabled/accessibility tests for every tier.
- [x] 2.4 Implement workspace header, save-context control, breadcrumb/context chips, pending-change affordance, notification host, and action-overflow primitives; verify default and 1024px layouts keep title, context, save state, and primary actions reachable.
- [x] 2.5 Expand shared DataTable/SearchPanel into a reusable entity-browser frame with labeled visible/total count, sort/filter hooks, contextual footer, technical-value disclosure, and inspector/drawer integration; verify filtering, copying, selection, and state-preservation tests.
- [x] 2.6 Implement standardized local skeleton, blocking progress, prerequisite, configured-empty, no-result, error/retry, operation-result, and notification components; verify each state renders distinct copy and actions without blank panels.
- [x] 2.7 Extract shared inventory-slot/grid and Pal-card presentation primitives while preserving rarity, quantity, portrait, level, gender, status, hover, selection, and keyboard behavior; verify focused rendering and interaction tests against existing fixture data.
- [x] 2.8 Complete the shared dialog/drawer scaffold with focus containment/restoration, Escape handling, minimum sizing, footer hierarchy, and risk variants; verify modal keyboard tests and destructive-action placement.
- [x] 2.9 Add localization keys and English fallbacks for all foundation components and accessible names, then run core i18n and resource-integrity tests.

## 3. Routing, Context, and Workspace Shell

- [x] 3.1 Define the metadata-driven route registry for Workspace, World, Editors, Tools, Reference, and System destinations, including stable IDs, labels/icons, shortcuts, prerequisites, accepted context, and help/risk metadata; verify every inventoried destination resolves exactly once.
- [x] 3.2 Implement `WorkspaceContext` for save identity/state, platform, player/guild/base/container selection, backup state, and pending-change summary using identifiers rather than save objects; verify transition, invalidation, and smart-default unit tests.
- [x] 3.3 Implement router navigation, back/forward history, last route per group, contextual links, and page capture/restore hooks; verify route history restores filters, selection, and context without retaining invalid entities.
- [x] 3.4 Implement the expanded/collapsed sidebar with grouped destinations, Tool Center entry, active state, tooltips, keyboard navigation, and persistent width/collapse settings; verify every route is reachable at 1024x700 and 1450x800.
- [x] 3.5 Implement the workspace shell around sidebar, drag/window-control region, header, context bar, page host, responsive inspector/drawer host, and notification host; verify window controls remain distinct and only the dedicated region drags the frameless window.
- [x] 3.6 Adapt `MainWindow` and existing page instances to the new router/shell while preserving page IDs, signals, load flows, shortcuts, and handlers; verify shell integration tests and remove `AppBar`/`NavStrip` from the live composition.
- [x] 3.7 Add the Ctrl+K/Ctrl+P command palette for routes and safe application commands with fuzzy filtering and keyboard selection; verify every route and load/save command is reachable without shortcut conflicts.
- [x] 3.8 Add entity-aware global search results for loaded players, guilds, bases, Pals, items, skills, technologies, and supported world data; verify result type labels and contextual navigation with fixture read models.
- [x] 3.9 Persist sidebar, splitter, last-route, recent-context, and per-page view state in user settings with versioned safe defaults; verify malformed/stale settings fall back without startup failure.
- [x] 3.10 Update the audit checkpoint for the completed foundation/shell phase and run focused shell, router, component, i18n, compileall, and offscreen render checks.

## 4. Overview, Tool Center, Activity, and Backups

- [x] 4.1 Implement Overview loaded-save summary with identity, platform, modification time, backup and pending-change state, entity counts, recent Activity, and direct quick actions; verify metric/action navigation and loaded fixture rendering.
- [x] 4.2 Implement Overview no-save/first-run state with open-file, open-folder, global drop, recent saves, and only genuinely load-independent utilities; verify invalid recent paths expose Locate and Remove actions.
- [x] 4.3 Define the Tool registry with category, title/description keys, prerequisites, risk, source/target requirements, launch callback, and search terms for every inventoried tool; verify registry completeness against existing launch handlers.
- [x] 4.4 Implement searchable/filterable Tool Center categories and requirement-aware cards, preserving every conversion, GamePass/Steam, Steam ID, repair, recovery, transfer, injection, restore, and other launch flow; verify unmet prerequisites explain and link to the required action.
- [x] 4.5 Implement the operation journal and Activity workspace with bounded chronological events, context, state, details, clear action, and real Undo only when supplied; verify load, backup, mutation, save, failure, and empty events.
- [x] 4.6 Implement the Backups workspace over the existing backup manager with timestamp, reason, source, size, reveal, and restore actions; verify restore confirmation creates a current-save backup and reports progress/result.
- [x] 4.7 Connect Overview, Tool Center, Activity, and Backups to localization, router context, notifications, and responsive layouts; run focused page tests and update the audit checkpoint.

## 5. World Workspaces

- [x] 5.1 Migrate Players to the shared entity browser with name-first columns, shortened copyable UID, filters/sort/count, structured inspector, direct Inventory/Pal Editor/Guild links, and contextual bulk footer; verify existing selection and bulk handlers plus history restoration.
- [x] 5.2 Migrate Bases to the shared entity browser with human-readable name, secondary IDs, guild/status metadata, structured inspector, and direct Inventory/Map/Guild links; verify existing base operations and selected-base propagation.
- [x] 5.3 Migrate Guilds to the shared entity browser with simplified list, member details in the inspector/drawer, row-level prerequisite copy, and direct Players/Bases links; verify member selection and guild mutation handlers.
- [x] 5.4 Rebuild guild assignment as a source/target/review workflow with affected counts, validation, progress, and result while preserving `move_player_to_guild`; verify cancel makes no changes and successful assignment refreshes related contexts.
- [x] 5.5 Migrate Exclusions to one segmented entity-browser pattern with per-view search/count, persistent Add Exclusion actions, loaded-empty guidance, and preserved right-click entry points; verify button and context menu create identical records.
- [x] 5.6 Recompose Map with map-first sizing, structured explorer, layer/filter controls, consolidated zoom/coordinates, responsive inspector, tooltips/accessibility, and entity links; verify toggles, +/- zoom, selection, column headers, and map state history at minimum size.
- [x] 5.7 Add consistent World no-save, no-selection, empty, no-result, loading, and error states and direct cross-links among Players, Guilds, Bases, Map, and related editors; verify context remains correct through a multi-page back/forward scenario.
- [x] 5.8 Run focused World tests, compileall, representative default/minimum render checks, and update the audit checkpoint.

## 6. Player and Base Inventory Editors

- [x] 6.1 Replace Player Inventory ribbon/dropdown context with workspace player chip/selector and distinct Inventory, Equipment, Stats, Missions, Technology, Palpedia, and supported category tabs; verify one-player smart selection and context switching.
- [x] 6.2 Migrate Player Inventory search/filter/sort, utility actions, warning-tier bulk actions, and sticky toolbar to shared components without changing handlers; verify item filtering, Modify Slots, Loadouts, Sort, and Fast Travel actions.
- [x] 6.3 Replace Player Inventory item/equipment rendering with shared grid primitives, structured equipment categories, elision/tooltips, preview/detail access, keyboard selection, and useful empty slots; verify no stretched trailing placeholder and rarity remains distinct from selection.
- [x] 6.4 Replace Base Inventory context with hierarchical guild/base chips and distinct Inventory/Base Pals view tabs, including one-guild/one-base smart defaults; verify context changes invalidate container selection safely.
- [x] 6.5 Migrate Base container navigation to grouped storage-first and muted debris sections with human names, duplicate indexes, raw-ID tooltips, search, and selection summary; verify every existing container remains selectable.
- [x] 6.6 Replace Base Inventory item rendering and toolbar with shared grid/filter/action primitives while preserving move, delete, slot modification, economy, picker, and structure-replacement handlers; verify focused operation tests.
- [x] 6.7 Migrate Base Pals, unknown structures, loading, empty container, and no-selection states to the shared state system; verify long operations keep shell/context usable and failure offers retry or recovery guidance.
- [x] 6.8 Migrate inventory-specific quantity, item picker, slot, loadout, economy, and structure dialogs to the shared scaffold with unchanged return contracts; run focused dialog and editor tests.
- [x] 6.9 Run both inventory suites, compileall, default/minimum render checks, and update the audit checkpoint.

## 7. Pal, Bulk, JSON, and Reference Workspaces

- [x] 7.1 Recompose Pal Editor into source/context, party/Palbox collection, and responsive inspector regions using the shared Pal primitives; verify selected Pal identity, party HP readability, and source switching.
- [x] 7.2 Complete Palbox paging and jump-to-box navigation for large collections with preserved box/selection state; verify first/last/invalid jumps and hundreds-of-box fixture behavior.
- [x] 7.3 Reorganize the Pal inspector into identity, editable values, computed stats, active skills, passive skills, work/technical details, and unit tooltips; verify edits use existing handlers and computed fields cannot imply editability.
- [x] 7.4 Implement contextual multi-selection and safe/bulk/destructive toolbar tiers with affected counts and single-row/overflow behavior; verify every existing toolbar handler fires and cancellation preserves selection.
- [x] 7.5 Redesign bulk item, ability, Pal mutation/deletion, skill removal, and other inventoried bulk flows with readable labels, source/target/review, preview where supported, backup/risk messaging, progress, and results; verify mutation semantics against fixtures.
- [x] 7.6 Migrate all Pal picker/create/clone/sync/food/fix-illegal and related dialogs to shared dialog/drawer/workspace patterns while preserving their contracts; verify the Pal dialog inventory has no legacy entries.
- [x] 7.7 Complete JSON Editor breadcrumb, explicit match navigation/count, readable tree, supported inline validation, and import/export/refresh hierarchy; verify path navigation and invalid edits do not apply.
- [x] 7.8 Inspect the existing JSON tooling for a safe raw-edit validation/apply boundary, implement raw mode if the boundary is reliable, otherwise record the deliberate deviation in the audit checkpoint; verify the chosen path with focused tests.
- [x] 7.9 Migrate Items, Pals, Skills, Technologies, breeding, World Data, IDs/internal data, and Docs/reference pages to shared search/browser/inspector/state patterns with cross-links from editors; verify every Reference route and breeding selection flow.
- [x] 7.10 Run Pal, bulk, JSON, reference, i18n, compileall, and representative render tests, then update the audit checkpoint.

## 8. Remaining Tools, Dialogs, and System Surfaces

- [x] 8.1 Migrate conversion workflows (save files, GamePass/Steam, Steam ID) to shared source/target/risk/progress/result presentation with existing callbacks; verify success, cancel, and failure paths.
- [x] 8.2 Migrate repair/recovery workflows (host repair, map restore, illegal data fixes, and every inventoried repair action) with prerequisites, backup state, affected summaries, progress, and recovery results; verify existing manager calls and no-change cancel paths.
- [x] 8.3 Migrate transfer/injection workflows (Character Transfer, Slot Injector, guild/base import/export/clone where exposed) to dedicated complex workspaces or drawers; verify source/target validation and result refresh behavior.
- [x] 8.4 Migrate every remaining simple dialog, picker, menu, popup, hover overlay, and confirmation from the inventory to the shared scaffold/components; verify the inventory reaches zero unowned or legacy exceptions.
- [x] 8.5 Implement Settings sections for General, Appearance, Save Safety, and Advanced preferences with validation and persistence; verify restart restores supported settings and corrupt values fall back safely.
- [x] 8.6 Implement About and Diagnostics with version, paths, environment, copy/export diagnostics, update warnings, and detachable technical console access; verify sensitive save content is not included by default.
- [x] 8.7 Verify all hidden, experimental, save-gated, and context-menu-only workflows use the new shell, state, dialog, table/button, and localization systems; update the inventory and audit checkpoint with evidence.
- [x] 8.8 Run focused tool/system/dialog tests, compileall, and representative operation render checks.

## 9. Save Safety, Accessibility, Responsiveness, and Performance

- [x] 9.1 Implement the pending-change journal and explicit Saved/Unsaved/Saving/Failed/Read Only/Backup Recommended states, wiring existing in-memory mutations and save completion without claiming unsupported rollback; verify state transitions and change-summary details.
- [x] 9.2 Add change review, supported undo/redo callbacks, save/revert/discard guards, and affected-count confirmations for risky and bulk actions; verify unsupported operations never expose false Undo.
- [x] 9.3 Protect open-file, open-folder, recent-save, global-drop, reload-from-disk, and external-change flows from replacing pending work; verify save-and-open, discard, and cancel branches with temporary fixture paths.
- [ ] 9.4 Add operation-aware automatic/offer backup policy and failure reporting that states whether the original save changed and where recovery exists; verify safe write, failed write, and restore scenarios without committing real saves.
- [ ] 9.5 Assess Palworld process detection reliability using existing platform capabilities, implement the running-game warning only if dependable, otherwise record the audit-approved deviation; verify either behavior or documented omission.
- [ ] 9.6 Complete keyboard traversal, focus visibility, accessible names, tooltips, context-menu alternatives, dialog focus trapping/restoration, and command navigation across every route; run automated accessibility contract tests and a manual keyboard smoke pass.
- [ ] 9.7 Verify semantic states remain distinguishable without color, text contrast meets the chosen target, technical text remains readable, and reduced-motion mode preserves feedback; record results in the visual QA artifacts.
- [ ] 9.8 Complete responsive behavior at 1450x800, 1200x750, and 1024x700: sidebar collapse, inspector drawers, toolbar overflow, readable headers, map bounds, and persisted splitter state; run layout-contract and offscreen render tests at all sizes.
- [ ] 9.9 Profile sidebar navigation, inspector opening, search, inventory switching, Palbox navigation, and large operations against the audit budgets; remove avoidable GUI-thread work or record measured exceptions with rationale.
- [ ] 9.10 Remove the persistent bottom status-strip presentation, route concise feedback to state/notifications/Activity and raw output to Diagnostics, and verify no raw HTTP/traceback/byte statistics appear in user-facing surfaces.
- [ ] 9.11 Run the full accessibility, state, safety, responsive, performance, i18n, resource-integrity, and visual-harness checks and update the audit checkpoint.

## 10. Audit Closure and Release Verification

- [ ] 10.1 Cross-check every Phase 1–7 migration item and all acceptance criteria in `AUDIT.md` against implemented behavior, linking each criterion to tests or visual evidence and recording deliberate deviations without silently narrowing scope.
- [ ] 10.2 Confirm the route/page/dialog/style inventory contains no live `AppBar`/`NavStrip`, legacy page ribbons, legacy table/button/dialog styling, glyph-font icons, unexplained disabled tools, or unowned screens; verify with structural searches and route traversal.
- [ ] 10.3 Run `uv run pytest -c tests/pytest.ini` and record the exact outcome in both the OpenSpec task status and audit checkpoint.
- [ ] 10.4 Run `uv run python -m compileall -q src tests` and `uv run pyright src`, resolving failures or recording genuine environment blockers without claiming success.
- [ ] 10.5 Perform manual smoke passes for no-save onboarding, save load/drop, navigation/history, every page family, entity links, representative edits, review/save/backup/restore, tool progress/failure, keyboard-only use, and minimum-size layout; record evidence and any approved deviations.
- [ ] 10.6 Render and inspect the final representative visual matrix, compare it to the audit principles rather than the legacy screenshots, and verify there are no blank, clipped, hybrid, or legacy-styled states.
- [ ] 10.7 Update the `AUDIT.md` checkpoint to Complete with final verification evidence, completed phase/task, deviations, and no remaining next task; verify all OpenSpec tasks are checked only when their full behavior is delivered.
