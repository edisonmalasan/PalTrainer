# UI/UX Migration Inventory

Baseline captured from `src/palworld_aio` on 2026-09-09. This is a live implementation inventory, not a list inferred from screenshots. Line numbers are discovery anchors and may move; stable class/function/route names are the tracked identities.

## Discovery Commands

```powershell
rg -n "_TAB_SETUP|page_order|_on_nav_changed" src/palworld_aio/ui/main_window.py
rg -n "^class .*\([^)]*(QDialog|FramelessDialog|BaseDialog)[^)]*\)" src/palworld_aio
rg -n "=\s*(QDialog|BaseDialog|FramelessDialog)\(" src/palworld_aio
rg -n "customContextMenuRequested\.connect|setContextMenuPolicy\(" src/palworld_aio
rg -l "setStyleSheet\(|styleSheet\(" src/palworld_aio
rg -n "AppBar|NavStrip|StatusBarStream|QStatusBar|create_page_ribbon|MenuPopup|StatsDrawer" src/palworld_aio/ui
```

## Registered Routes and Pages

All twelve current `_TAB_SETUP` / `_on_nav_changed` identities are preserved at the router boundary. New destinations are introduced by the named owner tasks.

| Current route | Current page | Migration owner |
|---|---|---|
| `tools` (0) | `ToolsTab` | 4.3–4.4 (Tool Center); 4.1–4.2 add separate Overview |
| `base_inventory` (1) | `BaseInventoryTab` | 6.4–6.8 |
| `player_inventory` (2) | `PlayerInventoryTab` | 6.1–6.3, 6.8 |
| `pal_editor` (3) | `PalEditorTab` / `PalEditorWidget` | 7.1–7.6 |
| `players` (4) | MainWindow-built Players page | 5.1 |
| `guilds` (5) | MainWindow-built Guilds page | 5.3–5.4 |
| `bases` (6) | MainWindow-built Bases page | 5.2 |
| `map` (7) | `MapTab` | 5.6 |
| `exclusions` (8) | MainWindow-built Exclusions page | 5.5 |
| `json_editor` (9) | `JsonEditorTab` | 7.7–7.8 |
| `docs` (10) | `DocsTab` / `WikiTab` | 7.9 |
| `breeding` (11) | `BreedingTab` | 7.9 |
| target `overview` | New loaded/no-save home | 4.1–4.2 |
| target `activity` | New operation history | 4.5 |
| target `backups` | New backup browser | 4.6 |
| target `settings` | `SettingsPage` with validated General, Appearance, Save Safety, and Advanced preferences | 8.5 |
| target `about` / `diagnostics` | `AboutPage` and privacy-bounded `DiagnosticsPage` System workspaces | 8.6 |

## Dialog and Dialog-Like Inventory

Every named entry below must use the shared scaffold, drawer, or dedicated workspace. Framework bases are tracked because leaving them legacy would keep all dependents legacy.

