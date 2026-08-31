# AGENTS.md - PalTrainer

## Project identity

PalTrainer is a Python desktop application for inspecting, repairing, converting, and editing Palworld save files. The GUI uses PyQt6. The `palsav` workspace package owns save serialization and compression.

## Repository structure

```text
src/palsav/               Save serialization, property codecs, compression, and containers
src/palworld_aio/         PyQt6 application, managers, editors, tabs, dialogs, and widgets
src/palworld_toolsets/    Conversion, transfer, map restoration, and slot tools
src/palworld_xgp_import/  Xbox Game Pass discovery, extraction, and packaging
src/palworld_coord/       Coordinate conversion helpers
src/                      Launch, paths, resources, localization, and shared imports
resources/                Game data, translations, guides, maps, themes, and assets
tests/                    Structural, integration, unit, and fixture tests
build/                    Nuitka, cx_Freeze, installer, and build verification tools
scripts/                  Local maintenance and test helpers
```

## Setup and development

Required tools are Python 3.11+, `uv`, a C/C++ build toolchain for native save dependencies, and the platform Qt prerequisites.

```bash
uv sync
uv run start.py
uv run python src/palworld_aio/main.py
```

On Windows, `start.cmd` launches the application and `test.cmd` runs it with fault reporting enabled. Keep `uv.lock` under version control when it exists; launchers must not delete it.

## Test, lint, typecheck, and format

```bash
uv run pytest -c tests/pytest.ini
uv run pytest -c tests/pytest.ini -m slow
uv run python -m compileall -q src tests
uv run pyright src
```

Pyright is the configured type checker. Do not claim that Ruff, Black, or another formatter is available until its configuration and dependency are added.

## Architecture and ownership

- `palsav` owns binary parsing, property dispatch, compression, save containers, serialization, and roundtrip behavior.
- `palworld_aio` owns PyQt6 presentation, dialogs, tabs, navigation, user interaction, and workflow orchestration.
- `palworld_toolsets` owns conversion, character transfer, host repair, map restoration, and slot injection.
- `palworld_xgp_import` owns the Game Pass container layer. Keep wrapper bytes separate from inner save payloads.
- `palworld_coord` owns coordinate transforms and known map-version boundaries.
- Filesystem code owns path discovery, validation, backups, temporary workspaces, and atomic replacement. UI code must not bypass it.
- Save mutation belongs in testable save/domain functions, not in widget event handlers.
- Keep UI state separate from loaded save data and keep long-running work off the Qt GUI thread.
- Preserve the dynamic test importer; update `tests/test_registry.py` when modules move.

## Save-data invariants

- Treat all save files, imports, archives, JSON, and manifests as untrusted input.
- Preserve unsupported properties, unknown bytes, trailing bytes, and container metadata when the engine cannot interpret them.
- Never silently normalize, discard, or reorder data without a format contract and regression coverage.
- Distinguish Level saves, player saves, global storage, and Game Pass wrappers.
- Keep legacy export readers. New export formats must be versioned and validated before import.
- The raw JSON editor is read-only by default. Write access requires a backup, strict diff, schema validation, and explicit confirmation.
- Destructive actions require a preview and a separate commit step.

## PyQt6 rules

- Use PyQt6 consistently; do not reintroduce another Qt binding.
- Use `pyqtSignal`, `pyqtSlot`, and `pyqtProperty` for Qt declarations.
- Follow Qt6 enum APIs and run focused GUI/import tests after widget changes.
- Never mutate or delete widget trees from a modal dialog signal handler while `exec()` is active. Defer refreshes until the dialog returns.
- Detach widgets from layouts before scheduling deletion. Avoid monkey-patching C++ virtual methods with closures and avoid QObject signal reference cycles.
- Keep dialogs, workers, and timers owned by live Qt objects and stop them during shutdown.

## Coding conventions

