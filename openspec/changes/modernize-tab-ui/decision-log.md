UI modernization decision log — final state (all 12 tabs reviewed)
Batches approved: 1 Tools, 2 Base Inventory, 3 Player Inventory, 4 Pal Editor, 5 Players/Guilds/Bases, 6 Map, 7 Exclusions, 8 Breeding/Docs. JSON Editor passed review with no changes.
Program-wide outcomes:
- Single tool-discovery system on Tools; masthead metrics; state-dependent drag hint.
- Human-readable labels everywhere (Base N, friendly containers, noun page titles).
- Picker selected-state pattern (shared set_picker_selected) reused across pages.
- All cyan (#7DD3FC family) eliminated from tabs incl. painter code; purple toolbar styles tokenized; Nerd Font references removed from pal editor (2 residual in player_pal_dialog + 1 inventory_tab noted as follow-up).
- Toolbar tier grammar: ghost (utility) / warnActionBtn (bulk mutation) / danger (destructive).
- Empty states: shared EmptyState with per-page hints; no-save vs no-selection vs configured-empty differentiated.
- Verification per batch: compileall, full pytest 481 passed, populated captures with backup Level.sav (read-only fixture).