| File | Dialog or dialog-like entry | Migration owner |
|---|---|---|
| `editor/dialogs.py` | `ThemedDialog` — shared `BaseDialog` compatibility adapter with centralized control roles, focus, Escape, and accessibility | 2.8, 8.4 |
| `editor/dialogs.py` | `InputDialog`; `DaysInputDialog`; `InactiveFilterDialog`; `LevelInputDialog`; `GameDaysInputDialog` | 8.4 |
| `editor/dialogs.py` | `KillNearestBaseDialog`; `ConfirmDialog`; `RadiusInputDialog`; `RadiusPreviewDialog`; `NudgeInputDialog` | 5.2, 5.6, 8.2, 8.4 |
| `editor/dialogs.py` | `PalDefenderDialog` | 8.2, 8.4 |
| `editor/dialogs.py` | `ScrollableGuildSelectionDialog`; `GuildSelectionDialog`; `ZoneManagementDialog` | 5.4, 5.6, 8.3–8.4 |
| `editor/gps_editor.py` | `GpsEditorDialog`; inline bulk-rename `FramelessDialog` | 8.4 |
| `editor/worldoption_editor.py` | `WorldOptionEditorDialog` — shared `BaseDialog` workspace with one centralized footer | 8.4 |
| `ui/chrome/components.py` | `BaseDialog`; `make_confirm_dialog` runtime instance | 2.8 |
| `ui/chrome/command_palette.py` | `CommandPalette` shared command-navigation dialog | 3.7 |
| `ui/global_search.py` | `GlobalSearchDialog` shared contextual-search dialog | 3.8 |
| `ui/tabs/tools_tab.py` | `ConversionOptionsDialog` | 8.1 |
| `ui/tabs/inventory_tab.py` | `ItemPickerDialog`; `ModifyInventorySlotsDialog`; `QuantityDialog`; `InventoryLoadoutDialog` | 6.8 |
| `ui/tabs/base_inventory_tab.py` | `GuildItemPickerDialog`; `GuildStructurePickerDialog`; `EconomyStatsDialog`; `ContainerSlotModificationDialog`; `ReplaceStructureDialog` | 6.8 |
| `ui/tabs/base_inventory_tab.py` | inline `QDialog` item/structure selection (line 322); container details (line 1353) | 6.8 |
| `ui/dialogs/fix_illegal_pal_dialog.py` | `FixIllegalPalDialog` — shared `BaseDialog` plus affected-count, backup, progress, result, and recovery state | 7.6, 8.2 |
| `ui/dialogs/fix_illegal_player_dialog.py` | `FixIllegalPlayerDialog` — shared `BaseDialog` plus affected-count, backup, progress, result, and recovery state | 8.2, 8.4 |
| `ui/dialogs/guild_assign_dialog.py` | `GuildAssignDialog` | 5.4 |
| `ui/dialogs/player_item_dialog.py` | `PlayerItemActionDialog` | 7.5, 8.4 |
| `ui/dialogs/player_pal_dialog.py` | `PlayerPalActionDialog` | 7.5, 8.4 |
| `ui/dialogs/player_technology_dialog.py` | `PlayerTechnologyActionDialog` | 7.5, 8.4 |
| `ui/dialogs/repair_workflow_dialog.py` | `RepairWorkflowDialog` shared source/review/progress/result scaffold | 8.2 |
| `ui/dialogs/transfer_workflow_dialog.py` | `TransferWorkflowDialog` shared source/target/review/progress/result scaffold | 8.3 |
| `ui/dialogs/tab_guide_dialog.py` | `TabGuideDialog` | 8.4, 8.6 |
| `ui/dialogs/skill_picker.py` | `SkillPicker` — tokenized, accessible transient picker with Escape cancellation | 7.3, 7.6 |
| `ui/tabs/breeding_tab.py` | `_SelectPalDialog` | 7.9 |
| `editor/pal_editor/widgets.py` | `PalEditorDialog` shared `BaseDialog` adapter; `FramelessDialog` is a source-compatible alias to that shared adapter for Global Pal Storage | 2.8, 7.6, 8.4 |
| `editor/pal_editor/create_dialogs.py` | learned-moves `PalEditorDialog`; `BulkSyncPalDialog`; `BulkSyncAllDialog` — shared scaffold | 7.5–7.6 |
| `editor/pal_editor/create_dialogs.py` | `PalCreateDialog` (`BaseDialog`); `BulkSpeciesDialog`; `FoodPickerDialog`; `CloneBulkDialog` (`PalEditorDialog`) | 7.6 |
| `editor/pal_editor/pal_editor_widget.py` | `EditPalsDialog`; inline bulk rename — shared `PalEditorDialog` scaffold | 7.3, 7.6 |
| `editor/pal_editor/pal_editor_bulk_ops.py` | inline bulk rename, bulk heal, and bulk max-buff — shared `PalEditorDialog` scaffold | 7.5–7.6 |
| `ui/main_window.py` | backup picker and Pal naming settings now use `BaseDialog`; no inline `QDialog` remains | 4.6, 8.4–8.5 |
| application and tool modules | Message and value prompts use shared `MessageDialog` / `InputPromptDialog` compatibility adapters; native `QFileDialog` remains only as the platform file/folder picker boundary | 2.8, 5.1–8.4, 9.2–9.4 |

## Popup, Overlay, Drawer, and Menu Inventory

