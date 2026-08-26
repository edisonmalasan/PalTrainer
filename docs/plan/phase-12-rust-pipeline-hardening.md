# Phase 12 — Rust Pipeline Hardening

**Goal:** Pure Rust, byte-perfect for all save types.

**Source:** `src/palsav/compressor/{enums,oozlib,zlib}`, `src/palsav/palooz`, `palobject.py` heavy skip.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 12.1 | `feat/compression-oodle` | Integrate `kraken` crate for PLM `0x31`, keep `OodleUnsupported` until wired | `cargo test` PLM decompress fixture |
| 12.2 | `feat/gvas-trailing-bytes` | Guild `V1_MARKER` pre/post preservation, Booth lock flag vs `owner GUID`, connector link remap test | `pal-save` rawdata byte-exact tests |
| 12.3 | `feat/concrete-bytes` | Concrete model `_patch_raw_concrete_bytes` preserve, area range `50-1000%` | base import offset test |
| 12.4 | `feat/skip-profiles` | `SKP_PALWORLD_CUSTOM_PROPERTIES` 6-path GUI vs CLI `save_diagnostic` full decode | `json_tools` roundtrip fixture |

**Skills:** `pal-trainer-save-pipeline`, `pal-trainer-binary-schemas`.

**Outcome:** `Level.sav` PLZ + player `PLM` both parse without `palsav` Python bridge.
