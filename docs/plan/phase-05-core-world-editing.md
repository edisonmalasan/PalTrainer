# Phase 05 — Core World Editing

**Goal:** Administration workflows with preview + backup.

**Source:** `palworld_aio/managers/{player,guild,base}_manager.py`, `editor/worldoption_editor.py`, `managers/data_manager.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 05.1 | `feat/player-editing` | `player::preview/commit_update_player`, level/HP, draft form, stale check | `player.rs` preview tests |
| 05.2 | `feat/player-tech-unlocks` | Bulk `max`, `unlock technologies/viewing cage/stat points` in `PlayersView` | e2e bulk |
| 05.3 | `feat/guild-editing` | `guild::rename/set level/transfer admin/delete empty` + lab research | `guild.rs` + `GuildsView` |
| 05.4 | `feat/base-editing` | `base::nudge, clone, import/export JSON, radius, repair` + `BasesView` 3 drawers | `base.rs` + `BasesView` |
| 05.5 | `feat/world-options` | `world::get/save` 18 rates + metadata `WorldOptionsView` | `world.rs` tests |
| 05.6 | `feat/exclusions` | `exclusions::ZoneExclusion` point-in-poly, `ExclusionConfig` persist | `map/MapView` tester |

**Outcome:** Edit/mutate players, guilds, bases with `preview→backup→commit` audit.
