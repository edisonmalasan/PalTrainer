# Phase 08 — Conversion, Transfer & Platform Tools

**Goal:** External workflows as guided wizards.

**Source:** `palworld_toolsets/{convert_generic,convertids,restore_map,slot_injector,character_transfer,fix_host_save,game_pass_save_fix,xgp_save_extract}.py`, `palworld_xgp_import/*`, `palworld_coord`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 08.1 | `feat/conversion-tools` | `conversion::calculate_identifier`, `convert_sav/json`, `inspect_raw_json` CityHash | conversion tool tests |
| 08.2 | `feat/restore-map-slot-injector` | `modifiers::restore_map` fog, `slot_injector` bounded `*30` pages | map/slot tests |
| 08.3 | `feat/character-transfer-host-swap` | `transfer::inspect/preview/commit` DPS handling, `host_swap` exchange semantics | transfer/host-swap tests |
| 08.4 | `feat/xgp-platform-tools` | `xgp::discover/extract/import` `containers.index` v14 UTF-16/FILETIME, Windows gate | xgp tests |
| 08.5 | `feat/tools-workbench-view` | `ToolsView` 4 tabs Converter/Modifiers/Transfer/XGP | `ToolsView` e2e |

**Skills:** `pal-trainer-cli-tools`, `pal-trainer-breeding`.

**Outcome:** `Level.sav` ↔ JSON, SteamID, map fog, palbox slots, cross-world migrate, GamePass ↔ Steam.
