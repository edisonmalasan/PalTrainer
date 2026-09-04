# 023 — Table Strategy: Dense Full-Bleed Tables & Search Recomposition

> **Status: ACTIVE.** Replaces plan 007 (rejected) and the table portions of
> 008–014 for table presentation. Infra from 003 (DataTable, tree styling)
> retained as base.

## 1. Objective

Replace the old search composition (search box above a per-panel-QSS tree,
sidebar-era bulk bar) with a **dense full-bleed table workspace**: ribbon with
inline search field, rule-separated header strip, inline row tools, and a
footer context strip — shared by Search Players/Guilds/Bases and Exclusions.

## 2. Scope

**In scope:** `widgets/search_panel.py` recomposition, main_window search tab
builders, exclusions tab, table QSS (`QTreeWidget/QHeaderView` global + new
objectNames), bulk action presentation (players).

**Out of scope:** context-menu internals, columns/data contracts, export
flows.

## 3. Design requirements

1. **Page ribbon owns search:** the search field lives in the ribbon (expand
   on focus, mono results count at right), not in a stacked box over the tree.
2. **Full-bleed table:** tree/table stretches edge to edge; header strip uses
   `border-bottom` rule, no per-header boxes; rows 28px dense, zebra via
   `alternate-background-color` token.
3. **Inline row tools:** row-level actions via context menu (preserved) with
   tokenized menu; selection highlights via `surface_active`, accent only on
   the selected row text.
4. **Footer context strip:** replaced bulk bar becomes a footer strip under
   the table: selected-count (mono) + bulk actions right-aligned (players
   tab), quiet styling.
5. **Empty state:** centered quiet prompt (`— no entries —` + hint), no blank
   void; **loading/error states** via banner classes from components.

## 4. Behavior preservation

- `SearchPanel` public API: `add_item/clear/refresh_labels/item_selected/
  tree` — unchanged (call sites in main_window keep signatures).
- Sorting, filter semantics (`_on_search`), context menus, per-panel
  signals — unchanged.
- Guild tab vertical splitter retained but restyled (two stacked tables).
- All strings via `t()`; column widths preserved.

## 5. Implementation tasks

1. `search_panel.py`: rebuild layout — filter row (QLineEdit `#searchInput`
   reuse), tree, footer strip (`#tableFooter`); delete per-panel
   `TREE_WIDGET_QSS` application.
2. `main_window.py` search tab builders: wrap panels with ribbons
   (`create_page_ribbon`), remove old margins; players bulk bar → footer
   strip inside panel (API-compatible).
3. `qss_builder.py`: delete `#bulkActionBar/#bulkActionLabel/#bulkHintLabel`
   blocks; add `#tableFooter`, `#searchCount`, refresh global
   `QTreeWidget::item` states; prune legacy-dark.qss `#searchTree` dup.
4. Exclusions tab (014 scope absorbed): three panels → single ribbon +
   segmented control (Players/Guilds/Bases) switching a stacked table, or
   three columns if splitter behavior must persist — choose stacked to break
   the old composition; context menus unchanged.
5. Rebuild theme; smoke.

## 6. Tests

- Smoke: players/guilds/bases/exclusions tabs build; filter hides rows
  (feed rows then set filter text); selection signal emits; footer count
  updates; exclusion switch works.
- Full suite (SearchPanel contract tests exist) + scanner + pyright delta.

## 7. Visual QA

Code-based structural assertions + capture (`Logs/search_v2.png`). Visual
PENDING manual review.

## 8. Risks & rollback

- SearchPanel is used by 6 screens — additive-only changes; keep old
  constructor signature.
- Rollback: single-file revert + qss restore.
