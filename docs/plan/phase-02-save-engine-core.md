# Phase 02 — Save Engine & Roundtrip Core

**Goal:** Rust loads and writes supported saves safely (pure Rust, byte-perfect).

**Source:** `src/palsav/**/*`, `src/palobject.py`, `docs/PalworldSaveTools/src/palworld_aio/utils.py` (hybrid bridge allowed temporarily).

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 02.1 | `feat/sav-container-compression` | `pal_save/archive` + `compression` PLZ/CNK (PLM typed error) | archive + compression roundtrip tests |
| 02.2 | `feat/gvas-primitives` | `gvas/model` ordered `PropertyEntry`, `uuid.rs`, `FArchive` primitives, NaN/Inf | `pal_save::gvas::reader/writer` tests |
| 02.3 | `feat/gvas-properties` | `properties/dispatch` + `skip_profiles` heavy path | property array/map/struct tests |
| 02.4 | `feat/rawdata-skeletons` | `rawdata/*` group/character/base/map/work trailing-byte stubs | byte-preservation placeholder tests |
| 02.5 | `feat/save-type-preservation` | Preserve CNK/PLZ/PLM origin through read→write | `SaveType` roundtrip + stale tests |

**Skills:** `pal-trainer-save-pipeline`, `pal-trainer-binary-schemas`.
**Outcome:** Fixture `save.sav` → `SaveSession::open` → `write` byte-exact (except PLM Oodle gap).
