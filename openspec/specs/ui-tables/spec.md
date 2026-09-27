# ui-tables Specification

## Purpose

Defines the single shared presentation frame for all data-table pages (Players, Guilds, Bases, Exclusions, JSON Editor) so search, tables, counts, and footers behave identically across the application.

## Requirements

### Requirement: Standard table-page frame order
The system SHALL present table-oriented pages with workspace header and context, then search/filter/sort controls with a labeled count, then the table or grid and responsive inspector, followed by status and contextual actions. At narrow supported widths the inspector SHALL become a drawer without clipping table actions.

#### Scenario: Player page follows the frame
- **WHEN** the user opens Players at minimum supported width
- **THEN** search, result count, readable table, selection details, and contextual bulk actions remain reachable without horizontal clipping

#### Scenario: JSON Editor follows the frame
- **WHEN** the user opens JSON Editor with no save loaded
- **THEN** the workspace shows a save prerequisite state while retaining visible search/navigation and import actions that are valid without loaded data

### Requirement: Tables share headers, selection, and counts

The system SHALL render table headers with a single header treatment, single-row selection with hover feedback, alternating rows, and a live result count that matches the visible row count after filtering.

#### Scenario: Filtering updates the count

- **WHEN** the user types a filter that matches a subset of rows on any table page
- **THEN** the toolbar count updates to the number of visible rows and clearing the filter restores the full count

### Requirement: Exclusions switching is unambiguous

The system SHALL present the three Exclusions views (players, guilds, bases) as a segmented control with exactly one view selected, each view showing its own search, table, and count.

#### Scenario: Switching exclusion views

- **WHEN** the user selects the guilds segment
- **THEN** only the guild-exclusion table is shown, the guilds segment reads selected, and the other two segments read unselected

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
