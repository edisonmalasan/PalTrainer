# Resources Provenance

All game data in `resources/game_data/` is derived from `docs/PalworldSaveTools/resources/game_data/` (MIT, © PalworldSaveTools contributors) and from in-game observation.

- **Source:** `https://github.com/cheahjs/PalworldSaveTools` and `https://github.com/deafdudecomputers/PalworldSaveTools` — character, item, and skill tables.
- **License:** MIT — see `LICENSE` at project root. Copied tables retain original MIT headers where present.
- **Versioning:** `resources/game_data/VERSION` tracks the bundled data version (`v1` = initial PalTrainer catalog). Future updates should bump `VERSION` and add `resources/game_data/v2/` without breaking `v1` reads. `GameCatalog::load()` prefers `v{VERSION}/catalog.json` then falls back to `catalog.json`.
- **Update procedure:** `pnpm run update:game-data` (planned) will fetch the latest PST `game_data` JSON, run `validate_integrity`, and write to the next versioned dir. Manual edits must pass `cargo test --lib resources::loader`.

**Assets:** `resources/assets/` placeholder for map tiles and pal icons (300+ `.png`/`.webp`). Missing icons fall back to `?` via `pal_icon_path()`.

**i18n:** `resources/i18n/en.json` is the English source; other locales will be added under `resources/i18n/` per Phase 20.