- Add type annotations to new public Python functions and keep control flow explicit.
- Keep entry points thin and delegate behavior to testable functions.
- Use `pathlib.Path` for new filesystem code.
- Prefer structured parsers and serializers over string replacement for data files.
- Show user-safe errors in dialogs and retain detailed diagnostics in logs.
- Normalize UUIDs consistently where the save format requires it.
- Add comments only for non-obvious format, security, or lifecycle behavior.
- Keep changes close to their existing domain and avoid unrelated refactors.

## Skills

Read the complete applicable skill before planning, reviewing, or implementing its subject area. Project skills live under `.agents/skills/`.

- `private/codebase-analysis`: evidence-based repository inspection and architecture planning.
- `design-taste-frontend-v1`: PyQt6 UI hierarchy, accessibility, interaction states, and polish.
- `private/pal-trainer-save-pipeline`: save containers, compression, GVAS/property handling, and roundtrip preservation.
- `private/pal-trainer-binary-schemas`: Booth and Guild layouts and byte-drift debugging.
- `private/pal-trainer-pal-editor`: Pal projections, validation bounds, and Palbox/party placement.
- `private/pal-trainer-stat-formula`: stat calculations and regression vectors.
- `private/pal-trainer-breeding`: breeding formulas, exclusions, and deterministic lookups.
- `private/pal-trainer-cli-tools`: coordinate transforms, UUID handling, and Game Pass workflows.
- `clean-code`: focused refactoring without behavior changes.
- `tdd`: test-first implementation for behavior changes.
- `review`: correctness, security, regression, and test review.
- `git-branch-naming`: branch naming rules.
- `git-commit`: focused Conventional Commit workflow.

If a private skill conflicts with a fixture or established invariant, document the uncertainty before changing behavior.

## Security and storage

- Never access save files directly from widgets.
- Canonicalize paths and enforce approved roots before access.
- Back up before every mutation, detect stale inputs, and replace files atomically.
- Use temporary directories for extraction and remove them on success and failure.
- Reject archive traversal, symlink escapes, unexpected members, and oversized inputs.
- Never commit real saves, exports, backups, logs, crash dumps, credentials, or machine-specific configuration.
- Keep network and release integration opt-in and limited to documented update behavior.

## Files not to modify

Do not modify generated or user-owned material without an explicit reason:

- `.venv/`, `__pycache__/`, `dist/`, build outputs, standalone bundles, and native dependency build directories.
- `node_modules/` or old frontend artifacts if present locally; they are not part of this Python project.
- Real save directories, `*.sav`, `*.savc`, exports, backups, logs, and temporary extraction folders.
- Lockfiles for package managers not used by this project.
- Reference material under `ib/` unless explicitly requested.

## Git workflow

- Do not work directly on `main` for implementation, documentation, configuration, or maintenance changes.
- Use one branch per independently reviewable feature, fix, documentation change, configuration change, or process step.
- Branch names use `{type}/{short-description}` in kebab-case with prefixes such as `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `ci/`, `hotfix/`, or `release/`.
- Before each task, inspect `git status --short --branch` and `git branch --all --verbose --no-abbrev`.
- Treat each plan as a planning group. Break it into independently verifiable features before editing.
- Keep commits process-by-process and buildable. Do not combine unrelated work into a bulk commit.
- Stage only the current feature, inspect `git diff --staged`, and use a clear Conventional Commit message.
- Push the feature branch only after verification. Do not commit or push work merely because a task is in progress.
- Open a pull request against `main` for each completed feature branch and identify the relevant plan item and verification.
- Integrate through the pull request with a merge commit titled `Merge pull request for <branch> into main`; do not squash away feature history unless explicitly requested.
- Never rewrite history or revert user changes without explicit authorization.

## Definition of Done

A change is complete when it follows this file and the relevant plan, has focused tests at the appropriate risk level, preserves save-data and security invariants, passes available import/test/type checks, and records any blocked verification honestly.
