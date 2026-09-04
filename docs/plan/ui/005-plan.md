> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 005 — Dashboard (Tools Tab) & Save-Loaded State

## Objective

Rebuild the Tools tab as the true "workshop front desk": save status card, live
statistics, and the two tool sections — using shared components, with real empty /
loading / error states.

## Scope

- `src/palworld_aio/ui/tabs/tools_tab.py` (ToolCard, ConversionOptionsDialog chrome,
  stat cards, save card, section grids), `widgets/stats_panel.py` (consumer-side).

## Dependencies

Plans 002, 003, 004.

## Design

### Page header
- `display`-size title + `secondary` subtitle (save file meaning), no oversized hero.

### Save card (single panel, not a rounded poster)
- Left: save-state `StatusDot` + status text (from ShellStateModel semantics).
- Path row: mono path (elided middle, tooltip full), "Change" ghost button
  (Steam/XGP flows preserved), "Open folder" tool button.
- When no save: `EmptyState` with actions **Open Save / Steam / Game Pass**;
  stats section hidden (existing behavior).
- Drag-drop hint only when a drop is possible; DropOverlay handles feedback.

### Statistics strip
- Four compact stat blocks (players/guilds/bases/pals) using StatsPanel semantics:
  label micro-caps, value mono; click deep-links to the matching sidebar entry
  (existing behavior preserved).

### Tool sections
- "Converting" and "Management" as `SectionHeader` + tool rows: replace decorative
  emoji cards with a dense **tool list/table** — icon, name, one-line description,
  action button (or whole row clickable). Group semantics preserved; all 12+ tools
  keep their current dispatch (`importlib` toolsets) and their option dialogs.
- `ToolCard.clicked` signal retained (or mapped) — no workflow changes.
- ConversionOptionsDialog restyled via BaseDialog scaffold.

### States
- Loading: existing `run_with_loading` header spinner + save-state chip; stat blocks
  show placeholder "—" until `load_finished`.
- Error: failed load shows inline ErrorBanner on the save card (message from
  exception) + status chip error; recovery = Change/Open actions.

## Implementation tasks

1. Rebuild layout with components; delete per-widget inline QSS.
2. Wire save-state + error banner from save_manager signals (no polling).
3. Keep `_setup_save_manager_connection`, `_update_stats`, `_reset_save_session`,
   tool dispatch, deep-links unchanged.
4. i18n keys for any new labels.

## Behavior-preservation requirements

- Steam/XGP/drag-drop load flows, stats values, deep-links, tool dispatch:
  byte-for-byte behavior. `ConversionOptionsDialog` result contract unchanged.

## Tests and verification

- Focused pytest (imports/structural), compileall; launch and exercise: no-save state,
  Steam load, XGP flow if available, every tool opens its dialog, stats update.

## Visual QA requirements

Screenshots: no-save, loaded (with stats), error state; ru_RU + zh_CN label check.

## Completion criteria

- Tools tab tokenized, states real, workflows untouched.

## Known risks

- Tool list is long — verify scrolling and row hover at 750px height.
- Stat deep-link relies on sidebar ids (plan 004) — keep ids stable.
