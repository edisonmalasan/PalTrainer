# PalTrainer

PalTrainer is a TypeScript + Tauri desktop app for inspecting and editing
Palworld save data. The Phase 1 scaffold intentionally does not parse or mutate
save files yet.

## Setup

```bash
pnpm install
```

Rust stable and the Tauri v2 system prerequisites are required for desktop
builds.

## Development

```bash
pnpm dev
pnpm tauri dev
```

Use `pnpm tauri dev` when testing desktop behavior.

## Verification

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm format
```

Rust checks are run from `src-tauri` once Rust is installed:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
```

## Release and recovery documentation

- [Supported save versions](SUPPORTED_VERSIONS.md)
- [Backup and restore](BACKUP_AND_RESTORE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Release notes template](.github/RELEASE_NOTES_TEMPLATE.md)
- [Release signing policy](.github/RELEASE_SIGNING.md)

Windows release bundles are configured for NSIS and MSI. A real installer
build also requires the Tauri Windows prerequisites, including Visual Studio
Build Tools with the MSVC and Windows SDK components.

## Game data provenance

`resources/game_data/` is versioned (`VERSION` → `v1/catalog.json`) and derived from
`docs/PalworldSaveTools/resources/game_data/` (MIT, © PalworldSaveTools). See
`resources/README.md` and `resources/game_data/README.md` for update procedure and license.
