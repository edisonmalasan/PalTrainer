# AUDIT §222 acceptance cross-check

Every criterion is listed below with its closest automated or visual evidence. Test filenames refer to `tests/unit/palworld_aio_tests/` unless otherwise stated; render scripts live under `scripts/scrs/`. Generated images and the copied dummy save remain outside the repository. All 97 rows were closed by the final suite, visual matrix, user-reported manual smoke, and recorded deviations.

## Phase 1–7 migration cross-check

The route, dialog, popup, context-menu, and stylesheet entries are individually owned in `migration-inventory.md`. The ranges below cover every completed Phase 1–7 task; the named suites and render artifacts were inspected against those entries. Final release checks are recorded in `visual-baseline.md` and the `AUDIT.md` checkpoint.

| Tasks | Implemented surface and evidence |
|---|---|
| 1.1–1.4 | `AUDIT.md` checkpoint, `migration-inventory.md`, `test_main_window.py` characterization, `render_uiux_baseline.py` no-save/loaded/dialog/1024×700 baseline. |
| 2.1–2.3 | `test_design_tokens.py`, `test_font_registry.py`, `test_icon_factory.py`, `test_components.py`; bundled fonts/icons and shared control roles. |
| 2.4–2.6 | `test_workspace_header.py`, `test_entity_browser.py`, `test_table_inspector.py`, `test_state_views.py`; default/minimum world renders. |
| 2.7–2.9 | `test_content_cards.py`, `test_pal_editor_tab.py`, `test_dialogs.py`, `test_localization.py`; shared slot, Pal, dialog, and localized resources. |
| 3.1–3.3 | `test_routes.py`, `test_workspace_context.py`, `test_router.py`; route/context/history contracts. |
| 3.4–3.6 | `test_sidebar.py`, `test_workspace_shell.py`, `test_main_window.py`; live shell traversal at default/minimum sizes. |
| 3.7–3.10 | `test_command_palette.py`, `test_global_search.py`, `test_workspace_settings.py`, `test_localization.py`; Phase 3 render/checkpoint evidence. |
| 4.1–4.2 | `test_overview_page.py`, `test_main_window.py`; loaded and no-save Overview renders. |
| 4.3–4.4 | `test_tool_registry.py`, `test_tool_center_page.py`, `test_tools_tab.py`; requirement-aware launcher parity. |
| 4.5–4.7 | `test_operation_journal.py`, `test_activity_page.py`, `test_backups_page.py`, `test_backup_catalog.py`; Phase 4 renders and checkpoint. |
| 5.1–5.3 | `test_players_page.py`, `test_bases_page.py`, `test_guilds_page.py`, `test_entity_browser.py`; world workspace matrix. |
| 5.4–5.6 | `test_guild_assign_dialog.py`, `test_exclusions_page.py`, `test_map_workspace.py`, `test_map_zoom_controls.py`; source/review and map renders. |
| 5.7–5.8 | `test_state_views.py`, `test_router.py`, `render_world_workspaces.py`; no-save/selected/minimum-size matrix. |
| 6.1–6.3 | `test_inventory_chip.py`, `test_content_cards.py`, `test_inventory_tab.py`; populated disposable-save Player Inventory render. |
| 6.4–6.6 | `test_base_inventory_chips.py`, `test_content_cards.py`; Base Inventory default/minimum renders. |
| 6.7–6.9 | `test_state_views.py`, `test_dialogs.py`, `test_base_inventory_chips.py`; inventory state/dialog and checkpoint evidence. |
| 7.1–7.4 | `test_pal_editor_tab.py`, `test_pal_editor_box_jump.py`, `test_pal_editor_toolbar.py`; 218-Pal disposable-save renders at 1450×800 and 1024×700. |
| 7.5–7.6 | `test_pal_editor_global_ops.py`, `test_pal_dialog_migration.py`, `test_player_item_dialog.py`, `test_player_pal_dialog.py`; bulk affected-count and dialog contracts. |
| 7.7–7.8 | `test_json_editor_breadcrumb.py`, `test_main_window.py`; structured JSON navigation and validated raw-mode boundary. |
| 7.9–7.10 | `test_wiki_tab.py`, `test_breeding_hint.py`, `test_routes.py`, `test_localization.py`; Reference matrix and checkpoint evidence. |

