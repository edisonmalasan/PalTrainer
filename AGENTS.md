# AGENTS.md

## Project overview

PalTrainer is a Python desktop application for inspecting, repairing, converting, and editing Palworld save files. The repository contains the PyQt6 desktop application and the `palsav` workspace package. Keep the application architecture modular and preserve the separation between presentation/workflows and save parsing/serialization.

--

## Stack

- Language: Python 3.11+
- Frontend/Desktop: PyQt6
- Save/Data: Palworld save files, JSON, archives, and Game Pass containers
- Packaging: setuptools, uv workspace packaging
- Testing: pytest
- Type checking: pyright
- Ops: Windows launchers, Nuitka, cx_Freeze
- Execution: Local desktop application with platform-specific Qt/runtime dependencies

--

## Setup & commands

These are the repository command contract. Keep the project configuration and package scripts aligned with them and remove/update any command that no longer works.

```bash
uv sync
uv run start.py
uv run python src/palworld_aio/main.py
uv run pytest -c tests/pytest.ini
uv run pytest -c tests/pytest.ini tests/test_registry.py
uv run pyright src
```

Additional checks:

```bash
uv run pytest -c tests/pytest.ini -m slow
uv run python -m compileall -q src tests
```

The slow suite is run with `uv run pytest -c tests/pytest.ini -m slow`. The compilation command checks Python compilation across `src/` and `tests/`. Native build tools and platform Qt prerequisites are required by some installed dependencies.

--

## Architecture boundaries

- The PyQt6 application owns UI, presentation, application workflows, and user-facing interactions.
- `palsav` owns Palworld save parsing, serialization, and save-domain behavior.
- Save mutation and business logic should remain in testable functions rather than being embedded directly in UI event handlers.
- Application entry points should remain thin and delegate behavior to the appropriate modules.
- Preserve package boundaries under `src/`.
- Save parsing and serialization code must not depend on presentation-layer widgets or UI state.
- UI code must not duplicate save parsing or serialization logic.
- Do not introduce new architectural layers unless at least one real requirement justifies them.
- Never silently corrupt, overwrite, or mutate a real save file without the existing application workflow explicitly authorizing the operation.

--

## Code style

- Python 3.11+; use `pathlib.Path`, annotations on new public functions, and explicit control flow.
- Prefer domain-oriented names and small explicit functions over generic helpers.
- Imports stay within the owning package/module; preserve the package boundaries under `src/`.
- Handle errors explicitly; never swallow failures.
- Keep entry points thin and keep save mutation/business logic in testable functions.

```python
def load_save(path: Path) -> SaveSession:
    validated = path_policy.require_file(path)
    return SaveSession.open(validated)
```

- Remove dead code, unused imports, debug logs, commented-out implementations, and temporary compatibility shims before finishing.

--

## Testing

- Bug fixes require a focused regression test when practical.
- New save parsing, serialization, mutation, conversion, or repair behavior requires focused coverage.
- Changes to save loading, writing, validation, conversion, registry behavior, or data integrity require focused tests.
- User-critical desktop workflows should have appropriate automated coverage where practical.
- Run the relevant focused tests while iterating and the full suite before finishing.
- Run `uv run pytest -c tests/pytest.ini`, `uv run pyright src`, and `uv run python -m compileall -q src tests` before finishing when applicable.
- Do not claim a check passed unless it was actually run.
- If a required check cannot run, report the exact command and reason.

--

## Boundaries — do not touch

- Never commit `.env`, `.env.*`, secrets, credentials, tokens, real save files, exports, backups, logs, or crash dumps.
- Never manually edit generated OpenSpec skills under `.agents/skills/`.
- Never modify `.venv/`, `__pycache__/`, `dist/`, `*.sav`, `*.savc`, or temporary extraction folders.
- Never edit generated files, build outputs, or vendored code unless the task explicitly requires it.
- Treat `ib/` as read-only reference material unless explicitly requested.
- Do not modify lockfiles for package managers not used by this project.
- Do not introduce unrelated build, packaging, or dependency changes unless the active requirement explicitly requires them.

--

## Change scope

- Make the smallest coherent change that satisfies the task/spec.
- Do not perform unrelated refactors or modify unrelated files.
- Do not upgrade dependencies without a task-specific reason.
- Do not rename/reorganize code unless required.
- Preserve existing behavior unless the active requirement changes it.
- Prefer adding to an existing module over inventing a new architectural layer.

--

## Git / PR workflow

`main` is the integration branch. Never perform planned work directly on `main`.

Every repository-mutating OpenSpec stage must use a remote branch and PR. Local-only working branches are not allowed.

### Branch naming

Branch names describe the technical work, not the raw OpenSpec change name.

