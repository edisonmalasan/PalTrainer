# AGENTS.md - PalTrainer

PalTrainer is a desktop app for modifying Palworld save files using TypeScript, Tauri, and Rust.

## Repository Structure

Current repository:

```text
PalTrainer/
  AGENTS.md
  README.md
  LICENSE
  docs/
```

Expected application structure after scaffold:

```text
PalTrainer/
  package.json
  pnpm-lock.yaml
  index.html
  vite.config.ts
  tsconfig.json
  src/
    app/
    features/
    shared/
    assets/
  src-tauri/
    Cargo.toml
    tauri.conf.json
    capabilities/
    src/
      commands/
      domain/
      pal_save/
      security/
      storage/
      tasks/
  resources/
    game_data/
    assets/
    i18n/
  tests/
    fixtures/
    e2e/
```

## Setup Commands

These commands apply after the Tauri scaffold exists:

```bash
pnpm install
```

Required tools:

- Node.js LTS.
- pnpm.
- Rust stable.
- Tauri v2 system prerequisites.

## Development Commands

```bash
pnpm tauri dev
pnpm dev
```

Use `pnpm tauri dev` for desktop behavior because filesystem permissions, dialogs, and Rust commands run through Tauri.

## Test Commands

```bash
pnpm test
cd src-tauri && cargo test
```

Slow fixture tests should be explicit and opt-in once added.

## Lint, Typecheck, and Format Commands

```bash
pnpm lint
pnpm typecheck
pnpm format
cd src-tauri && cargo fmt --check
cd src-tauri && cargo clippy --all-targets --all-features -- -D warnings
```

If one of these commands does not exist yet, add the project config before relying on it.

## Architecture Rules

- Rust owns save parsing, compression, mutation, backups, path validation, filesystem access, atomic writes, and long-running tasks.
- TypeScript owns UI, navigation, view state, filters, forms, validation messages, and rendering.
- Frontend code must call explicit Tauri commands for privileged operations.
- Keep canonical loaded-save state in a backend save session.
- Exchange typed command payloads and typed projections between frontend and backend.
- Prefer user-intent commands such as `load_save`, `get_save_summary`, `preview_delete_player`, and `commit_delete_player`.
- Destructive operations must support preview before commit.
- Long-running operations must report progress and avoid blocking the UI.

## Coding Conventions

- Use TypeScript strict mode.
- Use explicit DTO and projection types.
- Use Rust `serde` for command payloads and responses.
- Use typed Rust errors with user-safe messages.
- Normalize Palworld UIDs consistently by removing dashes and comparing lowercase.
- Keep feature UI under `src/features/<domain>/`.
- Keep shared frontend utilities under `src/shared/`.
- Keep backend domain logic under `src-tauri/src/domain/`.
- Keep backend command handlers thin; delegate logic to domain modules.
- Add comments only for non-obvious save-format, security, or data-integrity behavior.

## Files Not To Modify

Do not modify these without an explicit reason:

- Generated build outputs such as `dist/`, `target/`, and Tauri bundle artifacts.
- Dependency folders such as `node_modules/`.
- Backup folders, logs, crash dumps, temporary extraction folders, and user save directories.
- Real user save files.
- Lockfiles for package managers not used by the project.

## Security Rules

- Never let frontend code directly read, write, copy, delete, or enumerate save files.
- Use least-privilege Tauri capabilities.
- Canonicalize paths before reading or writing.
- Restrict writes to approved roots.
- Back up before save-modifying operations.
- Detect stale save files before overwrite.
- Write to temporary files and atomically replace final files.
- Queue deletions until the user confirms commit.
- Treat imported files as untrusted.
- Never commit `.sav`, `.savc`, archives, backups, logs, crash dumps, or personal game data.

## Git Rules

- Use branches prefixed with `codex/` unless the user asks for another branch name.
- Check `git status --short` before and after edits.
- Do not revert user changes.
- Keep commits focused on one logical change.
- Do not commit generated dependency folders or build outputs.
- Do not rewrite history unless explicitly requested.

## Definition of Done

A change is done when:

- It follows the architecture and security rules in this file.
- Tests match the risk of the change.
- Save-modifying behavior has backup, stale-save, path-validation, preview, and regression coverage.
- Frontend lint/typecheck/tests pass when available.
- Rust format/clippy/tests pass when available.
- Missing scaffold commands are clearly called out rather than assumed.