## Application Shell

| Criterion | Evidence | Status |
|---|---|---|
| Primary navigation has moved away from the current stacked horizontal layout. | test_workspace_shell.py; 1450×800 About render | Verified in release review |
| A persistent sidebar or equivalently strong new navigation structure exists. | test_sidebar.py; test_workspace_shell.py | Verified in release review |
| Save context is visible and understandable. | test_workspace_header.py; test_workspace_context.py | Verified in release review |
| Selected entity context is readable. | test_workspace_context.py; test_workspace_header.py | Verified in release review |
| Native window controls are visually separate from app-level actions. | test_workspace_shell.py; user About screenshot | Verified in release review |
| Unsaved state is explicit. | test_pending_changes.py; test_workspace_header.py | Verified in release review |
| Global search/command navigation is available or architecture allows it. | test_global_search.py; test_command_palette.py | Verified in release review |

## Visual System

| Criterion | Evidence | Status |
|---|---|---|
| Typography scale is standardized. | test_design_tokens.py; test_font_registry.py | Verified in release review |
| Spacing uses centralized tokens. | test_design_tokens.py; final world renders | Verified in release review |
| Buttons have clear hierarchy. | test_components.py; test_player_item_dialog.py | Verified in release review |
| Destructive actions are semantically different. | test_components.py; test_transfer_workflow_dialog.py | Verified in release review |
| Borders are reduced. | final world/Phase 8 renders; visual-baseline.md | Verified in release review |
| Accent usage is intentional. | test_design_tokens.py; final world renders | Verified in release review |
| Components use consistent radii. | test_design_tokens.py; test_components.py | Verified in release review |
| Tooltips use a shared system. | test_components.py; test_dialogs.py | Verified in release review |

## Navigation

| Criterion | Evidence | Status |
|---|---|---|
| World screens follow one navigation model. | test_routes.py; test_router.py; render_world_workspaces.py | Verified in release review |
| Editor screens follow one navigation model. | test_routes.py; test_main_window.py; render_world_workspaces.py | Verified in release review |
| Tool screens follow one navigation model. | test_tool_registry.py; test_tool_center_page.py | Verified in release review |
| Context persists between related pages. | test_workspace_context.py; test_router.py | Verified in release review |
| Back navigation preserves relevant state. | test_router.py; test_workspace_settings.py | Verified in release review |
| Important actions are not exclusively hidden in context menus. | test_entity_browser.py; test_main_window.py; user keyboard smoke | Verified in release review |

## Players

| Criterion | Evidence | Status |
|---|---|---|
| Human-readable player information is prioritized. | test_players_page.py; players_selected render | Verified in release review |
| UUIDs are secondary. | test_players_page.py; test_entity_browser.py | Verified in release review |
| Inspector is structured. | test_table_inspector.py; test_players_page.py | Verified in release review |
| Bulk actions appear contextually. | test_players_page.py; test_pending_changes.py | Verified in release review |
| Player → Inventory is direct. | test_players_page.py; test_main_window.py | Verified in release review |
| Player → Pal Editor is direct. | test_players_page.py; test_main_window.py | Verified in release review |
| Player → Guild is direct. | test_players_page.py; test_guilds_page.py | Verified in release review |

## Bases

| Criterion | Evidence | Status |
|---|---|---|
| Base names are primary. | test_bases_page.py; bases_no_result render | Verified in release review |
| IDs are secondary. | test_bases_page.py; test_entity_browser.py | Verified in release review |
| Base → Inventory is direct. | test_bases_page.py; test_base_inventory_chips.py | Verified in release review |
| Base → Map is direct. | test_bases_page.py; test_map_workspace.py | Verified in release review |
| Base → Guild is direct. | test_bases_page.py; test_guilds_page.py | Verified in release review |

## Guilds

| Criterion | Evidence | Status |
|---|---|---|
| Guild list is simplified. | test_guilds_page.py; test_entity_browser.py | Verified in release review |
| Member list does not permanently consume unnecessary space. | test_guilds_page.py; test_table_inspector.py | Verified in release review |
| Guild assignment workflow is redesigned. | test_guild_assign_dialog.py; test_guilds_page.py | Verified in release review |
| Guild → Players is direct. | test_guilds_page.py; test_players_page.py | Verified in release review |
| Guild → Bases is direct. | test_guilds_page.py; test_bases_page.py | Verified in release review |

