# ui-nav Delta

## Purpose

Defines the top navigation behavior of PalTrainer's shell: the app bar (brand, save chip, context indicator, utilities, window controls, drag zone) and a two-tier nav strip (primary tier of zone destinations plus a contextual secondary tier) with full interaction states and keyboard reachability.

## ADDED Requirements

### Requirement: Distinct nav icon for Base Inventory

The system SHALL render the Base Inventory nav destination with a container/inventory glyph that is visually distinct from the Bases building glyph; the two destinations SHALL NOT share the same house-shaped icon at any size. Any new icon asset SHALL follow the bundled SVG icon set and token-colored icon factory conventions.

#### Scenario: Bases and Base Inventory icons are distinguishable

- **WHEN** the nav strip (or overflow menu) renders the Bases and Base Inventory destinations side by side
- **THEN** each destination shows a distinct icon glyph, and both icons derive their color from the token icon factory

## MODIFIED Requirements

### Requirement: Context indicator summarizes current selection

The system SHALL display a compact current-context indicator (player, guild, or base selection and its save state summary) in the app bar, with full selection detail available on demand (popover or page headers) rather than in a permanently docked tray. The indicator SHALL be hidden when no save is loaded instead of showing a placeholder row.

#### Scenario: Selection updates propagate

- **WHEN** the user selects a player, guild, or base on any page
- **THEN** the context indicator updates to show that selection, and no permanent right-side tray remains visible

#### Scenario: No selection placeholder

- **WHEN** no selection has been made while a save is loaded
- **THEN** the context indicator shows an explicit placeholder rather than stale text

#### Scenario: No save loaded

- **WHEN** no save is loaded
- **THEN** the context indicator is not visible in the app bar, and it reappears when a save loads

### Requirement: Nav strip groups all 12 destinations into four zones

The system SHALL present all 12 page destinations in a top nav strip organized as two tiers: a primary tier of always-visible zone destinations — Tools (Start zone), World, Edit, Reference — and a contextual secondary tier showing only the destinations of the active zone: World (Map Viewer, Bases, Players, Guilds, Exclusions), Edit (Player Inventory, Base Inventory, Pal Editor, JSON Editor), Reference (Breeding, Docs). Activating the Tools primary destination navigates directly to the Tools page; activating World, Edit, or Reference activates that zone and navigates to the most recently visited destination in that zone, falling back to the zone's first destination. All 12 destinations remain reachable, Exclusions stays directly visible as a World destination, and exactly one destination shows the active treatment at any time. The page-ID set and the `nav_changed(str)` signal contract SHALL NOT change; keyboard shortcuts continue to activate any destination directly from any tier.

#### Scenario: Primary tier shows zones only

- **WHEN** the user looks at the nav strip with no save loaded
- **THEN** the primary tier shows exactly the zone destinations (Tools, World, Edit, Reference) and the secondary tier shows the active zone's destinations only

#### Scenario: Switching zones swaps the secondary tier

- **WHEN** the user activates a different zone in the primary tier
- **THEN** the secondary tier is replaced with that zone's destinations and the previously active zone's destinations are no longer shown

#### Scenario: All destinations reachable and distinct

- **WHEN** the user navigates through both tiers (or uses shortcuts and overflow)
- **THEN** all 12 destinations are reachable, each with a distinct label, and Exclusions is directly visible in the World zone's secondary tier

#### Scenario: Zone labels are user-facing

- **WHEN** any destination is shown
- **THEN** its zone (Start / World / Edit / Reference) is identifiable from the primary tier, and the labels localize with the application language

#### Scenario: Navigation contract preserved

- **WHEN** a destination is activated in either tier, by click, overflow menu, or keyboard shortcut
- **THEN** the shell activates the same page ID it did before this change and the nav strip signals `nav_changed` with that page ID

### Requirement: Nav strip interaction states

The system SHALL provide distinct visual treatments for nav destinations in both tiers: active (amber accent per the token palette), hover, pressed, and keyboard focus; zone destinations in the primary tier additionally show an active-zone treatment while any of their children is the active page; and no disabled destination state exists under normal operation (pages render empty states instead of disabling).

#### Scenario: Active destination indicated

- **WHEN** the user activates any destination via click or keyboard shortcut
- **THEN** the canvas shows the corresponding page, that destination alone shows the active treatment in the secondary tier, and its zone shows the active-zone treatment in the primary tier

#### Scenario: Narrow window overflow

- **WHEN** the window width cannot display all tier labels
- **THEN** each tier compacts its labels first and then collapses least-recently-relevant zone groups (secondary tier) or zone destinations (primary tier) into an overflow menu; every destination remains reachable
