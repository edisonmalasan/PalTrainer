> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 010 — Pal Editor

## Objective

Renovate the Pal Editor (tab wrapper + `editor/pal_editor/*` widget system) for
coherence and readability while preserving every editing behavior, validation bound,
and the fragile widget-lifetime handling.

## Scope

- `ui/tabs/pal_editor_tab.py`, `editor/edit_pals.py` (whitelisted by scanner),
  `editor/pal_editor/*`: pal_editor_widget, pal_info_widget/display/handlers,
  card_widgets, party_slot_widget, palbox_slot_widget, pal_ops, bulk/global ops,
  create_dialogs, widgets.py, icons.py, data.py, legacy_frame.py.

## Dependencies

Plans 002–005; SkillPicker restyle in plan 016.

## Design

- Tab header: title + player select button (existing popup) + GPS-mode badge when
  `constants.gps_gvas` active.
- Left: palbox/party slot grids — slot tiles 8px-radius panels, rarity/element
  accents only as borders/labels; drag interactions unchanged.
- Right: pal info panel — section headers per group (stats / passives / skills /
  misc), form rows with field helpers, mono for numbers; passive rank colors = game
  contract. pal_info_widget (103 inline styles) collapses to token classes.
- Cards (card_widgets) and create dialogs: BaseDialog scaffold; icon buttons from
  registry.
- Loading: existing `run_with_loading` + `_selection_generation` staleness guard
  preserved exactly (crash-critical, see fix/* history); no new widget-tree mutation
  during dialog exec.

## Implementation tasks

1. Restyle slot grids first (highest churn risk), compile+launch, then info panel,
   then ops dialogs.
2. Replace inline styles with token classes; keep scanner whitelist for edit_pals.py
   during transition, remove entries only in plan 018 when clean.
3. Keep all pal_ops/bulk_ops function signatures (domain layer untouched).

## Behavior-preservation requirements

- Pal creation/editing, Palbox/party placement, GPS mode, cross-tab selection sync
  (inventory ↔ editor via `parent_window` + `_syncing`), validation bounds,
  stat tooltips (stat_breakdown_tooltip), bulk ops: unchanged.

## Tests and verification

- compileall + pytest (palobject, domain_stats, pal-editor related units); launch:
  load save → editor → select pal → edit level/IVs/passives → save (fixture copy);
  GPS session open; party slot rebuilds (switch players repeatedly).

## Visual QA requirements

Screenshots: palbox grid, info panel, create dialog, bulk-ops dialog; CJK nicknames;
level-999 and negative-stat edge rendering.

## Completion criteria

- Editor tokenized; no new colors; lifetime handling untouched.

## Known risks

- Party-slot use-after-free history (fix/party-slot-build-crash): restyling must not
  reorder layout teardown; verify with rapid player switching.
- edit_pals.py scanner whitelist masks violations — extra manual review here.
