> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 006 — Results Panel & Statistics Panel

## Objective

Renovate the right-hand "Selection & Stats" dock and the shared StatsPanel into a
clean, mono-valued, copy-friendly results surface.

## Scope

- `src/palworld_aio/ui/chrome/results_widget.py`, `src/palworld_aio/widgets/stats_panel.py`.

## Dependencies

Plans 002, 003.

## Design

- SectionHeader "Selection" + clear button (existing hide/close behavior kept).
- Selection cards (player/guild/base): label-caps key + mono value + copy tool button;
  card = level-1 panel, accent left border only when populated; empty = muted dash.
- Stats grid: 2-col label/value rows, mono values, copy on click (existing),
  section toggle preserved; value labels initial "0" → muted "—" placeholder until
  data arrives (visual only).
- Width: min 320 / max 480 preserved; splitter sizes untouched.

## Implementation tasks

1. Restyle with components; remove inline QSS; keep objectNames consumers may rely on.
2. StatsPanel: token palette, mono values, keep `update_stats/refresh_*` API and
   clipboard behavior (show_warning on failure unchanged).
3. Keep deferred `managers.save_manager` imports (circular-import protection).

## Behavior-preservation requirements

- `set_player/set_guild/set_base/clear_selection/update_stats/refresh_stats_before/
  refresh_stats_after/refresh_labels` signatures and semantics unchanged.
- Clipboard error path unchanged.

## Tests and verification

- compileall + full pytest; launch: select player in search → results dock updates;
  copy buttons write clipboard; hide/show via sidebar toggle and splitter.

## Visual QA requirements

Screenshot: empty selection vs populated; long player names/guild names ellipsis
check; zh_CN labels.

## Completion criteria

- Dock and stats fully tokenized; API intact.

## Known risks

- objectName-based global QSS (valueCard, statsField, …) must keep working until
  all QSS moves into the builder — keep names during migration.
