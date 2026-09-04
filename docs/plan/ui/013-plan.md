> **RESET 2026-09-04: NEEDS REVISION — FROZEN.** The Mandatory Overhaul Reset
> (019-plan.md) rejected plans 004–007 as design decisions and froze 008–018:
> this plan was derived against the old shell (left sidebar + right dock + cyan
> glass) which is now banned (design-context §0). Before executing, rewrite or
> supersede this plan against the 019 divergence matrix (NexusBand shell, warm
> amber/teal palette, Hanken/Inter typography, ribbon page composition).
> Reusable here: domain inventory, functionality preservation lists, test lists.

# Plan 013 — JSON Editor

## Objective

Renovate the read-only raw JSON viewer: mono-typography data surface, toolbar and
search chrome, import guard flow — while keeping read-only-by-default and the strict
preview + confirm import contract.

## Scope

- `ui/tabs/json_editor_tab.py` (426 ln).

## Dependencies

Plans 002–004.

## Design

- Toolbar (panel): Refresh / Export / Import buttons (tool/default/primary kinds,
  Import opens guarded flow); status label as Badge (save loaded / none / stale).
- Search row: search input + prev/next tool buttons + match count badge; existing
  search semantics (tree filter/highlight) unchanged.
- Tree: mono font (Cascadia Mono 12), dense rows, Key/Value/Type columns, lazy
  children placeholders unchanged; hover/selected states; alternating rows subtle.
- Import guard flow (AGENTS invariant): preview panel (first 2000 chars, mono,
  bordered), explicit "Replace in-memory save" danger confirmation — restyled via
  BaseDialog; behavior byte-identical (`GvasFile.load` swap + `save_applied` signal).
- Empty: status "No save loaded" → EmptyState overlay when tree empty.

## Implementation tasks

1. Tokenize 10 inline styles; toolbar via components; tree via builder QSS.
2. Import preview/confirm dialog on scaffold; keep `_confirm_import` logic.

## Behavior-preservation requirements

- Read-only tree (no editing); export via json_tools; import preview + confirmation +
  signal unchanged; lazy loading behavior unchanged.

## Tests and verification

- compileall + pytest; launch: load save → open JSON tab (auto-load on show),
  search+matches, export to temp, import preview + cancel (no mutation), import
  confirm on a copy.

## Visual QA requirements

Screenshot: tree with deep nesting, search active, import preview dialog.
Long-value truncation and ellipsis check (no hidden overflow).

## Completion criteria

- JSON editor tokenized; import contract untouched.

## Known risks

- Very large trees: keep lazy loading and per-node font application cheap.
