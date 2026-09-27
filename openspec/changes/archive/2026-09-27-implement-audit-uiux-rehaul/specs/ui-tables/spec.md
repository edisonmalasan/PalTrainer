## ADDED Requirements

### Requirement: Entity browsers combine list, selection, and structured inspection
Players, Guilds, Bases, Exclusions, references, and other entity collections SHALL use a common browser frame containing search, applicable filters and sort, a labeled visible/total result count, a content-sized selectable table or grid, contextual footer actions, and a structured inspector or responsive drawer. Selection SHALL update details without destroying list state.

#### Scenario: Filter and inspect an entity
- **WHEN** the user filters a populated entity list and selects one result
- **THEN** the labeled count reflects visible and total records, the inspector shows the selected record, and closing the inspector preserves filter, sort, scroll, and selection state

### Requirement: Tables favor readable content over raw structure
Table columns SHALL prioritize human-readable names and meaningful status, size content responsively, avoid truncated headers at supported widths, and disclose full technical identifiers through tooltips and click-to-copy detail. Tables SHALL support visible keyboard focus and predictable single or multi-selection as the workflow requires.

#### Scenario: Table contains long identifiers
- **WHEN** a Players, Guilds, Bases, or JSON table renders values wider than the available column
- **THEN** headers remain understandable, primary content remains readable, values elide rather than overlap, and the full value is available through the shared detail affordance

### Requirement: Bulk actions are contextual and previewable
Bulk action surfaces SHALL remain hidden or inactive until selection exists, show the affected count, separate routine, warning, and destructive operations, and preserve the underlying selection after a canceled preview or confirmation.

#### Scenario: User cancels a bulk preview
- **WHEN** the user previews a bulk mutation and cancels
- **THEN** no data changes and the prior table selection and filters remain intact

## MODIFIED Requirements

### Requirement: Standard table-page frame order
The system SHALL present table-oriented pages with workspace header and context, then search/filter/sort controls with a labeled count, then the table or grid and responsive inspector, followed by status and contextual actions. At narrow supported widths the inspector SHALL become a drawer without clipping table actions.

#### Scenario: Player page follows the frame
- **WHEN** the user opens Players at minimum supported width
- **THEN** search, result count, readable table, selection details, and contextual bulk actions remain reachable without horizontal clipping

#### Scenario: JSON Editor follows the frame
- **WHEN** the user opens JSON Editor with no save loaded
- **THEN** the workspace shows a save prerequisite state while retaining visible search/navigation and import actions that are valid without loaded data

