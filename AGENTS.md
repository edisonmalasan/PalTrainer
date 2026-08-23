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

## Skills

Project skills are located under `.agents/skills/<name>/SKILL.md`. Private
domain skills are under `.agents/skills/private/<name>/SKILL.md`. They are
local project context and must be available to agents before implementing the
related work.

### Skill loading rules

- Read the complete `SKILL.md` before implementation, review, or planning work
  covered by that skill.
- Use `tauri-development` for any Tauri, Rust command, IPC, capability,
  filesystem, storage, plugin, configuration, packaging, or desktop lifecycle
  work.
- Use `design-taste-frontend-v1` for any frontend UI/UX work. This includes
  layout, visual hierarchy, typography, spacing, responsive behavior,
  components, interaction states, animation, accessibility, and polish.
- When a task crosses frontend and Tauri boundaries, load both skills before
  editing code.
- Load the applicable private domain skill before implementing or reviewing its
  subject area. If a task spans multiple domains, load all applicable skills.
- Project rules in this file and the authoritative `docs/PLAN.md` take
  precedence over generic recommendations in a skill.
- Do not invent a replacement rule when a private skill defines a save-format,
  data-model, formula, or roundtrip invariant. If the rule is uncertain or
  contradicted by fixtures, stop and document the uncertainty before changing
  behavior.

### Project skill registry

#### `tauri-development`

Path: `.agents/skills/tauri-development/SKILL.md`

Use for the TypeScript + React + Tauri + Rust application boundary. It covers
typed frontend-to-Rust commands and events, thin command handlers, Rust error
handling, least-privilege capabilities, filesystem validation, state
synchronization, performance, testing, and packaging. PalTrainer-specific
security and ownership rules in this file refine its generic examples.

#### `design-taste-frontend-v1`

Path: `.agents/skills/design-taste-frontend-v1/SKILL.md`

Use for all PalTrainer interface work. It defines the project's visual and
interaction baseline, including neutral palettes with one restrained accent,
dashboard-appropriate sans typography, responsive grid layouts, accessible
loading/empty/error states, restrained card use, icon requirements, and
transform/opacity-focused animation. Verify dependencies in `package.json`
before importing any UI, icon, motion, or styling library. Treat its highly
decorative examples as optional; PalTrainer remains a focused save editor and
must preserve usability, scanability, and performance.

#### `private/pal-trainer-save-pipeline`

Path: `.agents/skills/private/pal-trainer-save-pipeline/SKILL.md`

This is the core save-format contract. Use it for Rust parsing, writing,
compression, GVAS handling, property dispatch, save-version detection, and
roundtrip tests. It covers PLZ (`0x32`), PLM/Oodle (`0x31`), and CNK (`0x30`)
containers, GVAS headers, path-specific raw-data dispatch, and the sacred
roundtrip rule: unknown bytes must be retained and written back byte-for-byte.

#### `private/pal-trainer-binary-schemas`

Path: `.agents/skills/private/pal-trainer-binary-schemas/SKILL.md`

Use for Booth and Guild raw-data decoders/encoders and byte-drift debugging.
Preserve bytes before and after dynamic Guild `V1_MARKER` detection, support
Guild v1 and v2 role/permission layouts, and determine Booth lock state from
the documented lock flag rather than the private-lock player UID. Unlocking
must preserve the non-zero Booth UID and only clear the lock flag.

#### `private/pal-trainer-pal-editor`

Path: `.agents/skills/private/pal-trainer-pal-editor/SKILL.md`

Use for Pal entity projections, editor forms, Rust validation, mutation
commands, and Palbox/party placement. It defines wrapped save property types,
level/IV/soul/condenser bounds, maximum passive and equipped-skill counts,
sanitization requirements, and the Palbox model of 32 boxes with 30 slots
each. The backend remains the authority for all mutation limits.

#### `private/pal-trainer-stat-formula`

