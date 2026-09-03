# Plan 007 — Search Players, Guilds, Bases

## Objective

Unify the three deletion/search screens (and guild-members tree) onto the restyled
SearchPanel with proper empty states, selection states, and bulk-action feedback.

## Scope

- `ui/main_window.py` `_setup_players_tab / _setup_guilds_tab / _setup_bases_tab`
  (and exclusion list panels' visual shell — exclusions get their own plan),
  `widgets/search_panel.py` (restyle, API-stable), `ui/dialogs/guild_assign_dialog.py`.

## Dependencies

Plans 002–004.

## Design

- Page header: title + count badge (`Badge` neutral) + refresh ghost button.
- Toolbar: `make_search_input` (live filter, existing per-keystroke behavior),
  selection-mode toggles as tool buttons, bulk-action buttons in a footer bar
  (existing context menus stay).
- Tree: dense rows (28px), hover, selected = accent left border + tint
  (TREE_WIDGET_QSS regenerated from builder), numeric sort kept via `_SORT_ROLE`.
- Empty state: `EmptyState` ("no players match" vs "load a save") depending on
  `save_session.is_loaded()`.
- Guild members sub-tree: same styling; role context menu restyled
  (ScrollableContextMenu token palette).
- GuildAssignDialog: BaseDialog scaffold, two SearchPanels restyled, role-change
  flow untouched (guild_manager domain calls preserved), status colors → Badge.

## Implementation tasks

1. Restyle the three panels' chrome (they are constructed in main_window — extract
   a small `make_search_page()` helper in main_window or chrome to avoid triplication).
2. SearchPanel: builder QSS, empty-state hook, remove dead signal.
3. GuildAssignDialog scaffold + token palette (drop private `_TREE_STYLE`).

## Behavior-preservation requirements

- All deletion/repair flows (delete_player, delete_guild, delete_base_camp,
  move_player_to_guild, make_member_leader, rebuild_all_guilds) and their
  confirmation dialogs unchanged. ExtendedSelection behavior preserved.
- Search filtering, sort keys, context-menu actions unchanged.

## Tests and verification

- compileall, full pytest; launch: search/filter each list, select multiple,
  run one deletion with confirmation on a test save, guild assign dialog roundtrip.

## Visual QA requirements

Screenshot: populated + filtered + empty; long guild names; dense data at 100%.

## Completion criteria

- Three search screens + guild dialog tokenized; zero per-screen QSS.

## Known risks

- These flows are destructive — visual-only changes; test with fixture save
  (`tests/save_test/Level.sav` copy), never a real save.
