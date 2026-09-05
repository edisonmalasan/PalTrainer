# AGENTS.md - PalTrainer

## Project overview

PalTrainer is a Python 3.11+ PyQt6 desktop application for inspecting, repairing,
converting, and editing Palworld save files. `palsav` owns save serialization,
property codecs, compression, and containers; the application packages own UI and
workflow orchestration.

## Stack

- Language: Python 3.11+
- GUI: PyQt6
- Storage: Palworld save files, JSON, archives, and Game Pass containers
- Build/package: `uv`, Nuitka, cx_Freeze
- Native requirements: C/C++ build toolchain and platform Qt prerequisites

## Setup and verification commands

```text
uv sync
uv run start.py
uv run python src/palworld_aio/main.py
uv run pytest -c tests/pytest.ini
uv run pytest -c tests/pytest.ini -m slow
uv run python -m compileall -q src tests
uv run pyright src
```

Use focused pytest paths or node IDs when iterating. Do not claim a command passed
unless it was actually run. Do not claim Ruff, Black, or another formatter exists
unless its dependency and configuration are added.

## Repository ownership

- `src/palsav/`: binary parsing, property dispatch, compression, containers, and roundtrips.
- `src/palworld_aio/`: PyQt6 presentation, dialogs, tabs, navigation, and workflows.
- `src/palworld_toolsets/`: conversion, transfer, host repair, map restoration, and slot tools.
- `src/palworld_xgp_import/`: Game Pass discovery, extraction, and packaging.
- `src/palworld_coord/`: coordinate transforms and map-version boundaries.
- `resources/`: game data, translations, guides, maps, themes, and assets.
- `tests/`: structural, integration, unit, and fixture tests.

Filesystem code owns path validation, backups, temporary workspaces, and atomic
replacement. UI code must not bypass it. Save mutation belongs in testable domain
functions, not widget event handlers.

## Durable engineering rules

- Preserve unsupported properties, unknown bytes, trailing bytes, metadata, and roundtrip behavior.
- Treat saves, imports, archives, JSON, and manifests as untrusted input.
- Keep Level, player, global-storage, and Game Pass wrapper layers distinct.
- Keep legacy export readers; version and validate new export formats.
- JSON editing is read-only by default; writes require backup, strict diff, validation, and confirmation.
- Destructive actions require preview followed by a separate commit step.
- Keep long-running work off the Qt GUI thread and UI state separate from save data.
- Use `pathlib.Path` for new filesystem code and type annotations on new public functions.
- Keep entry points thin, control flow explicit, and user errors safe while logging diagnostics.

## PyQt6 rules

- Use PyQt6 consistently with `pyqtSignal`, `pyqtSlot`, and `pyqtProperty`.
- Follow Qt6 enum APIs and run focused GUI/import checks after widget changes.
- Do not mutate or delete widget trees from modal signal handlers while `exec()` is active; defer refreshes.
- Detach widgets from layouts before scheduling deletion; avoid QObject signal cycles and C++ virtual monkey-patching.
- Keep dialogs, workers, and timers owned by live Qt objects and stop them during shutdown.
- Centralize QSS/design tokens; avoid per-screen style duplication and hard-coded visual values.

## UI overhaul context

The UI overhaul is developed only on `feat/ui-overhaul`. Before UI work, read:

- `docs/plan/ui/000-index.md`
- `docs/plan/ui/000-design-context.md`
- `docs/plan/ui/PROGRESS.md`
- relevant OpenSpec artifacts and relevant files under `ib/image/`

The `ib/image/` folders are read-only functional references organized by tab.
They are not visual templates. The overhaul must create a substantially new layout,
navigation model, palette, typography, hierarchy, spacing, and component composition.
A recolor or small spacing change is not a successful overhaul. Record design and
progress decisions in the UI context and progress files.

## OpenSpec workflow

This is a brownfield OpenSpec project. OpenSpec artifacts are the source of truth
for approved capability behavior and change scope.

- Check `openspec/changes/` before nontrivial work; continue a relevant in-flight change.
- If no suitable change exists, use the installed OpenSpec propose/explore workflow before implementation.
- Read the relevant `openspec/specs/` and active change artifacts before modifying a capability.
- Use the OpenSpec apply workflow for implementation and update artifacts when reality differs from the plan.
- Sync approved changes into `openspec/specs/` and archive completed changes using the installed workflows.
- Do not manually edit generated OpenSpec skill files under `.agents/skills/`.
- Keep project-specific rules here and OpenSpec-specific configuration in `openspec/config.yaml`.
- Do not expand an active change with unrelated work.

## Testing and completion

Behavior changes need focused regression coverage. Run the relevant tests before
finishing and report failures or unavailable checks honestly. A change is complete
only when its OpenSpec tasks/specifications, tests, security/storage invariants, and
documentation are up to date.

## Boundaries

- Never commit real saves, exports, backups, logs, crash dumps, credentials, or machine configuration.
- Do not modify `.venv/`, `__pycache__/`, `dist/`, build outputs, native build directories, or `node_modules/`.
- Do not modify `*.sav`, `*.savc`, real save directories, temporary extraction folders, or lockfiles for unused package managers.
- Treat `ib/` as reference material; do not modify it unless explicitly requested.
- Do not upgrade dependencies or perform unrelated refactors without a task requirement.

## Git safety

- Work on a task branch, never directly on `main`; the current UI overhaul uses `feat/ui-overhaul` exclusively.
- Check `git status --short --branch` before significant work and inspect `git diff` before finishing.
- Never discard existing user changes or use destructive Git operations without explicit authorization.
- Do not rewrite history, commit, push, or open a pull request unless requested.
- Use focused Conventional Commits when commits are requested (`feat:`, `fix:`, `docs:`, `test:`, etc.).

## Source of truth order

1. Explicit user/task requirements
2. Approved OpenSpec change artifacts
3. Existing behavior and architecture
4. Tests
5. Repository documentation
6. Agent assumptions

When sources conflict, document the conflict and do not silently invent a resolution.

## Multi-agent work

Use OpenSpec artifacts as the shared source of truth. Determine file ownership before
editing, do not have agents modify the same files concurrently without coordination,
respect dependency order, and review prerequisite work before building on it.
