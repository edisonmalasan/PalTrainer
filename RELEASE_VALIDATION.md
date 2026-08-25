# Release Validation

## Required checks

Every pull request should run the repeatable checks that are available without
real user saves:

- `pnpm install --frozen-lockfile`
- `pnpm test`
- `pnpm typecheck`
- `pnpm test:e2e`
- `cargo fmt --check`
- `cargo test --manifest-path src-tauri/Cargo.toml --lib`

Repository-wide lint, build, and formatting gates remain required release work,
but are currently tracked separately because the existing feature views contain
baseline errors and formatting drift. They must be green before publishing an
installer.

## Playwright scope

The checked-in browser smoke suite uses a mocked Tauri IPC boundary. It verifies
that the workbench launches, route navigation works, and load/close session
feedback is rendered. It must never read or write a real `.sav` file.

Desktop smoke coverage must additionally run on a Windows runner with the Tauri
application and test fixtures. That suite should cover open, inspect, preview,
cancel, commit, restore, stale-save rejection, and reload. It is a separate
gate from browser-only tests because browser Playwright cannot prove native
filesystem or Rust command behavior.

## Windows toolchain

Installer validation requires a Windows runner with Visual Studio Build Tools,
the MSVC compiler, Windows SDK components, WebView2, Rust stable, Node.js LTS,
pnpm, and the Tauri CLI. The release must produce and checksum both NSIS and
MSI artifacts, then verify their Authenticode signatures.

## Oodle / PLM policy

The current Rust engine intentionally does not bundle Oodle/Kraken. PLM
decompression and all CNK/PLM write paths remain typed unsupported operations.
CI must not silently download, embed, or load a proprietary Oodle binary. A
future Oodle strategy requires a documented license, provenance, platform
matrix, isolated adapter, fixture coverage, and explicit security review before
the compatibility boundary changes.
