# Modular-monolith migration plan

## Decision

PalTrainer will remain a single Python desktop application, but its internal
dependencies will be arranged as a modular monolith. This is a better fit than
microservices or a clean-slate package rewrite: save editing is local, stateful,
and safety-critical, while the existing PyQt6 application and serializer must
continue to work without any behavioural or file-format changes.

The migration is incremental. Canonical modules become the only destination for
new code, while small compatibility facades preserve the existing import paths
until each caller has migrated. Each move is protected by import, contract, and
save round-trip tests.

## Architectural boundaries

| Module | Owns | May depend on | Must not depend on |
| --- | --- | --- | --- |
| palsav | Compression, GVAS, binary codecs, raw-data decoding, unknown/trailing-byte preservation | Standard library | Application, UI, tools |
| save_engine | Application-facing save-document adapter and codec/storage errors | palsav, standard library | UI, managers, widgets |
| palworld_aio.application | Save-session lifecycle and application orchestration | save_engine, domain/world/inventory services, platform helpers | Qt widgets and dialogs |
| palworld_aio.world | Read projections and mutation operations over worldSaveData | palsav types, inventory domain helpers | Qt, sessions, widgets |
| palworld_aio.inventory | Item/container ownership and inventory rules | palsav types and world values | Qt dialogs and save-session lifecycle |
| palworld_toolsets and palworld_xgp_import | Transfer, conversion, map, slot, and Game Pass workflows | save_engine, application/world/inventory interfaces | Qt widgets |
| palworld_aio.ui and palworld_aio.editor | PyQt6 presentation and interaction | application commands, read models, view state | Raw serialization and direct filesystem mutation |

The existing root modules and palworld_aio.managers package are transitional
compatibility surfaces, not new feature destinations.

## Non-negotiable invariants

- palsav retains ownership of compression, GVAS parsing, property dispatch,
  unsupported properties, unknown bytes, and trailing bytes.
- All destructive writes keep the current approved-path, backup, stale-file,
  preview/confirmation, and atomic-replacement behaviour.
- PyQt6 remains in presentation code. Long-running work remains outside the UI
  thread.
- Existing public imports remain valid through explicit compatibility modules
  until all callers are deliberately migrated.
- Test imports continue to use tests/dynamic_importer.py and tests/test_registry.py.

## Evidence from the current codebase

- src/save_engine/adapter.py already provides a stable boundary over palsav.
- src/palworld_aio/managers/save_session.py owns load/save lifecycle but still
  reaches into legacy managers and shared constants.
- src/palworld_aio/read_models.py and
  src/palworld_aio/managers/operations.py are world-focused modules that do not
  require Qt widgets.
- src/palworld_aio/managers/func_manager.py and
  src/palworld_aio/managers/save_manager.py remain broad legacy aggregation
  points used by presentation code.
- tests/harness/graph_validator.py prevents circular imports and broken
  relative imports, but previously had no explicit canonical-module
  compatibility contract.

## Migration tasks

### MM-001 — Record the canonical module map and enforce migration safety

Goal: Establish the architecture decision and regression gates before moving
code.

Relevant files: this document, tests/harness/graph_validator.py,
tests/unit/palworld_aio_tests/.

Approach: Document the dependency rule above; add focused tests that verify the
canonical modules import without Qt and that transitional module names keep
exporting the same public objects.

Acceptance criteria:

- The ownership and allowed dependencies of every major module are explicit.
- Compatibility is tested, rather than assumed.
- Existing structural checks remain green.

Verify: uv run pytest -c tests/pytest.ini

### MM-002 — Create canonical application and world modules

Goal: Move the existing save-session, world-projection, and world-operation
implementations behind feature-oriented module paths without changing their
runtime interfaces.

Relevant files: src/palworld_aio/managers/save_session.py,
src/palworld_aio/read_models.py, src/palworld_aio/managers/operations.py.

Approach: Move implementation code to palworld_aio.application and
palworld_aio.world. Replace the old modules with small, documented re-exports.
No data format, method signature, or exception contract changes are allowed.

Acceptance criteria:

- Canonical and legacy imports expose object identity for the moved public API.
- The save session still performs the same approval, backup, stale-file, atomic
  write, XGP, and reset operations.
- World reads and mutations produce the same results.

Verify: save-session, read-model, operation, and compatibility tests; then the
full default test suite.

### MM-003 — Point active application code to canonical modules

Goal: Make canonical paths the codebase's forward-facing dependencies.

Relevant files: direct consumers of read_models, operations, and save_session
under src/palworld_aio/.

Approach: Update internal application and UI consumers to import from
palworld_aio.application or palworld_aio.world. Keep compatibility facades for
external callers and tests during the wider migration.

Acceptance criteria:

- New internal imports no longer select the moved legacy module paths.
- The UI keeps its existing commands, load state, errors, and confirmations.
- No new import cycle is introduced.

Verify: structural graph audit and focused UI import tests.

### MM-004 — Split remaining manager responsibilities by feature

Goal: Retire broad manager modules gradually instead of moving their contents
as one risky change.

Relevant files: src/palworld_aio/managers/func_manager.py,
src/palworld_aio/managers/save_manager.py, manager consumers, and relevant
tests.

Approach: Extract one independently characterized vertical slice at a time:
diagnostics, player/guild/base workflows, save-file helpers, then command
orchestration. Each slice becomes a pure domain service or an application
command with explicit inputs and result objects.

Acceptance criteria:

- Each extracted feature is covered by characterization tests before deletion
  from its manager.
- UI code calls commands and displays results; it does not manipulate raw save
  structures or filesystem paths.
- No pending slice changes save semantics.

Verify: its focused unit tests, full default suite, and appropriate opt-in save
round-trip coverage.

### MM-005 — Migrate tools and platform helpers at their existing boundaries

Goal: Remove remaining cross-package reach-throughs without creating a second
application framework.

Relevant files: src/palworld_toolsets/, src/palworld_xgp_import/, and root
runtime/path/resource modules.

Approach: Introduce small, typed application interfaces for approved paths,
backup/atomic writes, save documents, and progress reporting. Migrate one tool
workflow at a time; leave a narrow adapter when compatibility requires it.

Acceptance criteria:

- Tool and XGP packages use application/save-engine interfaces instead of
  widget or manager internals.
- XGP wrapper bytes and inner save payloads remain separated.
- Platform startup/resource paths remain portable for packaged builds.

Verify: conversion, XGP, path-policy, and package import tests, followed by a
frozen-build smoke check when packaging code changes.

## Execution scope for this implementation series

The completed initial series executes MM-001 through MM-003 for the
already-seamed core:
save-session lifecycle, world projections, and world operations. MM-004 and
MM-005 remain deliberately incremental because rewriting every manager/tool at
once would weaken the project's save-data guarantees and make regressions
impossible to isolate.

The active MM-004 slice routes the legacy player-info display adapter through
the canonical world projection while preserving the UI's existing formatted
result. Further MM-004 work will follow the same characterization-first
approach.
