# ui-tables Specification

## Purpose

Defines the single shared presentation frame for all data-table pages (Players, Guilds, Bases, Exclusions, JSON Editor) so search, tables, counts, and footers behave identically across the application.

## Requirements

### Requirement: Standard table-page frame order

The system SHALL present every table page in the order: ribbon, then toolbar (search field, filters, result count), then card-contained table, then footer (status text plus page actions such as bulk actions or Refresh/Export/Import).

#### Scenario: Player page follows the frame

- **WHEN** the user opens the Players page
- **THEN** a search toolbar with result count appears above a card-contained table, and bulk actions (Bulk Item / Bulk Pal / Bulk Technology / Guild Assignments) appear in the footer zone, all visible without horizontal clipping at minimum window size

#### Scenario: JSON Editor follows the frame

- **WHEN** the user opens the JSON Editor with no save loaded
- **THEN** the search row (input plus navigation controls plus match count) sits above the Key/Value/Type table and Refresh/Export/Import actions sit in the footer with a save-status readout

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
