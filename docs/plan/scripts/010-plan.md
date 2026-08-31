# 010-plan — Refactor the current PyQt shell

## Objective

Reduce `MainWindow` to composition, navigation, and presentation coordination without redesigning the UI.

## Tasks

- Move feature actions into intent-named application commands.
- Introduce standard no-save, loading, loaded, dirty, saving, and error states.
- Centralize signal routing and refresh notifications.
- Define ownership and shutdown for workers, timers, dialogs, and progress widgets.
- Preserve navigation, menus, shortcuts, lazy loading, save actions, and the results panel.

## Files and areas

`src/palworld_aio/ui/main_window.py`, `ui/chrome.py`, `ui/sidebar.py`, `ui/results.py`, `ui/status_stream.py`, and `src/loading_manager.py`.

## Dependencies

`004-plan`, `006-plan`, `007-plan`, `008-plan`.

## Acceptance

The shell coordinates views and commands but does not perform raw save mutations or direct filesystem work.

