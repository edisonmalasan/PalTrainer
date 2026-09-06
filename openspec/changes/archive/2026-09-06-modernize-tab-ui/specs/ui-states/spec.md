## MODIFIED Requirements

### Requirement: Tools landing groups actions by purpose

The Tools page SHALL group actions by purpose with translated, user-facing section titles (no untranslated key text, no internal operation codenames): the save-hub masthead (state, path, load actions, metric chips) sits above exactly one grouped tool list system, field-report metrics appear only as masthead metric chips (the standalone metrics strip is removed), and redundant duplicate entry-point rows SHALL be consolidated without removing any tool entry point. The drag-and-drop hint SHALL appear only in the no-save state; in the loaded state the save path is a reveal affordance.

#### Scenario: Tools with no save loaded

- **WHEN** the Tools page is shown with no save loaded
- **THEN** the save-hub masthead ("No Save Loaded" plus load guidance), Steam/GamePass load actions, masthead metric chips, and the grouped tool sections are visible in reading order without overlapping, the drag-and-drop hint is visible, and every visible section title is translated user-facing copy

#### Scenario: Tools with a save loaded

- **WHEN** the Tools page is shown with a save loaded
- **THEN** the masthead shows the loaded state with the save path reveal affordance, the drag-and-drop hint is not visible, and the single grouped tool list remains the only tool discovery surface
