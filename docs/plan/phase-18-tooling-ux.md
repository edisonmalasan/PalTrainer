# Phase 18 — Tooling UX

**Goal:** Files picked via dialog with progress, not text inputs (Image 1 bottom 2×4 cards).

**Source:** `palworld_toolsets/*` 9 tools, `tools_tab.py` `CONVERTING/MANAGEMENT` cards.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 18.1 | `feat/tools-pickers` | `Converter: SAV↔JSON / SteamID`, `RestoreMap`, `SlotInjector` all path `open({filters: sav/json})` + `DropOverlay` + `ConversionOptionsDialog 380px` | `ConverterPanel` file pickers |
| 18.2 | `feat/tools-progress` | Long `run_with_loading` → `TaskTracker` `emit("progress")` + UI bar + `CancellationToken` | progress e2e |
| 18.3 | `feat/tools-xgp-firewall` | Windows-gate `IsUserAnAdmin` banner + `block_gamingservices_network` opt-in + cloud-sync warning | XGP panel guard |

**Outcome:** `Conversion Tools {Convert Save Files, GamePass↔Steam, SteamID, Restore Map}` + `Management Tools {Slot Injector, Character Transfer, Fix Host Save}` grids 2×2 per your screenshot, `rounded-[2.5rem]` + description under card (Bento).