## Exclusions

| Criterion | Evidence | Status |
|---|---|---|
| Adding an exclusion is discoverable. | test_exclusions_page.py; exclusions_empty render | Verified in release review |
| Right-click is optional rather than mandatory. | test_exclusions_page.py; test_main_window.py | Verified in release review |
| Player/Guild/Base exclusions use one coherent list. | test_exclusions_page.py; test_entity_browser.py | Verified in release review |
| Empty state is useful. | test_exclusions_page.py; exclusions_empty render | Verified in release review |

## Map

| Criterion | Evidence | Status |
|---|---|---|
| Map occupies the majority of the workspace. | test_map_workspace.py; map_selected render | Verified in release review |
| Browser becomes a structured explorer. | test_map_workspace.py; test_entity_browser.py | Verified in release review |
| Layers are understandable. | test_map_workspace.py; map_selected render | Verified in release review |
| Marker selection opens structured details. | test_map_workspace.py; test_map_zoom_controls.py | Verified in release review |
| Coordinates/zoom are consolidated. | test_map_zoom_controls.py; map_selected render | Verified in release review |
| Map controls have tooltips or labels. | test_map_workspace.py; test_main_window.py | Verified in release review |

## Player Inventory

| Criterion | Evidence | Status |
|---|---|---|
| Player context is obvious. | test_inventory_chip.py; player_inventory_selected render | Verified in release review |
| Inventory categories are visually distinct from global navigation. | test_inventory_chip.py; test_workspace_shell.py | Verified in release review |
| Grid styling is standardized. | test_content_cards.py; player_inventory_selected render | Verified in release review |
| Equipment is structured by category. | test_player_item_dialog.py; player_equipment_selected render | Verified in release review |
| Rarity and selection are visually different. | test_content_cards.py; test_inventory_chip.py | Verified in release review |
| Search/filter/sort are consistent. | test_inventory_chip.py; test_entity_browser.py | Verified in release review |
| Item details are easy to access. | test_player_item_dialog.py; test_content_cards.py | Verified in release review |

## Base Inventory

| Criterion | Evidence | Status |
|---|---|---|
| Guild/Base context is hierarchical. | test_base_inventory_chips.py; base_inventory_context render | Verified in release review |
| Containers use a clear navigator. | test_base_inventory_chips.py; base_inventory_context render | Verified in release review |
| Inventory grid shares Player Inventory primitives. | test_content_cards.py; test_base_inventory_chips.py | Verified in release review |
| Unknown structures have useful placeholders. | test_base_inventory_chips.py; base_inventory_context render | Verified in release review |
| Loading state communicates real work. | test_base_inventory_chips.py; test_state_views.py | Verified in release review |
| Base Pals has a proper empty state. | test_base_inventory_chips.py; base_pals_context render | Verified in release review |

## Pal Editor

| Criterion | Evidence | Status |
|---|---|---|
| Sources, collection, and details are separated clearly. | test_pal_editor_tab.py; populated dummy Pal render | Verified in release review |
| Palbox navigation is easy with hundreds of boxes. | test_pal_editor_box_jump.py; populated dummy Pal render | Verified in release review |
| Pal grid is readable. | test_pal_editor_tab.py; populated dummy Pal render | Verified in release review |
| Inspector is reorganized. | test_pal_editor_tab.py; test_pal_editor_toolbar.py | Verified in release review |
| Bulk actions appear only when relevant. | test_pal_editor_toolbar.py; test_pal_editor_global_ops.py | Verified in release review |
| Destructive actions are clearly distinguished. | test_pal_editor_global_ops.py; test_pal_dialog_migration.py | Verified in release review |

## Bulk Workflows