- Proposal/docs: `docs/<technical-scope>-proposal`

- Feature: `feat/<technical-scope>`

- Fix: `fix/<technical-scope>`

- Refactor: `refactor/<technical-scope>`

- Tests/validation: `test/<technical-scope>`

- Technical spike: `spike/<technical-scope>`

- Spec sync: `docs/<technical-scope>-spec-sync`

- Archive: `chore/archive-<technical-scope>`

Examples:

- `docs/save-repair-validation-proposal`

- `spike/save-serialization-validation`

- `feat/save-editor-workflow`

- `fix/corrupt-save-detection`

- `docs/save-editor-spec-sync`

- `chore/archive-save-editor-workflow`

Do not use the OpenSpec change ID as the branch name unless it is also the clearest technical description.

### Branch lifecycle

Before starting any repository-mutating stage:

1. Check `git status`.

2. Switch to `main`.

3. Pull the latest `origin/main`.

4. Create a new branch from the updated `main`.

5. Immediately push the new branch to `origin` and set upstream tracking.

6. Only then begin modifying files.

Never leave active repository work only on a local branch.

Recommended pattern:

```bash
git switch main

git pull --ff-only origin main

git switch -c <branch-name>

git push -u origin <branch-name>
```

### OpenSpec Git lifecycle

#### Explore

`/openspec-explore` is normally read-only.

If no repository files change, no branch or PR is required.

If exploration intentionally modifies tracked documentation, treat it as a normal repository-mutating stage and use a branch + PR.

#### Propose

For `/openspec-propose`:

1. Start from updated `main`.

2. Create a technical proposal branch such as `docs/<scope>-proposal`.

3. Immediately push the branch to `origin`.

4. Create/update the OpenSpec proposal, design, specs, tasks, and roadmap status.

5. Review the diff.

6. Commit using Conventional Commits.

7. Push all proposal commits to the remote branch.

8. Open a PR into `main`.

9. After required checks, merge the PR using a **merge commit**.

10. Delete the merged local and remote branch.

11. Return to `main` and pull the merged result before starting Apply.

Proposal artifacts should be committed and pushed before merge so the exact remote PR diff can be reviewed.

Do not reuse the proposal branch for Apply.

#### Apply

For `/openspec-apply-change`:

1. Ensure the approved proposal PR has already been merged.

2. Return to `main`.

3. Pull the latest `origin/main`.

4. Create a new implementation branch from `main`.

5. Immediately push the new branch to `origin`.

6. Apply only the approved OpenSpec tasks.

7. Commit coherent implementation steps using Conventional Commits.

8. Push commits regularly to the remote branch.

9. Run all required verification.

10. Review the final diff and test results.

11. Open or update the PR into `main`.

12. Merge only after required checks pass.

13. Merge using a **merge commit**.

14. Delete the merged local and remote branch.

15. Return to updated `main`.

Do not reuse the proposal branch for Apply.

Do not begin Sync or Archive from an unmerged Apply branch.

#### Sync

If `/openspec-sync` modifies repository files:

1. Ensure the Apply PR has already been merged.

2. Return to `main` and pull latest `origin/main`.

3. Create `docs/<scope>-spec-sync`.

4. Immediately push it to `origin`.

5. Run the approved OpenSpec sync.

6. Review the diff.

7. Commit using Conventional Commits.

8. Push the commit(s).

9. Open a PR into `main`.

10. Stop for review if the sync changes meaningful specification content.

11. Merge using a **merge commit** after review/checks.

12. Delete the local and remote branch.

13. Return to updated `main`.

Skip this stage when no spec synchronization is required.

#### Archive

For `/openspec-archive`:

1. Archive only after Apply and any required Sync are merged.

2. Return to `main`.

3. Pull latest `origin/main`.

4. Create `chore/archive-<technical-scope>`.

5. Immediately push the branch to `origin`.

6. Run the OpenSpec archive workflow.

7. Update Project Status, roadmap references, and archive links where required.

8. Review the diff.

9. Commit using Conventional Commits.

10. Push the archive commit(s).

11. Open a PR into `main`.

12. Merge only after review/checks pass.

13. Merge using a **merge commit**.

14. Delete the local and remote branch.

15. Return to `main` and pull latest `origin/main` before beginning the next roadmap phase.

### Commit conventions

Use Conventional Commits:

- `feat:` new product capability

- `fix:` bug fix

- `refactor:` behavior-preserving restructuring

- `test:` tests or technical validation

- `docs:` documentation/specification

- `chore:` repository/tooling/archive maintenance

Examples:

- `docs: propose save repair validation`

- `test: add save serialization regression tests`

- `feat: add save editor workflow`

- `fix: prevent invalid save mutation`

