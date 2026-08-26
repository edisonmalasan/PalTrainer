# Phase 16 — Map Canvas

**Goal:** Interactive world map, not table-only (Image 2).

**Source:** `palworld_coord sav_to_map/map_to_sav/treemap + MAP_Z_THRESHOLD=5000`, `palworld_aio/map/*`, `ui/tabs/map_tab.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 16.1 | `feat/map-canvas-asset` | Canvas tiles (world + treemap PNG), `Zoom fitInView`, toolbar 7 icons | map renders |
| 16.2 | `feat/map-markers` | `BaseMarker/PlayerMarker` draggable → `update_base_area_range` + `BaseRadiusRing` | marker drag test |
| 16.3 | `feat/zone-exclusions-canvas` | `rect + polygon` drawing `_zone_drawing_mode`, `zone_exclusions.json`, `is_point_in_exclusion` filtering | zone CRUD + tester |
| 16.4 | `feat/map-calibration` | `sav_to_map_by_z` pre/post-Sakurajima, `treemap_to_pixel`, `pixel_to_cursor` | `world_to_map_coordinates` pre/post |

**Outcome:** 62% canvas left + 38% `Map Browser` right split, `Bases|Players` toggle, `HoverOverlay`.
