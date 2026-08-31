# 011-plan — Split feature presentation modules

## Objective

Make feature tabs, editors, dialogs, and map/inventory views cohesive and maintainable while keeping their current functionality.

## Tasks

- Split view composition, selection state, data presentation, and command dispatch.
- Reuse common tables, pickers, editors, confirmations, loading states, and empty states.
- Remove direct raw-save access from widgets.
- Make modal refreshes lifecycle-safe and defer updates after dialog execution.
- Preserve all existing controls, filters, imports, exports, and editing workflows.

## Files and areas

`ui/tabs/map_tab.py`, `base_inventory_tab.py`, `inventory_tab.py`, `editor/pal_editor/`, `editor/gps_editor.py`, `editor/worldoption_editor.py`, `ui/dialogs.py`, `ui/create_dialogs.py`, and `ui/wiki_tab.py`.

## Dependencies

`010-plan` and the relevant domain plans.

## Acceptance

Feature modules are smaller and independently testable while the current navigation and action set remains intact.

