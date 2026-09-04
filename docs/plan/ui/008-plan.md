> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 008 — Map Viewer

## Objective

Renovate the map screen chrome (sidebar controls, overlays, toggles, calibration and
zone-drawing flows) while leaving the QGraphicsView rendering pipeline and marker
behavior intact.

## Scope

- `ui/tabs/map_tab.py` (chrome: sidebar, search, toggles, buttons, dialogs wiring),
  `ui/map_view/map_view.py` (overlay chips), `ui/map_view/map_markers.py`,
  `ui/map_items` colors → tokens, `base_hover_overlay.py` + `player_hover_overlay.py`.

## Dependencies

Plans 002–004.

## Design

### Layout
- Left: map canvas (unchanged) with in-view chips (coords/zoom) restyled: raised
  surface, mono font, subtle border.
- Right sidebar (panel): search input; toggles (bases/players/rings/zones) as
  `ToggleCheckBtn`; section headers (Bases / Players / Tools); tree restyle;
  action footer (calibrate, draw zone, import/export/clone).
- Overlays: merge `PlayerHoverOverlay` visuals into one shared hover-card component;
  both classes keep their APIs (map_tab uses both) — dedupe styles, not behavior.

### Painter colors → tokens
- Exclusion zones: danger family (fill 12%, border 40%); previews: accent;
  radius rings: accent 20% with dashed option; effect colors (delete/import/export/
  calibration/swap) map to semantic tokens at same alpha levels. Marker glow colors
  stay config-driven; player glow keeps green family (existing config).

### Zone drawing & calibration
- Same interactions (rect double-click, polygon click/double-close, Esc cancel,
  calibration clicks); only styling changes. Live status shown in a small
  `Badge` in the sidebar footer ("drawing: rect — double-click to finish").

## Implementation tasks

1. Restyle sidebar/trees/toggles/buttons via components; keep all 15 MapGraphicsView
   signals and the refresh() data path (`constants.loaded_level_json` + managers).
2. Replace painter color literals in map_items.py/map_effects.py/map_markers.py with
   imported token constants (allowed by scanner via `constants.` reference).
3. Hover overlays: shared visual, two thin classes preserved.
4. Empty state: no-save → EmptyState overlay above canvas (existing check).

## Behavior-preservation requirements

- All map mutations (delete_base_camp, import/export/clone, zone persistence via
  zone_manager, guild rename) unchanged; animation timers, zoom easing, overlay
  positioning callback unchanged.

## Tests and verification

- compileall + pytest; launch with fixture save: pan/zoom, hover markers, draw rect
  and polygon zones (create + cancel), calibrate, import/export roundtrip on copies.

## Visual QA requirements

Screenshots: full map, zone drawing, hover card, sidebar; dark canvas contrast check.

## Completion criteria

- Map chrome tokenized; painter colors token-referenced; interactions identical.

## Known risks

- QGraphicsItem colors are paint-level; token imports are fine but hex literals in
  painter code must be replaced exactly (alpha steps preserved).
- Overlay positioning math depends on chip sizes — verify at both zoom extremes.