- `docs: sync save editor requirements`

- `chore: archive save editor workflow`

Keep commits coherent and scoped.

Do not bundle unrelated changes into one commit.

### PR / merge conventions

- Every Propose, Apply, Sync, and Archive stage that changes repository files must go through a PR into `main`.

- Never silently commit completed stage work directly to `main`.

- Keep one coherent OpenSpec stage per branch.

- Open the PR from the remote branch, not from local-only work.

- Use **merge commits only** for OpenSpec and development PRs.

- Do **not** squash merge.

- Do **not** rebase merge.

- Preserve branch topology and individual branch commits in Git history.

- When using GitHub CLI, merge with:

    gh pr merge <PR_NUMBER> --merge --delete-branch

- Do not use:

    gh pr merge <PR_NUMBER> --squash

or:

```bash
gh pr merge <PR_NUMBER> --rebase
```

- Do not replace the default GitHub merge-commit title unless there is a specific reason.

- Prefer preserving the normal GitHub merge message, for example:

    Merge pull request #123 from owner/feat/save-editor-workflow

- Delete local and remote branches only after the PR has successfully merged.

- The PR and merge commit are the permanent historical record after branch deletion.

- Never begin the next OpenSpec stage from an unmerged branch.

- After every merge, switch back to `main` and update it from `origin/main` before creating the next branch.

### Expected OpenSpec branch flow

For one OpenSpec change, the normal flow is:

```text
main

  │

  ├── docs/<scope>-proposal

  │      ↓ push remote immediately

  │      ↓ /openspec-propose

  │      ↓ commit + push

  │      ↓ PR

  │      ↓ merge commit

  │

  ├── feat|spike|test/<scope>

  │      ↓ push remote immediately

  │      ↓ /openspec-apply-change

  │      ↓ implementation

  │      ↓ verification

  │      ↓ commit + push

  │      ↓ PR

  │      ↓ merge commit

  │

  ├── docs/<scope>-spec-sync

  │      ↓ only if sync is required

  │      ↓ /openspec-sync

  │      ↓ PR

  │      ↓ merge commit

  │

  └── chore/archive-<scope>

         ↓ /openspec-archive

         ↓ update roadmap/status

         ↓ PR

         ↓ merge commit

         ↓ delete branch

         ↓ return to updated main
```

### Git safety

- Check `git status` before significant work.

- Inspect `git diff` before every commit.

- Inspect the final diff before opening a PR.

- Never discard existing user changes.

- Never force-push unless explicitly authorized.

- Never use destructive Git operations unless explicitly authorized.

- Never rewrite history unless explicitly authorized.

- Never merge a PR with failing required checks unless explicitly authorized.

- Never claim a branch was pushed, a PR was opened, or a merge occurred unless it actually happened.

--

## Source of truth

When deciding behavior, use this order:

1. Explicit user/task requirements
2. Approved OpenSpec change/spec
3. Existing architecture and behavior
4. Tests
5. Repository documentation
6. Agent assumptions

When sources conflict, do not silently invent a resolution.

--

## Existing / brownfield work

- Inspect the relevant implementation before changing it.
- Read the relevant OpenSpec spec and check `openspec/changes/` for an active change.
- Continue an existing relevant change instead of creating a duplicate.
- Understand current behavior before redesigning it.
- Do not rewrite working systems merely because they are unfamiliar.

--

## Spec-driven development (OpenSpec)

This project uses OpenSpec for nontrivial changes.

openspec/
├── config.yaml
├── specs/
└── changes/

- `openspec/specs/` defines current agreed behavior; read the relevant spec before changing a capability.
- `openspec/changes/` holds in-flight changes; implementation must follow the active change.
- If no relevant change exists for nontrivial work, create one before implementation.
- Do not silently diverge from an active change; update its artifacts when requirements/design/tasks change.
- Do not expand a change with unrelated work.
- Use installed OpenSpec workflows: Explore → Propose → Apply → Verify → Sync → Archive.
- Explore is for investigation, not permission to implement.
- Use `/opsx:update` when planning artifacts need revision and `/opsx:sync` when approved specs should update the main spec set.
- Use the OpenSpec archive workflow rather than manually moving files.
- Regenerate OpenSpec AI instructions with `openspec update`; never hand-edit generated `.agents/skills/`.
- Durable project engineering rules belong here; OpenSpec capability behavior belongs in OpenSpec.

--

## Multi-agent development

- Determine file/module ownership before editing.
- Avoid multiple agents modifying the same files unless intentionally coordinated.
- Respect dependency order; do not parallelize dependent work just for speed.
- Review upstream agent output before building dependent work on top of it.
- Use OpenSpec artifacts as the shared plan and source of truth.