| Entry | Current role | Migration owner |
|---|---|---|
| `MenuPopup`, `ScrollableMenu`, `HoverMenuButton` | Token-driven shared application popup surface with bundled SVG icons and keyboard-accessible categories | 3.7, 4.4, 8.4–8.6 |
| `ScrollableContextMenu`, `_GroupHeader` | Token-driven shared context-menu surface with focusable actions, Escape dismissal, and bundled SVG chevrons | 2.3, 8.4, 9.6 |
| `show_player_select_popup` | Player context selection | 3.2, 6.1, 7.1 |
| `StyledCombo` popup | Custom select control | 2.3 |
| `LoadingPopup`, `LoadingOverlay` | Blocking progress | 2.6, 9.9 |
| `DropOverlay` | Global save drop | 4.2, 9.3 |
| `BaseHoverOverlay`, `PlayerHoverOverlay` | Token-driven accessible entity previews with structured descriptions | 5.1–5.2, 5.6, 8.4 |
| `PassiveEffectOverlay` | Pal visual effect | 2.1, 7.1, 9.7 |
| `StatsDrawer` / `TrayDrawer` and tray scrim | Current app-bar statistics drawer | 3.5–3.6, 4.1, 8.6 |
| `DetachedStatusWindow` | Technical console | 8.6, 9.10 |

## Context-Menu Workflow Inventory

Every action remains available in its context menu when useful, but task 9.6 must ensure important actions also have a visible/keyboard-reachable route.

| Hook | Actions discovered | Migration owner |
|---|---|---|
| `MainWindow._show_player_context_menu` | add/remove exclusion, delete/rename player, viewing cage, timestamp, technologies, level, guild leader/delete/rename/research/level, import base | 5.1, 5.4, 7.5, 8.2–8.4, 9.6 |
| `MainWindow._show_guild_context_menu` | exclusion, delete/rename/level/research, export/import bases | 5.3–5.4, 8.2–8.4, 9.6 |
| `MainWindow._show_guild_member_context_menu` | role, leader, research, exclusion, delete/rename/timestamp/level | 5.3–5.4, 8.2, 9.6 |
| `MainWindow._show_base_context_menu` | exclusion, delete, guild rename/level, export/import/clone, radius, Palbox nudge | 5.2, 5.5–5.6, 8.2–8.4, 9.6 |
| `MainWindow._show_exclusion_context_menu` | remove exclusion | 5.5 |
| `MapTab._on_marker_right_clicked`; `_on_empty_space_right_clicked`; `_on_tree_context_menu`; `_on_zone_right_click` | base/player/zone delete, export, clone, radius, coordinates, nudge, reassign/swap, import, drawing, and zone file operations | 5.6, 8.2–8.4, 8.7, 9.6 |
| `PlayerInventoryTab._on_slot_context_menu`; `_show_item_context_menu`; `_show_empty_slot_context_menu`; `_show_equip_context_menu` | edit quantity, delete/clear, add item, clear corrupted slot | 6.2–6.3, 6.8, 8.7, 9.2, 9.6 |
| `ContainerListWidget._show_context_menu`; `BaseInventoryTab._show_item_context_menu`; `_show_empty_slot_context_menu` | container details/refresh/export/add, edit/remove item, clear container, add item | 6.5–6.8, 8.7, 9.2, 9.6 |
| `build_pal_context_menu` | learned skills, export, clone/bulk clone, sync, rename, heal, buff, delete | 7.3–7.6, 9.2, 9.6 |
| `GuildAssignDialog._show_member_context_menu` | member selection/role interaction | 5.4, 9.6 |
| `SortableTreeWidget._on_context_menu` | generic copy/export-style tree actions | 2.5, 8.4, 9.6 |

## Inline Style Inventory

Counts are occurrences of `setStyleSheet(` or `styleSheet(` at baseline. Transparent/layout-only calls still need review; the owner may retain a call only when it derives from shared tokens and cannot be represented safely by a property/QSS selector.

