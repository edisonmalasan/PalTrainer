# Phase 13 — Resource Bundling

**Goal:** No hardcoded `loader.rs` 4 pals; real `resources/game_data`.

**Source:** `resources/game_data/*.json` 17 files, `resources/assets` tiles, `resources/i18n 10 locales`, `src/data/configs/*.json` loadouts.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 13.1 | `feat/resources-bundle` | Tauri `resources` bundle include `game_data/`, `assets/`, map PNGs, `tab_guide` HTML | `tauri.conf.json` `resources` + Linux test |
| 13.2 | `feat/resources-validation` | `loader::validate_integrity` duplicate IDs, casing, `work_suitability 1-4`, `max_stack>0`, icon fallback `?` | `resource-integrity` tests expand to 300 icons |
| 13.3 | `feat/resources-updateable` | Versioned asset dir + `world.json` provenance (download from PST release, licensed) | `README` provenance note |

**Outcome:** Breeding, pals, items, skills load from JSON not Rust literals.
