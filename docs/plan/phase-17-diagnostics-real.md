# Phase 17 — Diagnostics Realization

**Goal:** Scans stop being mock 6 Infos.

**Source:** `managers/func_manager.py` 56 exports, `save_diagnostic.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 17.1 | `feat/diagnostics-orphans` | Orphan `CharacterSaveParameterMap/Work/Container/Dynamic/Foliage` sweeps `_sweep_orphaned_*`, `_purge_dynamic_items` | `domain/diagnostics` cleanup tests |
| 17.2 | `feat/diagnostics-illegal` | `scan_illegal_pals_by_owner` + `check_is_illegal_pal` + `_scan_dps_for_illegals` + `invalid items/pals/passives` via `data_manager` maps | illegal pal/player tests |
| 17.3 | `feat/diagnostics-overfilled` | `detect_and_trim_overfilled_inventories (+50 buffer)` + `overfilled` preview | container capacity |
| 17.4 | `feat/diagnostics-death-bag` | `scan_and_protect_death_bags` + `is_death_bag_protected` guards all deletes, `Logs/Scan Save Logger` toggle | death-bag protected ids |

**Outcome:** Every `delete_invalid_* / delete_non_base_map_objects` queued in `files_to_delete` until commit with backup.
