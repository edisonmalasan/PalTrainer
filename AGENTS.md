# AGENTS.md

## Project overview

PalTrainer is a Python desktop application for inspecting, repairing, converting,
and editing Palworld save files. The GUI uses PyQt6, while the `palsav` workspace
package owns save serialization, compression, property codecs, and containers.

## Stack

- Language: Python 3.11+
- Framework: PyQt6
- Storage: Palworld saves, JSON, archives, and Game Pass containers
- Build/deploy: `uv`, Nuitka, cx_Freeze, Windows launchers

## Setup & commands

```text
uv sync
uv run start.py
uv run python src/palworld_aio/main.py
uv run pytest -c tests/pytest.ini
uv run pytest -c tests/pytest.ini -m slow
uv run pytest -c tests/pytest.ini tests/test_registry.py
uv run python -m compileall -q src tests
uv run pyright src
```

On Windows, `start.cmd` launches the application and `test.cmd` runs it with fault
reporting enabled. Keep `uv.lock` under version control. Launchers must not delete it.

## Code style

- Use `pathlib.Path` for new filesystem code and type annotations on new public functions.
- Keep entry points thin and delegate behavior to testable functions.
- Prefer structured parsers and serializers over string replacement.
- Use explicit control flow and do not leave dead code or silently swallowed errors.
- Imports/module style: follow the existing package boundaries under `src/`.
- Error handling: show safe user-facing errors and retain detailed diagnostics in logs.

```python
def load_save(path: Path) -> SaveSession:
    validated = path_policy.require_file(path)
    return SaveSession.open(validated)
```

## Testing

- Add focused regression coverage for new behavior and bug fixes.
- Run the relevant focused test while iterating and the full suite before finishing.
- Run `uv run python -m compileall -q src tests` after Python changes.
- Run `uv run pyright src` when type-affecting code changes.
- Do not claim tests passed unless they were actually run.
- If a required check cannot be run, report why.

## Boundaries — do not touch

- Never commit real saves, exports, backups, logs, crash dumps, credentials, or machine configuration.
- Never edit `.venv/`, `__pycache__/`, `dist/`, build outputs, native dependency build directories, or `node_modules/`.
- Never modify real save directories, `*.sav`, `*.savc`, temporary extraction folders, or unused package-manager lockfiles.
- Treat `ib/` as read-only reference material unless explicitly requested.
- Do not manually edit generated OpenSpec skills under `.agents/skills/`.

## Change scope

- Make the smallest coherent change that satisfies the task.
- Do not perform unrelated refactors or modify unrelated files.
- Do not upgrade dependencies without a documented reason.
- Preserve behavior unless the task explicitly changes it.
- Filesystem code owns validation, backups, temporary workspaces, and atomic replacement; UI code must not bypass it.
- Save mutation belongs in testable domain functions, not widget event handlers.

## Git / PR conventions

- Commit style: Conventional Commits such as `feat:`, `fix:`, `docs:`, `test:`, or `chore:`.
- Branch naming: `{type}/{short-description}` in kebab-case.
- Merge strategy: merge commits; do not squash feature history unless explicitly requested.
- The UI overhaul is developed on `feat/ui-overhaul`; ordinary work must use its own task branch.

### Git safety

- Check `git status --short --branch` before significant work.
- Inspect `git diff` before finishing and stage only the current change.
- Never discard existing user changes.
- Do not use destructive Git operations or rewrite history without explicit authorization.
- Do not push or open a pull request unless requested.

## Source of truth

When deciding what the project should do, use this order:

1. Explicit user/task requirements
2. Approved OpenSpec specifications and active change artifacts
3. Existing project behavior and architecture
4. Tests
5. Repository documentation
6. Agent assumptions

When sources conflict, do not silently invent a resolution.

## Existing / brownfield projects

- Inspect relevant implementation before modifying it.
- Check `openspec/changes/` for an active relevant change.
- Read relevant OpenSpec specs before modifying that capability.
- Read `docs/plan/ui/000-index.md`, `000-design-context.md`, and `PROGRESS.md` before UI work.
- For UI work, treat folders under `ib/image/` as read-only functional references, not visual templates.
- Do not rewrite working systems merely because they are unfamiliar.

## Spec-driven development (OpenSpec)

This project uses OpenSpec for specification-driven development. Its structure is:

```text
openspec/
├── config.yaml
├── specs/
└── changes/
```

- Before nontrivial work, use the installed OpenSpec explore/propose workflow when requirements or design need investigation.
- If a suitable active change exists, continue it rather than creating a duplicate.
- Use `openspec-apply-change` to implement an approved active change.
- If implementation reveals an incomplete or incorrect plan, update the change artifacts before diverging.
- Use sync and archive workflows when their stage is reached; do not improvise their file operations.
- Keep project-specific context in this file and OpenSpec configuration/artifact rules in `openspec/config.yaml`.

## Skills

Read the complete applicable skill before planning, reviewing, or implementing its subject area. Project skills live under `.agents/skills/`.

- `.agents\skills\design-taste-frontend-v1`
- `.agents\skills\openspec-apply-change`
- `.agents\skills\openspec-archive-change`
- `.agents\skills\openspec-explore`
- `.agents\skills\openspec-propose`
- `.agents\skills\openspec-sync-specs`
- `.agents\skills\openspec-update-change`
- `.agents\skills\pyqt6-ui-designer`

Do not include or load project-private skills unless the task explicitly authorizes them.

## Multi-agent development

- Determine ownership before editing files another agent may be using.
- Do not have multiple agents modify the same files without intentional coordination.
- Respect dependency order and review prerequisite work before building on it.
- Use OpenSpec artifacts as the shared source of truth.

## Definition of done

A change is complete when its approved OpenSpec requirements and tasks are satisfied,
focused tests pass, save-data and security invariants are preserved, and any blocked
verification is reported honestly.
