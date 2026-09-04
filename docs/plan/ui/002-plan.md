> **RESET 2026-09-04: INFRASTRUCTURE RETAINED — CONTENT SUPERSEDED.** The token
> dict architecture, QSS builder pipeline, theme scanner, and ThemeManager from
> this plan remain the technical foundation. The palette and typography CONTENT
> is replaced by 019-plan.md (warm amber/teal palette, Hanken Grotesk + Inter).
> Do not cite this plan for color/font values.

# Plan 002 — Design System Foundation: Tokens, Typography, Theme Architecture

## Objective

Implement the single source of truth for the new visual language: a themed token
module, the generated-QSS pipeline, the font strategy, and the ThemeManager that
applies it. After this plan, every later plan consumes tokens/components only —
no raw colors anywhere.

## Scope

- New: `src/palworld_aio/ui/chrome/tokens.py` (rewrite as palette dict + resolver),
  `src/palworld_aio/ui/chrome/qss_builder.py` (new), `src/palworld_aio/ui/chrome/fonts.py` (new).
- Update: `chrome/styles.py` (ThemeManager becomes theme-aware), `constants.py`
  (compat layer re-pointed), `resources/ui/themes/darkmode.qss` (regenerated via script).
- Update: `scripts/scrs/check_theme_violations.py` whitelist additions if needed.

## Dependencies

Plan 001 (audit).

## Design decisions implemented here (from 000-design-context.md)

1. **Palette dict.** `PALETTES = {'dark': {token: value}}` in tokens.py. Token groups:
   canvas/surface(1,2,3)/raised, on-surface/secondary/disabled, outline(1,2), accent
   (+bg/border composites at 8/12/20/35%), semantic success/warning/danger/info/special
   (each with bg+border), game-data rarity/element passthrough (imported from game
   domain constants, not redefined). All composites produced by the existing `rgba()`.
2. **Font strategy** (Windows-verified): body = `Segoe UI Variable Text` → `Segoe UI`;
   headings = `Segoe UI Variable Display` → `Segoe UI`; mono = `Cascadia Mono` →
   `Consolas`; icons = bundled `Hack Nerd Font`. `fonts.py` loads every
   `resources/assets/fonts/*.ttf` at startup (replaces header-only loading) and exposes
   `apply_app_fonts(app)` setting the application default font via `QFont.setFamilies`.
3. **Type scale**: display 20/600, title 15/600, section 13/600, body 12/400,
   secondary 11/400, micro 10/400, mono 11/400. Exposed as `TYPE = {'display': …, …}`
   consumed by QSS builder and Python widgets.
4. **Spacing/radius/height tokens**: SPACE {4,8,12,16,24,32}, RADIUS {4,6,8},
   HEIGHT {24,28,32,36}, ROW {28,32} — defined once, used by QSS builder and layout code.
5. **QSS generation.** `qss_builder.build_qss(palette) -> str` produces the full app
   stylesheet: global reset, scrollbars (6px, hover/pressed states), buttons
   (default/primary/danger/ghost/tool variants), inputs (lineedit/spinbox/combo with
   focus ring + error property), tables/trees (dense rows, hover, selected, alternating),
   headers (uppercase micro labels), menus/context menus, tooltips, checkboxes/radios,
   progress bars, splitters, chips/badges, dialogs, tab bars. Dynamic properties used:
   `class` (primary|danger|ghost|tool), `active`, `checked`, `error`, `dirty`, `level`.
6. **ThemeManager**: gains `theme` property, `set_theme(name)` regenerates QSS from the
   palette dict, `apply_global()` uses the builder (file fallback retained for
   standalone builds missing the module). Keeps `apply_to_widget`/`load_styles` API.
7. **Compatibility**: `constants.py` color constants are re-exported from the resolved
   dark palette so ~400 existing imports and `test_constants.py` keep working; when
   values change, `test_constants.py` is updated in the same commit.
8. **Regeneration script**: `scripts/scrs/build_theme.py` writes
   `resources/ui/themes/darkmode.qss` from the builder (splash needs the static file).

## Implementation tasks

1. Rewrite `chrome/tokens.py`: palette dict, `resolve(theme)`, keep `rgba()` helper,
   keep existing names working during transition (deprecation note).
2. Create `chrome/fonts.py` (`load_app_fonts()`, `app_font()`, `mono_font()`).
3. Create `chrome/qss_builder.py` with the complete component QSS (from the skill's
   qss_patterns.md patterns, adapted to PalTrainer tokens + Nerd Font icons).
4. Make `ThemeManager` theme-aware; wire `main.py` to call `fonts.load_app_fonts()`
   + `ThemeManager.set_theme('dark')` (replacing direct file load).
5. Update `bootup.py` splash fallback colors to palette values (no behavior change).
6. Write `scripts/scrs/build_theme.py`; regenerate `darkmode.qss`.
7. Update `test_constants.py` for any changed pinned values; add unit tests:
   tokens resolve without error, builder emits non-empty QSS containing key selectors,
   fonts module falls back gracefully when TTF missing.
8. Register `scripts/scrs/build_theme.py` in `tests/test_registry.py` if the harness
   requires it (follow validate_imports.py precedent).

## Behavior-preservation requirements

- No widget code changes in this plan; all existing QSS strings keep functioning
  (old QSS constants remain importable until plans 003–017 remove their consumers).
- `ThemeManager.apply_to_widget` behavior unchanged for detached console.
- Save/session/workflow code untouched.

## Tests and verification

- `uv run python -m compileall -q src tests`
- `uv run pytest -c tests/pytest.ini tests/unit/palworld_aio_tests/test_constants.py tests/unit/scripts/test_check_theme_violations.py`
- Launch app (`uv run start.py`): verify it boots with generated QSS, splash OK,
  all 12 tabs still render, no console errors.

## Visual QA requirements

Screenshot: shell, tools tab, one search panel, one dialog — confirm the new base
stylesheet applies cleanly to unstyled widgets before any screen migration begins.

## Completion criteria

- QSS for the whole app derives from tokens; `darkmode.qss` is a build artifact.
- No new hard-coded colors introduced anywhere; scanner stays green on new code.
- App launches and all existing tests pass.

## Known risks

- QSS generation bugs can globally restyle; mitigation: builder is unit-tested,
  launch smoke test after each change.
- `test_constants.py` pins values — any token change must update it atomically.
- Old hand-written QSS and generated QSS may fight during transition; mitigation:
  migration plans replace file-by-file, old QSS constants deleted only in plan 018.
