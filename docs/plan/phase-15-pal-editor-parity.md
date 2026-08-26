# Phase 15 — Pal Editor Parity

**Goal:** Full `pal_editor` grids as in Images 8-9.

**Source:** `palworld_aio/editor/pal_editor/*` 15 files, `data.py` `breedingdata.json`, `pal_ops.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 15.1 | `feat/pal-grids` | `Party 5` `Box 32×30 paged` `DPS 6×5×30` `GPS` with `PalboxSlot/PartySlot` drag-drop `_swap_dps_slots` | grid nav + paging |
| 15.2 | `feat/pal-verbs` | `Boss/Predator/Lucky/Awake/DNA/Fav`, 13 work suits, `Learn All`, `Max Stats` `calculate_max_hp` FixedPoint64 | `pal-trainer-pal-editor` bounds |
| 15.3 | `feat/pal-bulk` | `Ctrl+Click` multi-select anchor + `Restore All / Max All / Feed Food / All Skills` | bulk bar |
| 15.4 | `feat/pal-live-formula` | `HP/ATK/DEF/WorkSpeed` `pal-trainer-stat-formula`, `toUUID`, icons `_get_cached_pixmap` | formula regression vectors |

**Outcome:** `Box 1 (218) ◀ ▶` pagination + flame/star badges + right `No Pal Data` empty parity.
