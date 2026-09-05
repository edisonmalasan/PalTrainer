# AGENTS.md

## Project overview

PalTrainer is a Python desktop application for inspecting, repairing, converting,
and editing Palworld save files. The PyQt6 application owns presentation and
workflows, while the `palsav` workspace package owns save parsing and serialization.

## Stack

- Language(s): Python 3.11+
- Framework(s): PyQt6; setuptools/uv workspace packaging
- Database / storage: Palworld save files, JSON, archives, and Game Pass containers
- Infra / deploy: Windows launchers; Nuitka and cx_Freeze build tooling

## Setup & commands

```bash
uv sync
uv run start.py
uv run python src/palworld_aio/main.py
uv run pytest -c tests/pytest.ini
uv run pytest -c tests/pytest.ini tests/test_registry.py
uv run pyright src
```

`uv run pytest -c tests/pytest.ini -m slow` runs the slow suite. `uv run python -m
compileall -q src tests` checks Python compilation. Native build tools and platform
Qt prerequisites are required by some installed dependencies.

## Code style

- Use `pathlib.Path`, annotations on new public functions, and explicit control flow.
- Keep entry points thin; put save mutation and business logic in testable functions.
- Imports/module style: preserve the package boundaries under `src/`.
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
- Run `uv run pyright src` for type-affecting changes.
- Do not claim tests passed unless they were actually run.
- If a required check cannot be run, report why.

## Boundaries — do not touch

- Never edit generated files, build outputs, vendored code, or generated `.agents/skills/` files.
- Never commit `.env`, `.env.*`, secrets, credentials, real saves, exports, backups, logs, or crash dumps.
- Do not modify `.venv/`, `__pycache__/`, `dist/`, `*.sav`, `*.savc`, or temporary extraction folders.
- Treat `ib/` as read-only reference material unless explicitly requested.
- Do not modify lockfiles for package managers not used by this project.

## Change scope

- Make the smallest coherent change that satisfies the task.
- Do not perform unrelated refactors or modify unrelated files.
- Do not upgrade dependencies without a reason.
- Do not rename or reorganize code unless required by the task.
- Preserve existing behavior unless the task explicitly changes it.

## Git / PR conventions

- Commit style: Conventional commits such as `feat:`, `fix:`, `chore:`, `docs:`, or `test:`.
- Branch naming: `{type}/{short-description}` in kebab-case.
- Merge strategy: merge commits; do not rewrite history unless explicitly authorized.

### Git safety

- Check `git status --short --branch` before significant work.
- Inspect `git diff` before finishing and stage only the current change.
- Never discard existing user changes.
- Do not use destructive Git operations unless explicitly authorized.
- Do not rewrite history unless explicitly required.

## Source of truth

When deciding what the project should do, use this order:

1. Explicit user/task requirements
2. Approved OpenSpec specifications
3. Existing project behavior and architecture
4. Tests
5. Repository documentation
6. Agent assumptions

When sources conflict, do not silently invent a resolution.

## Existing / brownfield projects

When continuing an existing project:

- Inspect the relevant implementation before modifying it.
- Read the relevant OpenSpec specs.
- Check `openspec/changes/` for an existing active change.
- Understand current behavior before redesigning anything.
- Do not rewrite working systems merely because they are unfamiliar.
- Do not assume missing documentation means missing functionality.

## Spec-driven development (OpenSpec)

This project uses OpenSpec for specification-driven development.

### OpenSpec structure

    openspec/
    ├── config.yaml
    ├── specs/
    └── changes/

The project may contain generated OpenSpec skills under `.agents/skills/`. Their
exact set may vary by OpenSpec profile or version.

### OpenSpec rules

- Before nontrivial work, check `openspec/changes/` for an in-flight change.
- If a relevant change exists, continue it rather than creating a duplicate.
- If none exists, use the appropriate OpenSpec workflow before implementation.
- `openspec/specs/` is the source of truth for a capability's agreed behavior.
- Read the relevant spec before modifying that capability.
- Do not silently change specified behavior without updating the active change.
- Keep implementation aligned with the active change's requirements and tasks.
- Do not expand an OpenSpec change with unrelated work.

### OpenSpec workflow

Use the installed OpenSpec skills for the appropriate stage:

    Explore → Propose → Apply → Verify → Sync → Archive

Not every task requires every stage independently.

### Explore

Use `openspec-explore` when requirements, architecture, constraints, or approaches
need investigation. Exploration is for understanding and planning, not implementation.

### Propose

Use `openspec-propose` for a new nontrivial change that needs structured planning.
Capture intended behavior, requirements, design decisions, and implementation tasks.

### Apply

Use `openspec-apply-change` to implement an active change. Follow its requirements
and tasks; if the plan is incomplete, update the change rather than silently diverging.

### Update

Use `openspec-update-change` when requirements, design, tasks, or artifacts need
revision. Updating artifacts is not a substitute for implementation.

### Sync

Use `openspec-sync-specs` when approved change specs need synchronization into
`openspec/specs/`. Keep the main specs consistent with the implemented system.

### Archive

Use the OpenSpec archive workflow when a completed change is ready to close. Do not
manually improvise the archive workflow when the installed tooling provides it.

### Generated OpenSpec skills

Do not manually edit generated OpenSpec skill files under `.agents/skills/`. When
OpenSpec is upgraded or its profile changes, use `openspec update` to regenerate
the project's AI-tool instruction files. Project-specific rules belong here;
OpenSpec-specific context and artifact rules belong in `openspec/config.yaml`.

## Multi-agent development

- Determine ownership before editing files another agent may be using.
- Do not have multiple agents modify the same files unless intentionally coordinated.
- Respect dependency order between tasks.
- Do not parallelize dependent work merely for speed.
- Review another agent's result before building dependent work on top of it.
- Use OpenSpec artifacts as the shared source of truth.

For dependent work:

    A → B → C

Do not start B until A's required interface or output is stable enough to depend on.