Path: `.agents/skills/private/pal-trainer-stat-formula/SKILL.md`

Use for HP, ATK, DEF, and Work Speed calculations, previews, tooltips, and
regression tests. Keep formula inputs and rounding in sync with the skill,
recalculate display values from source data, and avoid presenting derived
values as persisted save fields unless the backend confirms them.

#### `private/pal-trainer-breeding`

Path: `.agents/skills/private/pal-trainer-breeding/SKILL.md`

Use for the breeding calculator, breeding projections, game-data ingestion,
and breeding tests. It defines CombiRank averaging, rarity tiebreakers,
IgnoreCombi handling, exclusion of non-breedable entries, standard pair
permutations, and unique-combination overrides.

#### `private/pal-trainer-cli-tools`

Path: `.agents/skills/private/pal-trainer-cli-tools/SKILL.md`

Use for coordinate translation, map overlays, UUID normalization, and Xbox
GamePass import/export. It defines the pre- and post-Sakurajima transforms,
the Z-threshold map switch, normalized UUID comparison, and the XGP UWP
container/manifests/index version 14 workflow. Steam `.sav` content and XGP
wrapper data must be treated as separate layers.

### Domain-to-layer ownership

- Rust owns the save pipeline, binary schemas, Pal validation/mutation, stat
  calculations that affect saved data, backups, filesystem operations,
  coordinate conversion for imported data, XGP packing/unpacking, and all
  roundtrip guarantees.
- TypeScript may calculate presentation-only previews such as stat displays or
  breeding results, but must use shared typed inputs and matching regression
  vectors. It must not become the authority for save validity or byte layout.
- UI code consumes typed projections and user-safe errors through Tauri; it
  must not parse raw save bytes or access save paths directly.

### Skill precedence

Project-specific rules in `AGENTS.md` take precedence over generic
recommendations from skills.

Skills provide specialized implementation guidance; they do not replace
the project's architecture, security, testing, or Git rules.

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

- Do not work directly on `main` for implementation, documentation, or configuration changes unless the user explicitly asks for a direct `main` edit.
- Use a separate branch for each feature, fix, documentation change, configuration change, or repository-maintenance task.
- Branch names must follow `{type}/{short-description}` in kebab-case, using valid prefixes such as `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `ci/`, `hotfix/`, or `release/`.
- Do not use `codex/`, `phase1/`, or other non-standard branch prefixes unless the user explicitly requests one.
- Before starting each feature, inspect `git status --short --branch` and `git branch --all --verbose --no-abbrev`.
- Implement and commit one feature or process step at a time. Do not combine unrelated Phase work into one bulk commit.
- For each feature branch: create or switch to the correct branch, implement only that feature, run the relevant verification, commit only the files for that feature, then push the branch.
- Use Conventional Commit messages such as `feat(scope): add thing`, `fix(scope): correct thing`, `docs(scope): clarify thing`, or `chore(scope): update thing`.
- Inspect staged diffs before committing with `git diff --staged`.
- Do not commit ignored files unless the user explicitly asks for that ignored file to be tracked. In particular, `docs/` is ignored and should stay untracked unless the user changes that rule.
- Check `git status --short --branch` before and after edits.
- Do not revert user changes.
- Keep commits focused on one logical change.
- Do not commit generated dependency folders or build outputs.
- Push feature branches to the remote after successful verification and commit.
- Merge to `main` only after the branch satisfies the relevant plan/AGENTS requirements and verification has been run or a blocker has been clearly recorded.
- Do not rewrite history unless explicitly requested.

## Definition of Done

A change is done when:

- It follows the architecture and security rules in this file.
- Tests match the risk of the change.
- Save-modifying behavior has backup, stale-save, path-validation, preview, and regression coverage.
- Frontend lint/typecheck/tests pass when available.
- Rust format/clippy/tests pass when available.
- Missing scaffold commands are clearly called out rather than assumed.