| Criterion | Evidence | Status |
|---|---|---|
| Bulk Item Management is reorganized. | test_player_item_dialog.py; test_transfer_workflow_dialog.py | Verified in release review |
| Bulk Ability editing uses readable labels. | test_player_item_dialog.py; test_pal_dialog_migration.py | Verified in release review |
| Bulk Pal deletion provides affected count. | test_pal_editor_global_ops.py; test_pal_editor_toolbar.py | Verified in release review |
| Skill removal supports preview where possible. | test_pal_dialog_migration.py; test_pal_editor_global_ops.py | Verified in release review |
| Guild assignment has clear source/target/review structure. | test_guild_assign_dialog.py; test_guilds_page.py | Verified in release review |

## JSON Editor

| Criterion | Evidence | Status |
|---|---|---|
| Tree structure is clearly readable. | test_json_editor_breadcrumb.py; editor_no_save render | Verified in release review |
| Search behavior is explicit. | test_json_editor_breadcrumb.py; test_entity_browser.py | Verified in release review |
| Paths can be identified. | test_json_editor_breadcrumb.py | Verified in release review |
| Import/export actions are clear. | test_json_editor_breadcrumb.py; test_main_window.py | Verified in release review |
| Validation exists for editable JSON. | test_json_editor_breadcrumb.py; test_uiux_baseline_contracts.py | Verified in release review |
| Raw JSON mode is considered or implemented if appropriate. | test_json_editor_breadcrumb.py; AUDIT deviation | Verified in release review |

## Safety

| Criterion | Evidence | Status |
|---|---|---|
| Dangerous operations provide confirmation. | test_pending_changes.py; test_main_window.py | Verified in release review |
| Backup behavior is visible. | test_backup_catalog.py; test_save_manager.py; dummy backup | Verified in release review |
| Unsaved changes are visible. | test_pending_changes.py; test_workspace_header.py | Verified in release review |
| Errors explain whether the save changed. | test_save_manager.py; test_main_window.py | Verified in release review |
| Save success is communicated. | test_main_window.py; test_shell_status_chrome.py | Verified in release review |
| Bulk destructive actions state affected counts. | test_player_item_dialog.py; test_pal_editor_global_ops.py | Verified in release review |

## Accessibility

| Criterion | Evidence | Status |
|---|---|---|
| Keyboard navigation works. | test_main_window.py; user keyboard smoke | Verified in release review |
| Focus states are visible. | test_components.py; user keyboard smoke | Verified in release review |
| Icon controls have accessible names. | test_components.py; test_font_registry.py | Verified in release review |
| Color is not the sole state indicator. | test_design_tokens.py; transfer_failure render | Verified in release review |
| Text contrast is acceptable. | test_design_tokens.py; visual-baseline.md | Verified in release review |
| Dialog focus behavior is correct. | test_components.py; test_styled_combo.py; user keyboard smoke | Verified in release review |

## Missing / Inaccessible Screens

| Criterion | Evidence | Status |
|---|---|---|
| Every existing screen not supplied in the screenshots is migrated. | test_routes.py; migration-inventory.md | Verified in release review |
| Currently broken Tool-tab screens use the new system when accessible. | test_tool_registry.py; test_tools_tab.py | Verified in release review |
| No legacy tabs remain. | test_main_window.py; test_dialogs.py | Verified in release review |
| No legacy dialogs remain. | test_dialogs.py; AUDIT Slot Injector deviation | Verified in release review |
| No legacy table styling remains. | test_dialogs.py generic-control scan; tokenized `baseTree`/`playerTree` rules; regenerated `darkmode.qss` | Verified in task 10.2 |
| No legacy button styling remains. | test_dialogs.py generic-control scan; test_design_tokens.py; selected-Pal default/minimum renders | Verified in task 10.2 |
| No legacy navigation remains. | test_main_window.py; AppBar/NavStrip structural search | Verified in release review |


## Final release evidence

- The user reported the release and keyboard smoke passes on the isolated dummy copy. The 33-state offscreen matrix was inspected; two world layout defects found there were fixed and retested.
- Full pytest: 1128 passed, 20 deselected. Compileall passed. Pyright remained at its prior 481-error, 2-warning baseline; no diagnostic landed on changed source lines.

The first-use Technology grid is a measured performance exception (3.16 seconds on the disposable fixture; 43 ms warm). The optional running-game warning is omitted under the reliability condition recorded in `AUDIT.md`.

Total criteria mapped: 97.
