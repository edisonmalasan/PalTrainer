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
