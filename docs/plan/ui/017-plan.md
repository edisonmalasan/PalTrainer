# Plan 017 — Accessibility, States, Resize, High-DPI, Localization Safety

## Objective

Cross-cutting quality pass: keyboard navigation, focus visibility, state completeness,
resize/min-size correctness, high-DPI behavior, long-text/CJK safety, and remaining
worker/dialog-lifecycle guarantees.

## Scope

- Whole `src/palworld_aio/ui` + `widgets` (touch-ups only; no redesigns).
- `main.py` (High-DPI policy if needed).

## Dependencies

Plans 002–016 (all screens migrated).

## Items

1. **Keyboard**: every nav/sidebar item StrongFocus; Esc closes dialogs/popups
   (verify each); Enter confirms dialogs; Tab order sane on forms; mnemonics where
   trivial; tree/table keyboard selection documented.
2. **Focus visibility**: builder QSS focus ring (2px accent border on inputs/buttons
   via `:focus`); verify on dark canvas (no invisible focus).
3. **State completeness audit**: script a checklist per interactive widget class —
   default/hover/pressed/focus/disabled (+selected/checked). Fix gaps via QSS only.
4. **Resize**: min window 1200×750 enforced; splitters (main, map, base-inventory,
   wiki) keep non-collapsible children; dialogs never fixed-frame (sizes via min +
   adjustSize); verify no clipping at min size and at 2560×1440.
5. **High-DPI**: verify at 125%/150% scaling (Qt6 default); set
   `QGuiApplication.setHighDpiScaleFactorRoundingPolicy(PassThrough)` only if
   rounding artifacts appear; icon pixmaps at device ratios for markers/chips.
6. **Localization safety**: run app in zh_CN, ja_JP, ru_RU, de_DE: no clipped labels
   (use elide/word-wrap, never fixed widths on text labels), `t()` everywhere
   (sweep for remaining literals in migrated files).
7. **Workers & lifecycle**: confirm `run_with_loading` guards on all slow paths;
   timers/dialogs owned by live QObjects, stopped at shutdown (header spinner,
   pulse, toast timers); no modal-handler widget-tree mutation (grep + review).

## Behavior-preservation requirements

- No functional changes — quality gates only.

## Tests and verification

- compileall + full pytest + `uv run pyright src`; manual keyboard walkthrough of
  every screen; DPI spot-checks; 4-language sweep.

## Visual QA requirements

Annotated screenshots: focus ring, disabled states, min-size layout, 150% DPI,
zh_CN/ja_JP/ru_RU samples per screen group.

## Completion criteria

- Checklist fully ticked; no P1 issues open.

## Known risks

- Keyboard polish can expose latent focus traps in popups (blocking loops) —
  document, don't restructure control flow.