| File | Baseline occurrences | Migration owner |
|---|---:|---|
| `editor/dialogs.py` | 25 | 2.8, 8.4 |
| `editor/gps_editor.py` | 17 | 8.4 |
| `editor/pal_editor/card_widgets.py` | 28 | 2.7, 7.1 |
| `editor/pal_editor/create_dialogs.py` | 94 | 7.6 |
| `editor/pal_editor/legacy_frame.py` | 7 | 7.1, 10.2 |
| `editor/pal_editor/pal_editor_bulk_ops.py` | 22 | 7.5–7.6 |
| `editor/pal_editor/pal_editor_widget.py` | 12 | 7.1–7.6 |
| `editor/pal_editor/pal_info_display.py` | 23 | 7.3 |
| `editor/pal_editor/pal_info_handlers.py` | 22 | 7.3, 7.6 |
| `editor/pal_editor/pal_info_widget.py` | 98 | 7.3 |
| `editor/pal_editor/palbox_slot_widget.py` | 14 | 2.7, 7.1–7.2 |
| `editor/pal_editor/party_slot_widget.py` | 18 | 2.7, 7.1 |
| `editor/pal_editor/widgets.py` | 8 | 2.7–2.8, 7.6 |
| `editor/worldoption_editor.py` | 1 | 8.4 |
| `ui/chrome/components.py` | 1 | 2.3–2.8 |
| `ui/chrome/styled_combo.py` | 3 | 2.3 |
| `ui/chrome/styles.py` | 5 | 2.1 (central application is allowed) |
| `ui/dialogs/fix_illegal_pal_dialog.py` | 8 | 7.6, 8.2 |
| `ui/dialogs/player_item_dialog.py` | 5 | 7.5, 8.4 |
| `ui/dialogs/player_pal_dialog.py` | 13 | 7.5, 8.4 |
| `ui/dialogs/player_technology_dialog.py` | 3 | 7.5, 8.4 |
| `ui/map_view/map_view.py` | 2 | 5.6 |
| `ui/tabs/base_inventory_tab.py` | 107 | 6.4–6.8 |
| `ui/tabs/breeding_tab.py` | 6 | 7.9 |
| `ui/tabs/docs/wiki_tab.py` | 34 | 7.9 |
| `ui/tabs/inventory_tab.py` | 142 | 6.1–6.8 |
| `ui/tabs/json_editor_tab.py` | 1 | 7.7 |
| `ui/tabs/map_tab.py` | 14 | 5.6 |
| `ui/tabs/pal_editor_tab.py` | 1 | 7.1 |
| `widgets/base_hover_overlay.py` | 1 | 5.2, 5.6 |
| `widgets/empty_state.py` | 4 | 2.6 |
| `widgets/loading_popup.py` | 6 | 2.6 |
| `widgets/menu_popup.py` | 5 | 3.7, 8.4 |
| `widgets/player_hover_overlay.py` | 1 | 5.1, 5.6 |
| `widgets/player_select_popup.py` | 3 | 3.2, 6.1, 7.1 |
| `widgets/scrollable_context_menu.py` | 8 | 2.3, 8.4 |
| `widgets/toggle_check.py` | 2 | 2.3 |
| `widgets/tree_widgets.py` | 1 | 2.5 |

## Legacy Shell and Chrome Inventory

| Legacy live element | Discovery anchor | Migration owner |
|---|---|---|
| `AppBar` | `MainWindow` lines 371/376 | 3.5–3.6 |
| `NavStrip` | `MainWindow` lines 372/385 and `chrome/nav_strip.py` | 3.4–3.6 |
| `create_page_ribbon` | 12 current pages plus helper in `chrome/components.py` | 2.4, 3.5–3.6, page owner tasks |
| `QStatusBar` / `StatusBarStream` | `MainWindow` lines 147/308/359 | 4.5, 8.6, 9.10 |
| `StatsDrawer` / tray scrim | `MainWindow` lines 370/395 and `_set_tray_drawer_visible` | 3.5–3.6, 4.1, 8.6 |
| global `MenuPopup` | `MainWindow._show_menu_popup_v2` and `_setup_menus` | 3.7, 4.4, 8.5–8.6 |
| 1200x750 minimum-size assumptions | main window and shell/layout tests | 2.1, 3.4–3.5, 9.8 |

## Completion Rule

Task 8.7 must revisit every row after migration. Task 10.2 closes this inventory only when each entry is removed, migrated, or retained as a token-driven shared-system implementation with an explicit reason and verification reference. No unowned entry is permitted.

## Task 8.4 Closure

