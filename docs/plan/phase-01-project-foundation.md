# Phase 01 — Project Foundation

**Goal:** Tauri app boots with reliable dev/test commands (no save editing yet).

**Source:** Scaffold decision in `docs/PLAN.md` § Implementation Phases / Phase 1.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 01.1 | `chore/scaffold-tauri` | Tauri v2 + Vite + TypeScript scaffold, `index.html` | `pnpm tauri dev` launches |
| 01.2 | `chore/toolchain` | `package.json` scripts, `tsconfig` strict, `eslint`, `prettier`, Rust workspace `Cargo.toml` | `pnpm lint`, `pnpm typecheck`, `cargo fmt --check` |
| 01.3 | `chore/capabilities` | `capabilities/default.json` least-privilege, `tauri.conf.json` | `cargo check` |
| 01.4 | `feat/app-shell-skeleton` | `src/app/App.tsx` routing, `src/app/routes.ts`, `ErrorBoundary`, `ViewShell` | `pnpm test` renders shell |
| 01.5 | `feat/settings-storage` | `storage/settings.rs`, `commands/settings` get/save | `cargo test` settings roundtrip |

**Outcome:** `pnpm install` → `pnpm tauri dev` shows workbench.
