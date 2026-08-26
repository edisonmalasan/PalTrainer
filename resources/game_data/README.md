# Game Data — Versioned Catalog

- **Current version:** `v1` — see `VERSION` file.
- **File:** `catalog.json` (also `v1/catalog.json` for versioned reads). Contains `pals`, `items`, `passives`, `activeSkills` as defined in `src-tauri/src/resources/loader.rs:GameCatalog`.
- **Provenance:** Derived from PalworldSaveTools `resources/game_data/` (MIT). See `../README.md`.
- **Validation:** `cargo test --lib resources::loader` runs `validate_integrity` (duplicate/casing, work 1-4, max_stack>0, tier/power checks) and `pal_icon_path` fallback.
- **Update:** To add a new version, copy current `catalog.json` to `v2/catalog.json`, bump `VERSION` to `v2`, edit, and ensure `GameCatalog::load()` prefers the versioned path.
