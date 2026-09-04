> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 015 — Wiki / Docs (+ Tab Guide Dialog)

## Objective

Restyle the reference reading surfaces: wiki browser (categories → details) and the
TabGuideDialog — calm typographic reading design, static game data, zero save risk.

## Scope

- `ui/tabs/docs_tab.py`, `ui/tabs/docs/wiki_tab.py` (1506 ln), `ui/dialogs/tab_guide_dialog.py`.

## Dependencies

Plans 002–004.

## Design

### Wiki
- Left rail (200px): category buttons (CatBtn) as nav list — selected = accent left
  bar, icon + 11px label; search field above; sort/filter row above results using
  components.
- Details: reading column (max ~720px), display title, section headers, key-value
  rows (label caps + value), stat tables (dense DataTable), rarity/element chips as
  Badges (game contract colors).
- Category pages: card list → dense rows (icon, name, secondary info); lazy `load()`
  flow unchanged.

### TabGuideDialog
- BaseDialog scaffold; TOC grid restyled (3 cols kept); rich-text pages keep HTML
  content (resources/tab_guide/<lang>/*.html untouched) — restyle the *frame* and
  drop the private palette (HEADER_COLOR #4a90e2 etc.) in favor of tokens; HTML
  bodies may keep their own inline colors (content files, out of scope).

## Implementation tasks

1. Tokenize 34 (wiki) + 14 (guide) inline styles; nav rail via components.
2. Keep lazy-loading `_loaded` flags, search/sort/filter logic, refresh() no-op.

## Behavior-preservation requirements

- All game-data reads (characters/items/world/skills/work_suitability JSON), icon
  paths, localization resources unchanged.

## Tests and verification

- compileall + pytest (test_game_data_json, test_resource_integrity); launch: browse
  every category, search, open TabGuideDialog from header, switch language.

## Visual QA requirements

Screenshots: category page, detail page (long text + tables), guide dialog; reading
comfort check (no oversized headings; line length sane).

## Completion criteria

- Docs surfaces tokenized; guide dialog on scaffold.

## Known risks

- Rich-text QLabel pages depend on HTML/CSS subset — frame restyle only; verify no
  clipping at 780×660 minimum.
