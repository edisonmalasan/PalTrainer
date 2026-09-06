# ui-tables Delta

## Purpose

Defines the single shared presentation frame for all data-table pages (Players, Guilds, Bases, Exclusions, JSON Editor) so search, tables, counts, footers, and inspector pairing behave identically across the application.

## ADDED Requirements

### Requirement: Inspector panel accompanies capped-height tables

The World Data table pages (Bases, Players, Guilds) SHALL pair their card-contained table with a right-hand inspector/detail panel following the Docs list-plus-detail pattern: selecting a row populates the inspector with that row's key details and available follow-up actions (for example "Open in Base Inventory" on Bases), and no selection leaves the inspector in the shared empty-state presentation. The table container SHALL size to its content up to a maximum height (scrolling internally beyond it) rather than forcing a full-viewport fill, so the inspector absorbs the freed canvas instead of the page leaving a large empty band.

#### Scenario: Bases inspector follows selection

- **WHEN** a base row is selected on the Bases page
- **THEN** the inspector shows that base's details (name, guild, identifiers, counts) with follow-up actions, and the identifiers use the monospace tooltip/copy treatment

#### Scenario: Table height is content-driven

- **WHEN** a table page shows fewer rows than fill the viewport
- **THEN** the table container height fits the content (bounded by a maximum), no full-height empty band sits below the table, and the inspector occupies the side region at full canvas height

#### Scenario: Inspector without selection

- **WHEN** no row is selected on Bases, Players, or Guilds with a save loaded
- **THEN** the inspector shows the shared empty-state presentation naming the selection prerequisite

### Requirement: Bulk actions sit adjacent to their table

The Players page bulk action bar (Bulk Item Management, Bulk Pal Management, Bulk Technology Management, Guild Assignments) SHALL render in the footer zone immediately following the table card — visually attached to the table it acts on — with all existing handlers preserved, rather than floating at the page bottom far from the table.

#### Scenario: Players bulk actions adjacency

- **WHEN** the Players page renders with a save loaded
- **THEN** the bulk action bar appears directly below the table card within the table column, remains visible without scrolling at default window size, and triggers the same operations as before

### Requirement: Pagination indicator is labeled

Table pages with pagination SHALL label the page indicator as "Page N of M" (localized), and SHALL hide the indicator entirely when the table has exactly one page.

#### Scenario: Single page hides indicator

- **WHEN** a table's filtered content fits in one page
- **THEN** no bare numeral indicator renders; **WHEN** content spans multiple pages
- **THEN** the indicator reads "Page N of M"

## MODIFIED Requirements

### Requirement: Standard table-page frame order

The system SHALL present every table page in the order: ribbon, then toolbar (search field, filters, result count), then card-contained table, then footer (status text plus page actions such as bulk actions or Refresh/Export/Import). On World Data pages (Bases, Players, Guilds) the footer page actions attach directly to the table column beside the inspector panel; on single-column table pages (Exclusions, JSON Editor) the footer spans the table width.

#### Scenario: Player page follows the frame

- **WHEN** the user opens the Players page
- **THEN** a search toolbar with result count appears above a card-contained table, bulk actions (Bulk Item / Bulk Pal / Bulk Technology / Guild Assignments) appear in the footer zone directly below the table, and everything is visible without horizontal clipping at minimum window size

#### Scenario: JSON Editor follows the frame

- **WHEN** the user opens the JSON Editor with no save loaded
- **THEN** the search row (input plus navigation controls plus match count) sits above the Key/Value/Type table and Refresh/Export/Import actions sit in the footer with a save-status readout

## REMOVED Requirements

(none)