The simple-surface inventory now has **0 unowned entries and 0 legacy-scaffold exceptions**. General editor inputs, filters, confirmations, guild/zone selectors, radius/nudge utilities, and PalDefender inherit the shared `BaseDialog` adapter. World Options, backup selection, Pal naming, Game Pass world selection, tab guides, editor pickers, and all previously migrated domain dialogs use `BaseDialog` directly or a dedicated task-owned workspace. Application-wide message/value prompts use `MessageDialog` and `InputPromptDialog` while preserving Qt-compatible return values. Popup menus, context menus, and entity hover overlays are styled solely by centralized QSS object names and tokens; no inline stylesheet remains in those four popup/overlay modules.

Verification is enforced by `tests/unit/palworld_aio_tests/test_dialogs.py`, which scans the complete `src` tree for native message/input imports, unowned direct `QDialog` subclasses or instances, and inline popup/overlay styles. The only direct `QDialog` subclasses are the shared `BaseDialog` itself and Slot Injector, the task 8.3-owned dedicated complex workspace. `GpsEditorDialog` inherits `FramelessDialog`, which is an alias to the shared `PalEditorDialog`/`BaseDialog` adapter rather than a legacy scaffold. Task 8.7 will still revisit context-menu discoverability and hidden workflow reachability; task 10.2 performs the final repository-wide legacy audit.

## Task 8.5 Closure

The live `settings` route now owns a responsive `SettingsPage` with General, Appearance, Save Safety, and Advanced sections. `UserPreferences` validates every supported enum, boolean, and optional geometry value at the configuration boundary while preserving unrelated extension keys and delegating versioned navigation state to `WorkspaceSettings`. Changes persist immediately, language and loading behavior update through existing application paths, console detachment updates live, and the existing pre-load safety backup plus unsaved-exit guard are controlled by explicit preferences with safe defaults.

`test_user_preferences.py` verifies a complete restart round trip, corrupt-value recovery, and non-mapping recovery. `test_settings_page.py`, `test_save_manager.py`, and `test_main_window.py` cover section reachability, valid emitted values, responsive rendering, backup behavior, and live route registration.

## Task 8.6 Closure

`AboutPage` replaces the legacy inline-rich-text message box with a first-class System workspace for product/game versions, capabilities, credits, project access, update checks, update-available/current/failure states, and direct Diagnostics navigation. `DiagnosticsPage` presents runtime versions, operating system, launch mode, application/configuration/data/backup paths, bounded live technical output, and detachable-console access. Copy and export use a generated support report that never reads the loaded save or its path; console output is included only after an explicit, off-by-default opt-in that warns about local paths.

`system_info.py` owns the bounded metadata contract. Focused tests cover route registration, header About navigation, update-state propagation, path actions, clipboard copy, UTF-8 export, console detachment state, responsive layouts, report size bounds, and marker-based proof that loaded save content/current save paths do not enter the default report.

## Task 8.7 Closure

The post-migration traversal covers every registered destination, all seven Tool Center utilities, the application menu's file/function/map/exclusion/language/configuration groups, direct and nested dialogs, and every context workflow discovered from current source. All 19 route descriptors are registered in the live `WorkspaceShell`; each save-gated route renders the shared prerequisite state before a save is loaded. Hidden application-menu handlers remain reachable through the shell header, retain localized labels and shared message/input/dialog adapters, and delegate long operations to the shared loading/result path. No separate experimental feature flag or unregistered experimental screen was found in the current source.

Every direct `QMenu` now declares the token-driven `appContextMenu` identity and a localized accessible name. Map marker, empty-space, explorer, and zone menus no longer apply `MENU_STYLE`; the guild-role, shell-overflow, application submenu, and legacy-non-live navigation overflow surfaces share the same identity. `SortableTreeWidget`, the generic context-signal tree, no longer carries a hardcoded private table theme and inherits centralized table/header/focus styling through its `dataTree` identity.

Structural evidence lives in `test_dialogs.py`, `test_main_window.py`, `test_routes.py`, and `test_tool_registry.py`: it rejects an unowned dialog, context workflow, direct native menu, or inline generic-tree theme; proves inventory parity; proves all registered/save-gated route behavior; and preserves every tool launcher contract. Task 9.6 remains responsible for the separate keyboard and visible-alternative audit for important context actions, and task 10.2 remains the final repository-wide zero-legacy closure gate.
