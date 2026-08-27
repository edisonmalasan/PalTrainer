# Map Tile Assets

Placeholder raster tiles for the phase 16 map canvas (`docs/plan/phase-16-map-canvas.md`).

| File                  | Purpose                                                                      |
| --------------------- | ---------------------------------------------------------------------------- |
| `world-map.png`       | Base world map tile (512x512, displayed at 2048x2048 with 4x pixel scaling). |
| `treemap-overlay.png` | Transparent biome/water overlay tile, aligned to the world map grid.         |

These are **generated placeholders** (`node scripts/gen-map-placeholders.mjs`),
not authentic Palworld map art. Replace both files with real game-derived tiles
and keep the same file names — the backend serves them through the allowlisted
`get_map_asset` command keyed by logical name (`world-map`, `treemap-overlay`).

Provenance: generated locally, deterministic output (seed `20260828`); no
external artwork or game files are embedded.
