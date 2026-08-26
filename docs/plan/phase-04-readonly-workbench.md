# Phase 04 — Read-Only Workbench & Resource Layer

**Goal:** Inspect full save before editing.

**Source:** `palworld_aio/ui/main_window.py` shell, `ui/tabs/*` 8 tabs, `resources/game_data` 17 JSON + map tiles.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 04.1 | `feat/resource-loader` | `resources/loader.rs` `GameCatalog`, `breeding.rs` calculator + `validate_integrity` | resource integrity tests |
| 04.2 | `feat/workbench-shell` | `app/App.tsx` `lg:grid-[240px_1fr]`, `routes.ts` 12 routes, sidebar groups | `pnpm test` ViewShell renders |
| 04.3 | `feat/shared-components` | `ViewShell`, `DataTable` sortable/search, `EmptyState`, `PreviewModal` | `shared-components.test.tsx` |
| 04.4 | `feat/read-only-views` | `features/{players,guilds,bases,pals,inventory,map,breeding,diagnostics}` read-only tables + `get_*` commands (mock → real) | `cargo test --lib` mock + `vitest` |

**Design:** `design-taste-frontend-v1` neutral + single accent, `Geist/Satoshi` + `JetBrains Mono`.

**Outcome:** Load `Level.sav` → browse every entity tab.
